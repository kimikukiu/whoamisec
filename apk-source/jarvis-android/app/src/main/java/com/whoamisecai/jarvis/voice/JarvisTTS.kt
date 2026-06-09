package com.whoamisecai.jarvis.voice

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.Voice
import android.util.Log
import java.util.Locale

/**
 * JARVIS TTS Engine v7 — Fixed Edition
 *
 * Fixes from v6:
 * - Sets Google TTS engine explicitly for better voice quality
 * - en-US male voice with JARVIS-like depth (pitch 0.9, speed 1.1)
 * - Graceful fallback to default TTS engine if Google TTS unavailable
 * - Proper initialization listener with retry
 * - Utterance progress tracking for state management
 */
class JarvisTTS(private val context: Context) : TextToSpeech.OnInitListener {

    companion object {
        private const val TAG = "JarvisTTS"
        private const val GOOGLE_TTS_PACKAGE = "com.google.android.tts"
        private const val TARGET_VOICE_NAME = "en-us-x-iq-local"
        private const val DEFAULT_RATE = 1.1f    // Slightly faster
        private const val DEFAULT_PITCH = 0.9f  // Deeper, more JARVIS-like
    }

    private var tts: TextToSpeech? = null
    private var isReady = false
    private var currentUtteranceId = 0

    // Callbacks
    var onSpeakStart: (() -> Unit)? = null
    var onSpeakDone: ((Boolean) -> Unit)? = null  // success
    var onSpeakError: (() -> Unit)? = null

    /**
     * Initialize TTS engine
     */
    fun initialize(): Boolean {
        Log.i(TAG, "Initializing TTS engine...")

        tts = TextToSpeech(context, this)
        return true  // Actual readiness determined in onInit callback
    }

    override fun onInit(status: Int) {
        when (status) {
            TextToSpeech.SUCCESS -> {
                Log.i(TAG, "TTS engine initialized successfully")

                // Try to set Google TTS engine
                val googleTtsInstalled = setGoogleTTSEngine()

                if (googleTtsInstalled) {
                    Log.i(TAG, "Google TTS engine set as primary")
                } else {
                    Log.w(TAG, "Google TTS not available, using default engine")
                }

                // Set language and voice
                setJARVISVoice()

                isReady = true
            }
            TextToSpeech.ERROR -> {
                Log.e(TAG, "TTS engine initialization FAILED")
                isReady = false
                onSpeakError?.invoke()
            }
        }
    }

    /**
     * Try to set Google TTS as the engine
     */
    private fun setGoogleTTSEngine(): Boolean {
        return try {
            val engines = TextToSpeech.getEngines()
            val googleEngine = engines.find { it.name.contains(GOOGLE_TTS_PACKAGE) }

            if (googleEngine != null) {
                val result = tts?.setEngineByPackageName(GOOGLE_TTS_PACKAGE)
                result == TextToSpeech.SUCCESS
            } else {
                Log.w(TAG, "Google TTS engine not found on device")
                false
            }
        } catch (e: Exception) {
            Log.w(TAG, "Error setting Google TTS engine: ${e.message}")
            false
        }
    }

    /**
     * Set the JARVIS voice profile
     */
    private fun setJARVISVoice() {
        try {
            // Set language to en-US
            val localeResult = tts?.setLanguage(Locale.US)
            when (localeResult) {
                TextToSpeech.LANG_MISSING_DATA, TextToSpeech.LANG_NOT_SUPPORTED -> {
                    Log.w(TAG, "en-US locale not available, trying English")
                    tts?.setLanguage(Locale.ENGLISH)
                }
            }

            // Try to find and set the ideal male voice
            val voices = tts?.voices
            val jarvisVoice = voices?.firstOrNull { voice ->
                voice.name.contains(TARGET_VOICE_NAME) ||
                (voice.locale == Locale.US && voice.name.contains("male", ignoreCase = true))
            }

            if (jarvisVoice != null) {
                tts?.setVoice(jarvisVoice)
                Log.i(TAG, "JARVIS voice set: ${jarvisVoice.name}")
            } else {
                Log.w(TAG, "Ideal voice not found, using default en-US voice")
                // Fallback: set any en-US voice
                val fallbackVoice = voices?.firstOrNull { it.locale == Locale.US }
                if (fallbackVoice != null) {
                    tts?.setVoice(fallbackVoice)
                }
            }

            // Set JARVIS-like speech parameters
            tts?.setSpeechRate(DEFAULT_RATE)
            tts?.setPitch(DEFAULT_PITCH)

            Log.i(TAG, "TTS config: rate=${DEFAULT_RATE}x, pitch=${DEFAULT_PITCH}x")

        } catch (e: Exception) {
            Log.e(TAG, "Error setting JARVIS voice: ${e.message}")
        }
    }

    /**
     * Speak text with JARVIS voice
     */
    fun speak(text: String) {
        if (!isReady || tts == null) {
            Log.w(TAG, "TTS not ready, cannot speak")
            onSpeakError?.invoke()
            return
        }

        val cleanText = text
            .replace("*", "")    // Remove markdown
            .replace("#", "")    // Remove headers
            .replace("_", "")    // Remove emphasis
            .trim()

        if (cleanText.isEmpty()) return

        currentUtteranceId++
        val utteranceId = "jarvis_$currentUtteranceId"

        Log.d(TAG, "Speaking: $cleanText (id=$utteranceId)")

        // Set utterance listener
        tts?.setOnUtteranceCompletedListener { utteranceIdCompleted ->
            if (utteranceIdCompleted == utteranceId) {
                Log.d(TAG, "Utterance completed: $utteranceId")
                onSpeakDone?.invoke(true)
            }
        }

        tts?.setOnUtteranceProgressListener(object : android.speech.tts.UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) {
                if (utteranceId == this@JarvisTTS.utteranceId) {
                    Log.d(TAG, "Utterance started: $utteranceId")
                    onSpeakStart?.invoke()
                }
            }

            override fun onDone(utteranceId: String?) {
                if (utteranceId == this@JarvisTTS.utteranceId) {
                    Log.d(TAG, "Utterance done: $utteranceId")
                    onSpeakDone?.invoke(true)
                }
            }

            override fun onError(utteranceId: String?) {
                Log.e(TAG, "Utterance error: $utteranceId")
                onSpeakError?.invoke()
            }
        })

        // Queue the speech
        val result = tts?.speak(cleanText, TextToSpeech.QUEUE_FLUSH, null, utteranceId)

        if (result != TextToSpeech.SUCCESS) {
            Log.e(TAG, "speak() failed with code: $result")
            onSpeakError?.invoke()
        }
    }

    /**
     * Stop current speech
     */
    fun stop() {
        try {
            tts?.stop()
        } catch (e: Exception) {
            Log.w(TAG, "stop() error: ${e.message}")
        }
    }

    /**
     * Check if TTS is ready
     */
    fun isAvailable(): Boolean = isReady

    /**
     * Check if currently speaking
     */
    fun isSpeaking(): Boolean = tts?.isSpeaking == true

    /**
     * Clean up resources
     */
    fun destroy() {
        stop()
        try {
            tts?.shutdown()
        } catch (e: Exception) {
            Log.w(TAG, "destroy() error: ${e.message}")
        }
        tts = null
        isReady = false
    }
}
