package com.whoamisecai.jarvis.voice;

import android.content.Context;
import android.content.Intent;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.util.Log;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * JARVIS Autonomous Voice Engine
 *
 * Features:
 *  - Continuous speech recognition in Romanian (ro-RO)
 *  - Auto-restart on silence (never stops listening)
 *  - TTS responses in Romanian
 *  - Real-time audio level monitoring for HUD visualization
 *  - VAD (Voice Activity Detection) via audio amplitude
 *
 * JARVIS is ALWAYS listening. When you speak, he hears.
 * When you stop, he processes. When he answers, he speaks.
 * Then he goes back to listening. Autonomous loop.
 */
public class JarvisVoiceEngine {

    private static final String TAG = "JarvisVoice";

    // ── Config ──
    private static final int SAMPLE_RATE = 16000;
    private static final int CHANNEL = AudioFormat.CHANNEL_IN_MONO;
    private static final int ENCODING = AudioFormat.ENCODING_PCM_16BIT;
    private static final int BUFFER_SIZE = 1024;
    private static final float VAD_THRESHOLD = 0.02f;  // Voice activity threshold
    private static final int SILENCE_TIMEOUT_MS = 3000;  // 3s silence = end of speech
    private static final int RESTART_DELAY_MS = 500;    // Quick restart after response

    // ── State ──
    public enum VoiceState { IDLE, LISTENING, PROCESSING, SPEAKING }
    private volatile VoiceState voiceState = VoiceState.IDLE;
    private volatile boolean autonomous = true;  // Always-on mode
    private volatile boolean ttsReady = false;

    // ── Components ──
    private final Context context;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private SpeechRecognizer speechRecognizer;
    private TextToSpeech textToSpeech;
    private AudioRecord audioRecord;
    private Thread audioThread;

    // ── Callbacks ──
    public interface VoiceCallback {
        void onVoiceStateChange(VoiceState state);
        void onAudioLevel(float level);
        void onSpeechRecognized(String text);
        void onSpeechPartial(String text);
        void onError(String error);
    }

    private VoiceCallback callback;

    // ── Silence detection ──
    private Runnable silenceRunnable;
    private float currentAudioLevel = 0f;

    public JarvisVoiceEngine(Context context) {
        this.context = context;
    }

    public void setCallback(VoiceCallback callback) {
        this.callback = callback;
    }

    /**
     * Start JARVIS autonomous voice loop.
     * He will listen forever, process commands, respond, and listen again.
     */
    public void startAutonomous() {
        Log.i(TAG, "JARVIS Autonomous Voice System — ONLINE");
        autonomous = true;
        initTTS();
        initAudioMonitor();
        startListening();
    }

    /**
     * Stop autonomous mode.
     */
    public void stopAutonomous() {
        Log.i(TAG, "JARVIS Autonomous Voice System — STANDBY");
        autonomous = false;
        stopListening();
        stopAudioMonitor();
    }

    /**
     * Say something in Romanian.
     */
    public void speak(String text) {
        if (textToSpeech != null && ttsReady) {
            setState(VoiceState.SPEAKING);
            // Clean text for TTS (remove markdown, URLs, etc.)
            String clean = text.replaceAll("\\[.*?\\]", "")
                    .replaceAll("https?://\\S+", "")
                    .replaceAll("[#*_`~]", "")
                    .trim();
            if (!clean.isEmpty()) {
                Bundle params = new Bundle();
                params.putFloat("pitch", 0.9f);  // Deeper voice
                params.putFloat("speech_rate", 1.0f);
                textToSpeech.speak(clean, TextToSpeech.QUEUE_FLUSH, params, "jarvis_response");
            }
        }
    }

    // ── Speech Recognition ──

    private void initSpeechRecognizer() {
        if (speechRecognizer != null) {
            try { speechRecognizer.destroy(); } catch (Exception e) {}
        }
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context);
        speechRecognizer.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                Log.d(TAG, "Microfon pregatit — JARVIS asculta");
            }

            @Override
            public void onBeginningOfSpeech() {
                Log.d(TAG, "Voce detectata — procesez...");
                resetSilenceTimer();
            }

            @Override
            public void onRmsChanged(float rmsdB) {
                // Update audio level for HUD visualization
                currentAudioLevel = (rmsdB + 10f) / 20f; // Normalize -10..10 -> 0..1
                if (callback != null) callback.onAudioLevel(currentAudioLevel);
            }

            @Override
            public void onBufferReceived(byte[] buffer) {}

            @Override
            public void onEndOfSpeech() {
                Log.d(TAG, "Sfarsit voce — analizez...");
            }

            @Override
            public void onError(int error) {
                String msg = getErrorText(error);
                Log.w(TAG, "Speech error: " + msg);
                if (callback != null) callback.onError(msg);
                // Auto-restart in autonomous mode
                if (autonomous) {
                    handler.postDelayed(() -> {
                        if (autonomous) startListening();
                    }, RESTART_DELAY_MS);
                }
            }

            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(
                        SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String text = matches.get(0);
                    Log.i(TAG, "Recunoscut: " + text);
                    if (callback != null) callback.onSpeechRecognized(text);
                }
                // Continue listening after processing
                if (autonomous) {
                    handler.postDelayed(() -> {
                        if (autonomous && voiceState != VoiceState.SPEAKING) {
                            startListening();
                        }
                    }, 2000);
                }
            }

            @Override
            public void onPartialResults(Bundle partialResults) {
                ArrayList<String> matches = partialResults.getStringArrayList(
                        SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    if (callback != null) callback.onSpeechPartial(matches.get(0));
                    resetSilenceTimer(); // Still speaking
                }
            }

            @Override
            public void onEvent(int eventType, Bundle params) {}
        });
    }

    private void startListening() {
        if (!autonomous) return;
        if (speechRecognizer == null) initSpeechRecognizer();

        setState(VoiceState.LISTENING);
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ro-RO");
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "ro-RO");
        // Also accept English fallback
        intent.putExtra(RecognizerIntent.EXTRA_SUPPORTED_LANGUAGES,
                "ro-RO,en-US,en-GB");
        intent.putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE,
                context.getPackageName());
        intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5);
        // Request longer silence for thinking
        intent.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 5000);
        intent.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 3000);
        intent.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_MINIMUM_LENGTH_MILLIS, 1000);

        try {
            speechRecognizer.startListening(intent);
        } catch (Exception e) {
            Log.e(TAG, "Nu pot porni recunoasterea: " + e.getMessage());
            if (callback != null) callback.onError("Eroare microfon");
            // Retry
            handler.postDelayed(() -> {
                if (autonomous) startListening();
            }, 2000);
        }
    }

    private void stopListening() {
        if (speechRecognizer != null) {
            try { speechRecognizer.stopListening(); } catch (Exception e) {}
            try { speechRecognizer.cancel(); } catch (Exception e) {}
        }
        cancelSilenceTimer();
    }

    // ── TTS ──

    private void initTTS() {
        textToSpeech = new TextToSpeech(context, status -> {
            if (status == TextToSpeech.SUCCESS) {
                int result = textToSpeech.setLanguage(new Locale("ro", "RO"));
                if (result == TextToSpeech.LANG_MISSING_DATA ||
                    result == TextToSpeech.LANG_NOT_SUPPORTED) {
                    // Fallback to English TTS
                    textToSpeech.setLanguage(Locale.US);
                    Log.w(TAG, "Limba romana nu e disponibila — fallback EN");
                } else {
                    Log.i(TAG, "TTS Romana — activ");
                }
                ttsReady = true;
                textToSpeech.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override
                    public void onStart(String utteranceId) {
                        setState(VoiceState.SPEAKING);
                    }

                    @Override
                    public void onDone(String utteranceId) {
                        // Done speaking — back to listening
                        if (autonomous) {
                            handler.postDelayed(() -> startListening(), RESTART_DELAY_MS);
                        } else {
                            setState(VoiceState.IDLE);
                        }
                    }

                    @Override
                    public void onError(String utteranceId) {
                        Log.e(TAG, "TTS Error");
                        if (autonomous) startListening();
                    }
                });
            } else {
                Log.e(TAG, "TTS init esuat");
            }
        });
    }

    // ── Audio Level Monitor ──

    private void initAudioMonitor() {
        try {
            int bufferSize = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL, ENCODING);
            audioRecord = new AudioRecord(MediaRecorder.AudioSource.MIC,
                    SAMPLE_RATE, CHANNEL, ENCODING, Math.max(bufferSize, BUFFER_SIZE));

            if (audioRecord.getState() == AudioRecord.STATE_INITIALIZED) {
                audioThread = new Thread(() -> {
                    short[] buffer = new short[BUFFER_SIZE];
                    audioRecord.startRecording();
                    while (autonomous && !Thread.currentThread().isInterrupted()) {
                        int read = audioRecord.read(buffer, 0, BUFFER_SIZE);
                        if (read > 0) {
                            float sum = 0;
                            for (int i = 0; i < read; i++) {
                                sum += Math.abs(buffer[i]) / 32768f;
                            }
                            float level = sum / read;
                            currentAudioLevel = level;
                            if (callback != null) callback.onAudioLevel(level);
                        }
                    }
                });
                audioThread.setDaemon(true);
                audioThread.start();
            }
        } catch (Exception e) {
            Log.e(TAG, "Audio monitor esuat: " + e.getMessage());
        }
    }

    private void stopAudioMonitor() {
        if (audioRecord != null) {
            try { audioRecord.stop(); } catch (Exception e) {}
            try { audioRecord.release(); } catch (Exception e) {}
            audioRecord = null;
        }
        if (audioThread != null) {
            audioThread.interrupt();
            audioThread = null;
        }
    }

    // ── Silence Timer ──

    private void resetSilenceTimer() {
        cancelSilenceTimer();
        silenceRunnable = () -> {
            // Silence detected too long — restart listening
            Log.d(TAG, "Prea multa liniste — restart");
            if (autonomous) startListening();
        };
        handler.postDelayed(silenceRunnable, SILENCE_TIMEOUT_MS);
    }

    private void cancelSilenceTimer() {
        if (silenceRunnable != null) {
            handler.removeCallbacks(silenceRunnable);
            silenceRunnable = null;
        }
    }

    // ── State ──

    private void setState(VoiceState state) {
        this.voiceState = state;
        if (callback != null) callback.onVoiceStateChange(state);
    }

    public VoiceState getState() { return voiceState; }
    public boolean isAutonomous() { return autonomous; }
    public float getAudioLevel() { return currentAudioLevel; }

    // ── Cleanup ──

    public void destroy() {
        autonomous = false;
        stopListening();
        stopAudioMonitor();
        cancelSilenceTimer();
        if (textToSpeech != null) {
            try { textToSpeech.stop(); } catch (Exception e) {}
            try { textToSpeech.shutdown(); } catch (Exception e) {}
        }
        if (speechRecognizer != null) {
            try { speechRecognizer.destroy(); } catch (Exception e) {}
        }
    }

    private static String getErrorText(int error) {
        switch (error) {
            case SpeechRecognizer.ERROR_AUDIO: return "Eroare audio";
            case SpeechRecognizer.ERROR_CLIENT: return "Eroare client";
            case SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS: return "Fara permisiune microfon";
            case SpeechRecognizer.ERROR_NETWORK: return "Eroare retea";
            case SpeechRecognizer.ERROR_NETWORK_TIMEOUT: return "Timeout retea";
            case SpeechRecognizer.ERROR_NO_MATCH: return "Nu am inteles — repetati";
            case SpeechRecognizer.ERROR_RECOGNIZER_BUSY: return "Recunoastere ocupata";
            case SpeechRecognizer.ERROR_SERVER: return "Eroare server";
            case SpeechRecognizer.ERROR_SPEECH_TIMEOUT: return "Timp expirat — vorbiti";
            default: return "Eroare necunoscuta (" + error + ")";
        }
    }
}
