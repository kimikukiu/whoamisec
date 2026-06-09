package com.whoamisecai.jarvis

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.speech.SpeechRecognizer
import android.util.Log
import android.view.View
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.whoamisecai.jarvis.ai.JarvisAiEngine
import com.whoamisecai.jarvis.hud.JarvisHudView
import com.whoamisecai.jarvis.voice.JarvisTTS
import com.whoamisecai.jarvis.voice.JarvisVoiceEngine
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * JARVIS HUD Activity — Main entry point
 *
 * Orchestrates:
 * 1. Permission handling (bulletproof flow)
 * 2. Voice engine (SpeechRecognizer + AudioRecord fallback)
 * 3. TTS engine (Google TTS, JARVIS voice profile)
 * 4. AI engine (Gemini primary, Cerebras fallback)
 * 5. HUD visualization
 * 6. Wake word detection
 */
class JarvisHudActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "JarvisHudActivity"
        private const val MIC_PERMISSION_REQUEST = 1001
        private const val AUTO_RESTART_DELAY_MS = 800L
    }

    // Engines
    private lateinit var voiceEngine: JarvisVoiceEngine
    private lateinit var ttsEngine: JarvisTTS
    private lateinit var aiEngine: JarvisAiEngine

    // UI elements
    private lateinit var hudView: JarvisHudView
    private lateinit var statusText: TextView
    private lateinit var engineModeText: TextView
    private lateinit var transcriptText: TextView
    private lateinit var responseText: TextView
    private lateinit var debugText: TextView

    // State
    private var isAutonomous = true
    private var lastFinalTranscript: String = ""
    private var isProcessingResponse = false
    private val mainHandler = Handler(Looper.getMainLooper())
    private val scope = CoroutineScope(Dispatchers.Main + Job())
    private var permissionDialogShown = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_jarvis_hud)

        // Initialize UI
        initViews()

        // Initialize engines
        initEngines()

        // Check permission and start
        checkPermissionAndStart()
    }

    override fun onResume() {
        super.onResume()
        // Re-check permission on resume (handles settings changes)
        if (voiceEngine.hasMicPermission() && voiceEngine.currentState == JarvisVoiceEngine.VoiceState.IDLE) {
            startVoiceLoop()
        }
    }

    override fun onPause() {
        super.onPause()
        voiceEngine.stopListening()
    }

    override fun onDestroy() {
        super.onDestroy()
        voiceEngine.destroy()
        ttsEngine.destroy()
        mainHandler.removeCallbacksAndMessages(null)
    }

    // ========================
    // UI Initialization
    // ========================

    private fun initViews() {
        hudView = findViewById(R.id.jarvis_hud_view)
        statusText = findViewById(R.id.jarvis_status)
        engineModeText = findViewById(R.id.jarvis_engine_mode)
        transcriptText = findViewById(R.id.jarvis_transcript)
        responseText = findViewById(R.id.jarvis_response)
        debugText = findViewById(R.id.jarvis_debug)
    }

    // ========================
    // Engine Initialization
    // ========================

    private fun initEngines() {
        // Voice Engine
        voiceEngine = JarvisVoiceEngine(this).apply {
            onStateChange = { state -> onVoiceStateChanged(state) }
            onTranscript = { text, isFinal -> onTranscriptReceived(text, isFinal) }
            onAudioLevel = { level -> onAudioLevelChanged(level) }
            onError = { error -> onVoiceError(error) }
            onWakeWordDetected = { onWakeWordDetected() }
            onRequestSpeechPermission = { requestMicPermission() }
        }

        // TTS Engine
        ttsEngine = JarvisTTS(this).apply {
            onSpeakStart = { onTTSSpeakStart() }
            onSpeakDone = { success -> onTTSSpeakDone(success) }
            onSpeakError = { onTTSSpeakError() }
        }

        // AI Engine
        aiEngine = JarvisAiEngine()
    }

    // ========================
    // Permission Handling
    // ========================

    /**
     * Bulletproof permission flow:
     * 1. Check if granted → start immediately
     * 2. If not → show rationale dialog
     * 3. If "Don't ask again" → open app settings
     * 4. Handle request result
     */
    private fun checkPermissionAndStart() {
        if (hasMicPermission()) {
            Log.i(TAG, "Permission already granted")
            onPermissionGranted()
        } else {
            Log.w(TAG, "Permission not granted, requesting...")
            // Check if we should show rationale (user has denied before but not "don't ask again")
            if (ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.RECORD_AUDIO)) {
                showPermissionRationaleDialog()
            } else {
                // First time or "don't ask again" — just request
                requestMicPermission()
            }
        }
    }

    private fun hasMicPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            this, Manifest.permission.RECORD_AUDIO
        ) == PackageManager.PERMISSION_GRANTED
    }

    private fun requestMicPermission() {
        if (permissionDialogShown) return
        ActivityCompat.requestPermissions(
            this,
            arrayOf(Manifest.permission.RECORD_AUDIO),
            MIC_PERMISSION_REQUEST
        )
    }

    private fun showPermissionRationaleDialog() {
        permissionDialogShown = true
        AlertDialog.Builder(this)
            .setTitle("Microphone Access Required")
            .setMessage("JARVIS requires microphone access for voice recognition. Without this permission, voice commands cannot function.\n\nThe microphone is used exclusively for processing your voice commands to JARVIS.")
            .setPositiveButton("Grant Permission") { _, _ ->
                permissionDialogShown = false
                requestMicPermission()
            }
            .setNegativeButton("Cancel") { _, _ ->
                permissionDialogShown = false
                showSettingsRedirectDialog()
            }
            .setCancelable(false)
            .show()
    }

    private fun showSettingsRedirectDialog() {
        AlertDialog.Builder(this)
            .setTitle("Microphone Access Denied")
            .setMessage("JARVIS cannot operate without microphone access.\n\nPlease enable it in Settings → Apps → JARVIS → Permissions → Microphone.")
            .setPositiveButton("Open Settings") { _, _ ->
                openAppSettings()
            }
            .setNegativeButton("Exit") { _, _ ->
                finish()
            }
            .setCancelable(false)
            .show()
    }

    private fun openAppSettings() {
        val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
            data = Uri.fromParts("package", packageName, null)
        }
        startActivity(intent)
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            MIC_PERMISSION_REQUEST -> {
                val granted = grantResults.isNotEmpty() &&
                        grantResults[0] == PackageManager.PERMISSION_GRANTED

                if (granted) {
                    Log.i(TAG, "Permission granted by user")
                    Toast.makeText(this, "Microphone access granted", Toast.LENGTH_SHORT).show()
                    onPermissionGranted()
                } else {
                    Log.w(TAG, "Permission denied by user")
                    // Check if "don't ask again" was clicked
                    if (!ActivityCompat.shouldShowRequestPermissionRationale(
                            this, Manifest.permission.RECORD_AUDIO
                        )) {
                        // User clicked "don't ask again"
                        showSettingsRedirectDialog()
                    } else {
                        // User just denied, show rationale again
                        showPermissionRationaleDialog()
                    }
                }
            }
        }
    }

    /**
     * Called when microphone permission is confirmed
     */
    private fun onPermissionGranted() {
        // Initialize TTS
        ttsEngine.initialize()

        // Initialize voice engine
        val success = voiceEngine.initialize()

        if (!success) {
            Log.e(TAG, "Voice engine initialization failed even with permission")
            updateStatus("INIT ERROR")
            return
        }

        // Check if SpeechRecognizer is available
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            Toast.makeText(
                this,
                "Using alternative voice engine",
                Toast.LENGTH_LONG
            ).show()
            engineModeText.text = "AUDIO RECORD FALLBACK"
            engineModeText.setTextColor(Color.parseColor("#ffaa00"))
        } else {
            engineModeText.text = "GOOGLE STT"
        }

        // Greeting
        greetUser()

        // Start voice loop after greeting
        mainHandler.postDelayed({
            startVoiceLoop()
        }, 3000)
    }

    // ========================
    // Voice Engine Callbacks
    // ========================

    private fun onVoiceStateChanged(state: JarvisVoiceEngine.VoiceState) {
        runOnUiThread {
            when (state) {
                JarvisVoiceEngine.VoiceState.IDLE -> {
                    updateStatus("STANDBY")
                    hudView.hudState = JarvisHudView.HudState.IDLE
                    hudView.audioLevel = 0f

                    // Auto-restart in autonomous mode (if not processing)
                    if (isAutonomous && !isProcessingResponse) {
                        mainHandler.postDelayed({
                            if (voiceEngine.currentState == JarvisVoiceEngine.VoiceState.IDLE) {
                                startVoiceLoop()
                            }
                        }, AUTO_RESTART_DELAY_MS)
                    }
                }
                JarvisVoiceEngine.VoiceState.INITIALIZING -> {
                    updateStatus("INITIALIZING")
                    hudView.hudState = JarvisHudView.HudState.IDLE
                }
                JarvisVoiceEngine.VoiceState.LISTENING -> {
                    updateStatus("LISTENING")
                    hudView.hudState = JarvisHudView.HudState.LISTENING
                }
                JarvisVoiceEngine.VoiceState.PROCESSING -> {
                    updateStatus("PROCESSING")
                    hudView.hudState = JarvisHudView.HudState.PROCESSING
                }
                JarvisVoiceEngine.VoiceState.SPEAKING -> {
                    updateStatus("SPEAKING")
                    hudView.hudState = JarvisHudView.HudState.SPEAKING
                }
                JarvisVoiceEngine.VoiceState.ERROR -> {
                    updateStatus("ERROR")
                    hudView.hudState = JarvisHudView.HudState.ERROR
                }
                JarvisVoiceEngine.VoiceState.FALLBACK_AUDIO_RECORD -> {
                    updateStatus("FALLBACK MODE")
                    hudView.hudState = JarvisHudView.HudState.FALLBACK
                    engineModeText.text = "AUDIO RECORD"
                    engineModeText.setTextColor(Color.parseColor("#ffaa00"))
                }
            }
        }
    }

    private fun onTranscriptReceived(text: String, isFinal: Boolean) {
        runOnUiThread {
            if (isFinal) {
                lastFinalTranscript = text.trim()
                transcriptText.text = lastFinalTranscript
                transcriptText.alpha = 1f
                Log.i(TAG, "Final transcript: $lastFinalTranscript")

                // Process with AI
                if (lastFinalTranscript.isNotEmpty()) {
                    processWithAI(lastFinalTranscript)
                }
            } else {
                // Partial result — show with dimmed alpha
                transcriptText.text = text
                transcriptText.alpha = 0.6f
            }
        }
    }

    private fun onAudioLevelChanged(level: Float) {
        runOnUiThread {
            hudView.audioLevel = level
        }
    }

    private fun onVoiceError(error: String) {
        runOnUiThread {
            Log.w(TAG, "Voice error: $error")
            responseText.text = error
            responseText.setTextColor(Color.parseColor("#ff4444"))
        }
    }

    // ========================
    // AI Processing
    // ========================

    private fun processWithAI(userMessage: String) {
        if (isProcessingResponse) return
        isProcessingResponse = true

        voiceEngine.stopListening()
        hudView.hudState = JarvisHudView.HudState.PROCESSING
        updateStatus("PROCESSING")

        scope.launch {
            val response = aiEngine.sendMessage(userMessage)

            if (response.success) {
                responseText.text = response.text
                responseText.setTextColor(Color.parseColor("#00ff41"))
                debugText.text = "v7.0-voice-fixed | ${response.engine} (${response.latencyMs}ms)"

                // Speak response
                ttsEngine.speak(response.text)
            } else {
                responseText.text = "Apologies, sir. ${response.error ?: "I seem to be having connectivity issues."}"
                responseText.setTextColor(Color.parseColor("#ff4444"))
                hudView.hudState = JarvisHudView.HudState.ERROR

                // Resume listening after error delay
                mainHandler.postDelayed({
                    isProcessingResponse = false
                    startVoiceLoop()
                }, 2000)
            }
        }
    }

    // ========================
    // TTS Callbacks
    // ========================

    private fun onTTSSpeakStart() {
        runOnUiThread {
            hudView.hudState = JarvisHudView.HudState.SPEAKING
            updateStatus("SPEAKING")
        }
    }

    private fun onTTSSpeakDone(success: Boolean) {
        runOnUiThread {
            isProcessingResponse = false
            hudView.hudState = JarvisHudView.HudState.IDLE
            hudView.audioLevel = 0f

            // Resume listening after speaking
            mainHandler.postDelayed({
                startVoiceLoop()
            }, AUTO_RESTART_DELAY_MS)
        }
    }

    private fun onTTSSpeakError() {
        runOnUiThread {
            isProcessingResponse = false
            Log.w(TAG, "TTS speak error, continuing...")

            mainHandler.postDelayed({
                startVoiceLoop()
            }, AUTO_RESTART_DELAY_MS)
        }
    }

    // ========================
    // Wake Word Detection
    // ========================

    private fun onWakeWordDetected() {
        runOnUiThread {
            Log.i(TAG, "Wake word detected!")
            Toast.makeText(this, "Wake word detected", Toast.LENGTH_SHORT).show()

            // Wake word detected — show acknowledgment and continue listening
            responseText.text = "At your service, sir."
            responseText.setTextColor(Color.parseColor("#00ff41"))
        }
    }

    // ========================
    // Voice Loop Control
    // ========================

    private fun startVoiceLoop() {
        if (!voiceEngine.hasMicPermission()) {
            requestMicPermission()
            return
        }

        if (isProcessingResponse) return

        try {
            voiceEngine.startListening()
        } catch (e: Exception) {
            Log.e(TAG, "startVoiceLoop error: ${e.message}")
            mainHandler.postDelayed({
                startVoiceLoop()
            }, AUTO_RESTART_DELAY_MS * 2)
        }
    }

    // ========================
    // UI Helpers
    // ========================

    private fun updateStatus(text: String) {
        statusText.text = text
    }

    private fun greetUser() {
        val hour = SimpleDateFormat("HH", Locale.US).format(Date()).toInt()
        val timeOfDay = when (hour) {
            in 0..11 -> "morning"
            in 12..16 -> "afternoon"
            else -> "evening"
        }
        val greeting = String.format(
            getString(R.string.jarvis_greeting), timeOfDay
        )
        responseText.text = greeting
        ttsEngine.speak("Good $timeOfDay, sir. All systems operational.")
    }
}
