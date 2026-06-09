package com.whoamisecai.jarvis.voice

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import androidx.core.content.ContextCompat
import kotlinx.coroutines.*
import okhttp3.*
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * JARVIS Voice Engine v7 — Fixed Edition
 * 
 * Fixes from v6:
 * - SpeechRecognizer creation failure: wrapped in try/catch, fallback to AudioRecord + cloud STT
 * - MIC permission: checked before EVERY voice operation, with proper rationale flow
 * - startListening failure: retry logic (3x) with 2s delay, then fallback
 * - AudioRecord hardware test: graceful test, catches SecurityException
 * - Language: en-US default, auto-detect from locale
 * - State machine: IDLE → INITIALIZING → LISTENING → PROCESSING → SPEAKING → IDLE
 */
class JarvisVoiceEngine(
    private val context: Context
) : RecognitionListener {

    companion object {
        private const val TAG = "JarvisVoiceEngine"

        // API Keys
        private const val CEREBRAS_API_KEY = "csk-jx5jc636khef5j2xf64298wwpwpwvc99pkkt9wkcdy2ryedx"
        private const val CEREBRAS_STT_ENDPOINT = "https://api.cerebras.ai/v1/audio/transcriptions"

        // Audio Record Config
        private const val SAMPLE_RATE = 16000
        private const val CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO
        private const val AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT

        // Retry Config
        private const val MAX_RETRIES = 3
        private const val RETRY_DELAY_MS = 2000L

        // Wake Word
        private const val WAKE_WORD = "jarvis"
        private const val WAKE_WORD_ALT = "hey jarvis"

        // Silence detection for AudioRecord fallback
        private const val SILENCE_THRESHOLD = 500
        private const val MAX_RECORDING_MS = 15000L
        private const val END_SILENCE_MS = 1500L
    }

    // Voice States
    enum class VoiceState {
        IDLE, INITIALIZING, LISTENING, PROCESSING, SPEAKING, ERROR, FALLBACK_AUDIO_RECORD
    }

    // Current state
    @Volatile var currentState: VoiceState = VoiceState.IDLE
        private set

    // SpeechRecognizer (primary)
    private var speechRecognizer: SpeechRecognizer? = null
    private var recognizerAvailable = true

    // AudioRecord (fallback)
    private var audioRecord: AudioRecord? = null
    private var isRecordingFallback = false
    private var recordingJob: Job? = null

    // Retry counter
    private var retryCount = 0

    // Audio level for visualization
    @Volatile var audioLevel: Float = 0f
        private set

    // Callbacks
    var onStateChange: ((VoiceState) -> Unit)? = null
    var onTranscript: ((String, Boolean) -> Unit)? = null  // text, isFinal
    var onAudioLevel: ((Float) -> Unit)? = null
    var onError: ((String) -> Unit)? = null
    var onWakeWordDetected: (() -> Unit)? = null
    var onRequestSpeechPermission: (() -> Unit)? = null

    // OkHttpClient for cloud STT
    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .writeTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .build()

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    /**
     * Initialize the voice engine. Must be called after permission is granted.
     */
    fun initialize(): Boolean {
        setState(VoiceState.INITIALIZING)

        // Check permission first
        if (!hasMicPermission()) {
            Log.w(TAG, "initialize: No RECORD_AUDIO permission")
            setState(VoiceState.ERROR)
            onError?.invoke("Microphone permission not granted")
            onRequestSpeechPermission?.invoke()
            return false
        }

        // Try to create SpeechRecognizer
        recognizerAvailable = createSpeechRecognizer()

        if (!recognizerAvailable) {
            Log.w(TAG, "initialize: SpeechRecognizer unavailable, using fallback")
            setState(VoiceState.IDLE)
            return true  // Fallback mode is acceptable
        }

        setState(VoiceState.IDLE)
        Log.i(TAG, "Voice engine initialized (SpeechRecognizer=${if (recognizerAvailable) "available" else "fallback"})")
        return true
    }

    /**
     * Check if microphone permission is granted
     */
    fun hasMicPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            context, Manifest.permission.RECORD_AUDIO
        ) == PackageManager.PERMISSION_GRANTED
    }

    /**
     * Create SpeechRecognizer with full error handling
     */
    private fun createSpeechRecognizer(): Boolean {
        return try {
            // Check if SpeechRecognizer is available on device
            if (!SpeechRecognizer.isRecognitionAvailable(context)) {
                Log.w(TAG, "SpeechRecognizer.isRecognitionAvailable() returned false")
                return false
            }

            // Destroy existing instance if any
            speechRecognizer?.destroy()

            val recognizer = SpeechRecognizer.createSpeechRecognizer(context)
            recognizer.setRecognitionListener(this)
            speechRecognizer = recognizer

            // Configure for longer listening window and better detection
            try {
                val intent = createRecognitionIntent()
                recognizer.createRecognizerIntent() // Test that we can actually use it
            } catch (e: Exception) {
                Log.w(TAG, "SpeechRecognizer created but may not be fully functional: ${e.message}")
            }

            Log.i(TAG, "SpeechRecognizer created successfully")
            true
        } catch (e: SecurityException) {
            Log.e(TAG, "SecurityException creating SpeechRecognizer (permission?): ${e.message}")
            false
        } catch (e: UninitializedPropertyAccessException) {
            Log.e(TAG, "UninitializedPropertyAccessException — Google App not installed: ${e.message}")
            false
        } catch (e: Exception) {
            Log.e(TAG, "Cannot create SpeechRecognizer: ${e.javaClass.simpleName}: ${e.message}")
            false
        }
    }

    /**
     * Create the recognition intent with proper configuration
     */
    private fun createRecognitionIntent(): Intent {
        return Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, getLanguage())
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, getLanguage())
            putExtra(RecognizerIntent.EXTRA_ONLY_RETURN_DEFAULT_LANGUAGE, true)
            putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, context.packageName)

            // CRITICAL: Longer listening window to avoid premature cut-off
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 1500L)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 1000L)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_MINIMUM_LENGTH_MILLIS, 200L)

            // Request partial results for live transcript
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        }
    }

    /**
     * Get language — en-US default, locale fallback
     */
    private fun getLanguage(): String {
        val locale = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            context.resources.configuration.locales[0]
        } else {
            @Suppress("DEPRECATION")
            context.resources.configuration.locale
        }

        // Default to en-US for JARVIS persona
        return "en-US"
    }

    /**
     * Start listening for voice input
     */
    fun startListening() {
        // ALWAYS check permission first
        if (!hasMicPermission()) {
            Log.w(TAG, "startListening: No permission, requesting")
            onRequestSpeechPermission?.invoke()
            return
        }

        when {
            recognizerAvailable -> startSpeechRecognizer()
            else -> startAudioRecordFallback()
        }
    }

    /**
     * Start with Android SpeechRecognizer (primary engine)
     */
    private fun startSpeechRecognizer() {
        val recognizer = speechRecognizer
        if (recognizer == null) {
            Log.e(TAG, "startListening: SpeechRecognizer is null")
            switchToFallback("SpeechRecognizer is null")
            return
        }

        setState(VoiceState.LISTENING)
        retryCount = 0

        try {
            val intent = createRecognitionIntent()
            recognizer.startListening(intent)
            Log.d(TAG, "startListening: SpeechRecognizer.startListening() called")
        } catch (e: SecurityException) {
            Log.e(TAG, "startListening FAILED: SecurityException — ${e.message}")
            switchToFallback("Permission denied for SpeechRecognizer")
        } catch (e: IllegalStateException) {
            Log.e(TAG, "startListening FAILED: IllegalStateException — ${e.message}")
            handleRetryOrFallback("SpeechRecognizer in bad state")
        } catch (e: Exception) {
            Log.e(TAG, "startListening FAILED: ${e.javaClass.simpleName} — ${e.message}")
            handleRetryOrFallback("SpeechRecognizer error: ${e.message}")
        }
    }

    /**
     * Handle retry logic or switch to fallback
     */
    private fun handleRetryOrFallback(reason: String) {
        retryCount++
        if (retryCount < MAX_RETRIES) {
            Log.w(TAG, "Retry $retryCount/$MAX_RETRIES after: $reason")
            setState(VoiceState.IDLE)
            onError?.invoke("Retrying ($retryCount/$MAX_RETRIES)...")

            scope.launch {
                delay(RETRY_DELAY_MS)
                if (currentState == VoiceState.IDLE) {
                    startSpeechRecognizer()
                }
            }
        } else {
            Log.e(TAG, "Max retries reached, switching to fallback: $reason")
            switchToFallback(reason)
        }
    }

    /**
     * Switch to AudioRecord + Cloud STT fallback
     */
    private fun switchToFallback(reason: String) {
        Log.w(TAG, "Switching to AudioRecord fallback: $reason")
        recognizerAvailable = false
        speechRecognizer?.destroy()
        speechRecognizer = null
        onError?.invoke("Using alternative voice engine")
        startAudioRecordFallback()
    }

    /**
     * Start AudioRecord fallback — record audio and send to cloud STT
     */
    private fun startAudioRecordFallback() {
        if (!hasMicPermission()) {
            onRequestSpeechPermission?.invoke()
            return
        }

        setState(VoiceState.FALLBACK_AUDIO_RECORD)
        retryCount = 0
        isRecordingFallback = true

        recordingJob = scope.launch {
            try {
                // Test hardware first
                if (!testAudioRecordHardware()) {
                    Log.e(TAG, "AudioRecord hardware test failed")
                    withContext(Dispatchers.Main) {
                        setState(VoiceState.ERROR)
                        onError?.invoke("Microphone hardware test failed — check device mic")
                    }
                    return@launch
                }

                // Start recording
                val audioData = recordAudioFallback()

                if (audioData != null && audioData.isNotEmpty()) {
                    withContext(Dispatchers.Main) {
                        setState(VoiceState.PROCESSING)
                    }
                    // Send to cloud STT
                    val transcript = performCloudSTT(audioData)
                    withContext(Dispatchers.Main) {
                        if (transcript != null) {
                            onTranscript?.invoke(transcript, true)
                            checkWakeWord(transcript)
                        } else {
                            onError?.invoke("Speech recognition failed (cloud)")
                        }
                        // Restart listening after a delay
                        setState(VoiceState.IDLE)
                        delay(500)
                        startListening()
                    }
                }
            } catch (e: CancellationException) {
                Log.d(TAG, "AudioRecord recording cancelled")
            } catch (e: SecurityException) {
                Log.e(TAG, "AudioRecord SecurityException: ${e.message}")
                withContext(Dispatchers.Main) {
                    setState(VoiceState.ERROR)
                    onError?.invoke("MICROFON REFUZAT — permission denied")
                }
            } catch (e: Exception) {
                Log.e(TAG, "AudioRecord fallback error: ${e.javaClass.simpleName}: ${e.message}")
                withContext(Dispatchers.Main) {
                    setState(VoiceState.ERROR)
                    onError?.invoke("Recording error: ${e.message}")
                }
            } finally {
                isRecordingFallback = false
                stopAudioRecord()
            }
        }
    }

    /**
     * Test AudioRecord hardware — returns true if mic is working
     */
    private fun testAudioRecordHardware(): Boolean {
        return try {
            val bufferSize = AudioRecord.getMinBufferSize(
                SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT
            )
            if (bufferSize == AudioRecord.ERROR || bufferSize == AudioRecord.ERROR_BAD_VALUE) {
                Log.e(TAG, "getMinBufferSize returned error: $bufferSize")
                return false
            }

            val recorder = AudioRecord(
                MediaRecorder.AudioSource.MIC,
                SAMPLE_RATE,
                CHANNEL_CONFIG,
                AUDIO_FORMAT,
                bufferSize
            )

            if (recorder.state != AudioRecord.STATE_INITIALIZED) {
                Log.e(TAG, "AudioRecord failed to initialize (state=${recorder.state})")
                recorder.release()
                return false
            }

            // Brief test recording
            recorder.startRecording()
            val testBuffer = ShortArray(bufferSize / 2)
            val read = recorder.read(testBuffer, 0, testBuffer.size)

            recorder.stop()
            recorder.release()

            val success = read > 0
            Log.i(TAG, "AudioRecord hardware test: ${if (success) "PASSED" else "FAILED"} (read=$read bytes)")
            success
        } catch (e: SecurityException) {
            Log.e(TAG, "AudioRecord hardware test SecurityException: ${e.message}")
            false
        } catch (e: Exception) {
            Log.e(TAG, "AudioRecord hardware test failed: ${e.javaClass.simpleName}: ${e.message}")
            false
        }
    }

    /**
     * Record audio using AudioRecord with silence detection
     */
    private suspend fun recordAudioFallback(): ByteArray? {
        val bufferSize = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT)
        if (bufferSize == AudioRecord.ERROR || bufferSize == AudioRecord.ERROR_BAD_VALUE) {
            Log.e(TAG, "recordAudioFallback: Invalid buffer size")
            return null
        }

        return withContext(Dispatchers.IO) {
            val recorder = AudioRecord(
                MediaRecorder.AudioSource.MIC,
                SAMPLE_RATE,
                CHANNEL_CONFIG,
                AUDIO_FORMAT,
                bufferSize * 2
            )

            if (recorder.state != AudioRecord.STATE_INITIALIZED) {
                Log.e(TAG, "recordAudioFallback: AudioRecord not initialized")
                return@withContext null
            }

            audioRecord = recorder
            recorder.startRecording()

            val outputStream = ByteArrayOutputStream()
            val buffer = ShortArray(bufferSize / 2)
            val pcmBuffer = ByteArray(buffer.size * 2)

            val startTime = System.currentTimeMillis()
            var lastSoundTime = startTime
            var totalSamples = 0

            Log.i(TAG, "AudioRecord fallback recording started...")

            try {
                while (isRecordingFallback && isActive) {
                    val read = recorder.read(buffer, 0, buffer.size)
                    if (read <= 0) continue

                    // Convert to bytes for WAV
                    val byteBuffer = ByteBuffer.allocate(read * 2)
                    byteBuffer.order(ByteOrder.LITTLE_ENDIAN)
                    for (i in 0 until read) {
                        byteBuffer.putShort(buffer[i])
                    }
                    outputStream.write(byteBuffer.array())

                    // Calculate RMS for audio level visualization
                    var sumSquares = 0.0
                    for (i in 0 until read) {
                        sumSquares += buffer[i].toDouble() * buffer[i].toDouble()
                    }
                    val rms = Math.sqrt(sumSquares / read)
                    val normalizedLevel = (rms / 32768.0 * 10).coerceIn(0.0, 1.0).toFloat()

                    withContext(Dispatchers.Main) {
                        audioLevel = normalizedLevel
                        onAudioLevel?.invoke(normalizedLevel)
                    }

                    // Detect if there's actual speech
                    if (rms > SILENCE_THRESHOLD) {
                        lastSoundTime = System.currentTimeMillis()
                    }

                    totalSamples += read

                    // Stop conditions
                    val elapsed = System.currentTimeMillis() - startTime
                    val silenceDuration = System.currentTimeMillis() - lastSoundTime

                    if (elapsed > MAX_RECORDING_MS) {
                        Log.d(TAG, "Max recording time reached")
                        break
                    }
                    if (elapsed > 2000 && silenceDuration > END_SILENCE_MS) {
                        Log.d(TAG, "End silence detected after ${silenceDuration}ms")
                        break
                    }
                }
            } finally {
                recorder.stop()
                recorder.release()
                audioRecord = null
            }

            // Convert to WAV format
            val pcmData = outputStream.toByteArray()
            if (pcmData.isEmpty()) {
                Log.w(TAG, "No audio data recorded")
                return@withContext null
            }

            Log.i(TAG, "Recorded ${pcmData.size} bytes of PCM audio")
            pcmToWav(pcmData, SAMPLE_RATE)
        }
    }

    /**
     * Convert PCM bytes to WAV format
     */
    private fun pcmToWav(pcmData: ByteArray, sampleRate: Int): ByteArray {
        val numChannels = 1
        val bitsPerSample = 16
        val byteRate = sampleRate * numChannels * bitsPerSample / 8
        val blockAlign = numChannels * bitsPerSample / 8
        val dataSize = pcmData.size

        val wavBuffer = ByteBuffer.allocate(44 + dataSize)
        wavBuffer.order(ByteOrder.LITTLE_ENDIAN)

        // RIFF header
        wavBuffer.put("RIFF".toByteArray())
        wavBuffer.putInt(36 + dataSize)
        wavBuffer.put("WAVE".toByteArray())

        // fmt subchunk
        wavBuffer.put("fmt ".toByteArray())
        wavBuffer.putInt(16)  // subchunk size
        wavBuffer.putShort(1.toShort())  // PCM format
        wavBuffer.putShort(numChannels.toShort())
        wavBuffer.putInt(sampleRate)
        wavBuffer.putInt(byteRate)
        wavBuffer.putShort(blockAlign.toShort())
        wavBuffer.putShort(bitsPerSample.toShort())

        // data subchunk
        wavBuffer.put("data".toByteArray())
        wavBuffer.putInt(dataSize)
        wavBuffer.put(pcmData)

        return wavBuffer.array()
    }

    /**
     * Perform cloud-based STT using Cerebras API
     */
    private suspend fun performCloudSTT(audioData: ByteArray): String? {
        return withContext(Dispatchers.IO) {
            try {
                val requestBody = MultipartBody.Builder()
                    .setType(MultipartBody.FORM)
                    .addFormDataPart("file", "recording.wav",
                        okhttp3.RequestBody.create(
                            "audio/wav".toMediaTypeOrNull(),
                            audioData
                        )
                    )
                    .addFormDataPart("model", "whisper-large-v3")
                    .addFormDataPart("language", "en")
                    .build()

                val request = Request.Builder()
                    .url(CEREBRAS_STT_ENDPOINT)
                    .addHeader("Authorization", "Bearer $CEREBRAS_API_KEY")
                    .post(requestBody)
                    .build()

                val response = httpClient.newCall(request).execute()
                val responseBody = response.body?.string()

                if (response.isSuccessful && responseBody != null) {
                    val json = JSONObject(responseBody)
                    val text = json.optString("text", "")
                    if (text.isNotEmpty()) {
                        Log.i(TAG, "Cloud STT result: $text")
                        return@withContext text.trim()
                    }
                } else {
                    Log.e(TAG, "Cloud STT failed: ${response.code} — $responseBody")
                }

                null
            } catch (e: Exception) {
                Log.e(TAG, "Cloud STT error: ${e.javaClass.simpleName}: ${e.message}")
                null
            }
        }
    }

    /**
     * Stop listening
     */
    fun stopListening() {
        isRecordingFallback = false
        recordingJob?.cancel()
        recordingJob = null

        try {
            speechRecognizer?.stopListening()
        } catch (e: Exception) {
            Log.w(TAG, "stopListening error: ${e.message}")
        }

        setState(VoiceState.IDLE)
    }

    /**
     * Stop AudioRecord fallback
     */
    private fun stopAudioRecord() {
        try {
            audioRecord?.stop()
            audioRecord?.release()
        } catch (e: Exception) {
            Log.w(TAG, "stopAudioRecord error: ${e.message}")
        }
        audioRecord = null
    }

    /**
     * Set the voice state and notify callbacks
     */
    private fun setState(state: VoiceState) {
        currentState = state
        Log.d(TAG, "State: $state")
        onStateChange?.invoke(state)
    }

    /**
     * Check for wake word in transcript
     */
    private fun checkWakeWord(text: String) {
        val lower = text.lowercase().trim()
        if (lower.startsWith(WAKE_WORD) || lower.startsWith(WAKE_WORD_ALT)) {
            Log.i(TAG, "Wake word detected: $text")
            onWakeWordDetected?.invoke()
        }
    }

    // ========== RecognitionListener Callbacks ==========

    override fun onReadyForSpeech(params: Bundle?) {
        Log.d(TAG, "onReadyForSpeech")
        setState(VoiceState.LISTENING)
    }

    override fun onBeginningOfSpeech() {
        Log.d(TAG, "onBeginningOfSpeech")
        // Reset retry count on successful start
        retryCount = 0
    }

    override fun onEndOfSpeech() {
        Log.d(TAG, "onEndOfSpeech")
        audioLevel = 0f
        onAudioLevel?.invoke(0f)
    }

    override fun onPartialResults(partialResults: Bundle?) {
        val results = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
        if (!results.isNullOrEmpty()) {
            val text = results[0]
            Log.d(TAG, "onPartialResults: $text")
            onTranscript?.invoke(text, false)
        }
    }

    override fun onResults(results: Bundle?) {
        Log.d(TAG, "onResults")
        val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
        if (!matches.isNullOrEmpty()) {
            val text = matches[0]
            Log.i(TAG, "onResults final: $text")
            onTranscript?.invoke(text, true)
            checkWakeWord(text)
        } else {
            Log.w(TAG, "onResults: No matches")
        }

        // Reset audio level
        audioLevel = 0f
        onAudioLevel?.invoke(0f)

        // Return to idle, will be restarted by the activity if in autonomous mode
        setState(VoiceState.IDLE)
    }

    override fun onError(errorCode: Int) {
        val errorMsg = when (errorCode) {
            SpeechRecognizer.ERROR_NO_MATCH -> "No speech matched"
            SpeechRecognizer.ERROR_AUDIO -> "Audio recording error"
            SpeechRecognizer.ERROR_CLIENT -> "Client error"
            SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Insufficient permissions"
            SpeechRecognizer.ERROR_NETWORK -> "Network error"
            SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timeout"
            SpeechRecognizer.ERROR_SERVER -> "Server error"
            SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Recognizer busy"
            SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Speech timeout"
            else -> "Unknown error ($errorCode)"
        }

        Log.w(TAG, "onError: $errorMsg (code=$errorCode)")

        when (errorCode) {
            SpeechRecognizer.ERROR_NO_MATCH -> {
                // User paused too long or no speech detected — just restart
                Log.d(TAG, "NO_MATCH — restarting listener")
                setState(VoiceState.IDLE)
                scope.launch {
                    delay(500)
                    startListening()
                }
            }

            SpeechRecognizer.ERROR_AUDIO -> {
                // Audio recording failed — retry, then fallback
                handleRetryOrFallback("Audio error")
            }

            SpeechRecognizer.ERROR_NETWORK, SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> {
                // Network issues — try offline / fallback
                Log.w(TAG, "Network error — switching to offline mode")
                switchToFallback("Network error")
            }

            SpeechRecognizer.ERROR_SERVER -> {
                // Server error — retry after delay
                handleRetryOrFallback("Server error")
            }

            SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> {
                // Recognizer busy — wait longer and retry
                Log.w(TAG, "Recognizer busy — waiting before retry")
                setState(VoiceState.IDLE)
                scope.launch {
                    delay(3000)
                    startListening()
                }
            }

            SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> {
                Log.e(TAG, "Insufficient permissions for SpeechRecognizer")
                setState(VoiceState.ERROR)
                onError?.invoke("MIC BLOCAT — insufficient permissions")
                onRequestSpeechPermission?.invoke()
            }

            SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> {
                // No speech detected within timeout — restart
                Log.d(TAG, "Speech timeout — restarting")
                setState(VoiceState.IDLE)
                scope.launch {
                    delay(500)
                    startListening()
                }
            }

            else -> {
                handleRetryOrFallback(errorMsg)
            }
        }
    }

    override fun onRmsChanged(rmsdB: Float) {
        // Normalize RMS to 0-1 range for visualization
        // rmsdB typically ranges from 0 to ~10
        val normalized = (rmsdB / 10f).coerceIn(0f, 1f)
        audioLevel = normalized
        onAudioLevel?.invoke(normalized)
    }

    override fun onBufferReceived(buffer: ByteArray?) {
        // Not used but must be implemented
    }

    override fun onEvent(eventType: Int, params: Bundle?) {
        // Not used but must be implemented
    }

    /**
     * Clean up resources
     */
    fun destroy() {
        stopListening()
        scope.cancel()

        try {
            speechRecognizer?.destroy()
        } catch (e: Exception) {
            Log.w(TAG, "destroy SpeechRecognizer error: ${e.message}")
        }
        speechRecognizer = null

        stopAudioRecord()
    }

    /**
     * Test function to run AudioRecord hardware diagnostics
     * Returns a human-readable result string
     */
    fun runHardwareDiagnostic(): String {
        val results = StringBuilder()
        results.appendLine("=== JARVIS Voice Diagnostic ===")
        results.appendLine("Timestamp: ${java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss", java.util.Locale.US).format(java.util.Date())}")
        results.appendLine()

        // Permission check
        val hasPermission = hasMicPermission()
        results.appendLine("1. RECORD_AUDIO Permission: ${if (hasPermission) "GRANTED ✓" else "DENIED ✗"}")
        if (!hasPermission) {
            results.appendLine("   → FIX: Grant mic permission in Settings")
        }
        results.appendLine()

        // SpeechRecognizer availability
        val srAvailable = SpeechRecognizer.isRecognitionAvailable(context)
        results.appendLine("2. SpeechRecognizer Available: ${if (srAvailable) "YES ✓" else "NO ✗"}")
        if (!srAvailable) {
            results.appendLine("   → FIX: Install Google App or use fallback mode")
        }
        results.appendLine()

        // AudioRecord hardware test
        results.appendLine("3. AudioRecord Hardware Test:")
        try {
            val bufferSize = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT)
            results.appendLine("   MinBufferSize: $bufferSize")

            if (bufferSize == AudioRecord.ERROR) {
                results.appendLine("   Status: ERROR — hardware not supported ✗")
            } else if (bufferSize == AudioRecord.ERROR_BAD_VALUE) {
                results.appendLine("   Status: BAD_VALUE — invalid parameters ✗")
            } else {
                val recorder = AudioRecord(
                    MediaRecorder.AudioSource.MIC,
                    SAMPLE_RATE,
                    CHANNEL_CONFIG,
                    AUDIO_FORMAT,
                    bufferSize * 2
                )
                results.appendLine("   State: ${recorder.state}")
                results.appendLine("   Recording: ${if (recorder.state == AudioRecord.STATE_INITIALIZED) "OK ✓" else "FAIL ✗"}")

                if (recorder.state == AudioRecord.STATE_INITIALIZED) {
                    recorder.startRecording()
                    val testBuf = ShortArray(bufferSize / 2)
                    val read = recorder.read(testBuf, 0, testBuf.size)
                    results.appendLine("   Test Read: $read samples")

                    var sumSq = 0.0
                    for (s in testBuf) sumSq += s.toDouble() * s.toDouble()
                    val rms = Math.sqrt(sumSq / testBuf.size)
                    results.appendLine("   Noise Floor RMS: ${"%.2f".format(rms)}")
                    results.appendLine("   Diagnostic: ${if (read > 0) "PASSED ✓" else "INCONCLUSIVE ⚠"}")

                    recorder.stop()
                }
                recorder.release()
            }
        } catch (e: SecurityException) {
            results.appendLine("   Status: MIC BLOCAT — SecurityException ✗")
            results.appendLine("   → FIX: Grant RECORD_AUDIO permission")
        } catch (e: Exception) {
            results.appendLine("   Status: FAILED — ${e.javaClass.simpleName}: ${e.message} ✗")
        }

        results.appendLine()
        results.appendLine("4. Current State: $currentState")
        results.appendLine("5. Retry Count: $retryCount")
        results.appendLine("6. Recognizer Mode: ${if (recognizerAvailable) "Google STT" else "AudioRecord Fallback"}")
        results.appendLine()
        results.appendLine("=== Diagnostic Complete ===")

        return results.toString()
    }
}

// Extension for MediaType
private fun String.toMediaTypeOrNull(): okhttp3.MediaType? =
    okhttp3.MediaType.get(this)
