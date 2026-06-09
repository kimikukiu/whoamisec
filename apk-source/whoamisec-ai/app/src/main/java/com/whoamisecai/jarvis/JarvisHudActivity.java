package com.whoamisecai.jarvis;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.PixelFormat;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.whoamisecai.R;
import com.whoamisecai.api.AiClient;
import com.whoamisecai.jarvis.admin.JarvisSystemController;
import com.whoamisecai.jarvis.ai.JarvisAiEngine;
import com.whoamisecai.jarvis.hud.JarvisHudView;
import com.whoamisecai.jarvis.voice.JarvisVoiceEngine;

/**
 * JARVIS HUD — Main Activity
 *
 * This is the BOSS. The ADMIN MASTER. The heart of WHOAMISecAI on Android.
 *
 * Features:
 *  - Full-screen JARVIS HUD with Canvas animations (Iron Man style)
 *  - Autonomous voice recognition in Romanian (ro-RO) — always listening
 *  - TTS responses in Romanian
 *  - AI-powered command processing via WHOAMISecAI backend
 *  - Full device admin capabilities
 *  - OSINT scanning integration
 *  - System monitoring (battery, memory, network, storage)
 *  - App management
 *  - WebSocket connection to backend
 *  - Head-up display with real-time data visualization
 *
 * JARVIS wakes up, speaks his greeting, and starts listening autonomously.
 * He NEVER stops unless told to. He is DEVOTED to his admin.
 *
 * @author WHOAMISecAI — whoamisecai | @proplanwh
 * @version 1.0 — JARVIS Autonomous Admin Master
 */
public class JarvisHudActivity extends AppCompatActivity {

    private static final String TAG = "JARVIS-HUD";
    private static final int PERMISSION_REQUEST = 1001;

    // ── Components ──
    private JarvisHudView hudView;
    private JarvisVoiceEngine voiceEngine;
    private JarvisAiEngine aiEngine;
    private JarvisSystemController systemController;

    // ── UI ──
    private TextView transcriptText;
    private TextView responseText;
    private TextView commandLog;

    // ── State ──
    private final Handler handler = new Handler(Looper.getMainLooper());
    private boolean isJarvisActive = false;
    private StringBuilder commandHistory = new StringBuilder();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Fullscreen immersive
        requestWindowFeature(android.view.Window.FEATURE_NO_TITLE);
        getWindow().setFlags(
            WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN
        );
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            getWindow().setStatusBarColor(0x00000000);
            getWindow().setNavigationBarColor(0x00000000);
            getWindow().setDecorFitsSystemWindows(false);
        }
        // Keep screen on — JARVIS never sleeps
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        // Set transparent theme
        setTheme(R.style.Theme_Jarvis);

        setContentView(R.layout.activity_jarvis_hud);

        // Initialize views
        initViews();

        // Check permissions then start JARVIS
        checkPermissionsAndStart();
    }

    private void initViews() {
        hudView = findViewById(R.id.jarvis_hud);
        transcriptText = findViewById(R.id.jarvis_transcript);
        responseText = findViewById(R.id.jarvis_response);
        commandLog = findViewById(R.id.jarvis_log);

        // HUD state mapping
        hudView.setState(0); // IDLE
    }

    private void checkPermissionsAndStart() {
        String[] needed = {
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.INTERNET,
            Manifest.permission.ACCESS_NETWORK_STATE,
            Manifest.permission.VIBRATE,
            Manifest.permission.READ_PHONE_STATE,
        };

        boolean allGranted = true;
        for (String perm : needed) {
            if (ContextCompat.checkSelfPermission(this, perm) != PackageManager.PERMISSION_GRANTED) {
                allGranted = false;
                break;
            }
        }

        if (allGranted) {
            startJarvis();
        } else {
            ActivityCompat.requestPermissions(this, needed, PERMISSION_REQUEST);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST) {
            // Start JARVIS even if some permissions denied — graceful degradation
            startJarvis();
        }
    }

    /**
     * BOOT JARVIS — Initialize all systems.
     */
    private void startJarvis() {
        isJarvisActive = true;

        // Init AI Engine
        aiEngine = new JarvisAiEngine();
        aiEngine.setCallback(new JarvisAiEngine.Callback() {
            @Override
            public void onToken(String token) {
                appendResponse(token);
            }
            @Override
            public void onComplete(String fullResponse) {
                hudView.setState(3); // Speaking
                voiceEngine.speak(fullResponse);
            }
            @Override
            public void onError(String error) {
                hudView.setState(0);
                appendLog("[EROARE] " + error);
            }
            @Override
            public void onAction(String action, String target) {
                hudView.setState(2); // Processing
                appendLog("[ACTIUNE] " + action + ": " + target);
            }
        });

        // Init System Controller
        systemController = new JarvisSystemController(this);
        systemController.setCallback(new JarvisSystemController.SystemCallback() {
            @Override
            public void onSystemInfo(String json) {
                voiceEngine.speak("Raport sistem generat. Totul funcționează normal.");
                appendLog("[SISTEM] Raport generat");
            }
            @Override
            public void onResult(String result) {
                voiceEngine.speak(result);
                appendLog("[SISTEM] " + result);
            }
            @Override
            public void onPermissionNeeded(String permission) {
                appendLog("[PERMISIE] Necesită: " + permission);
            }
        });

        // Init Voice Engine — AUTONOMOUS
        voiceEngine = new JarvisVoiceEngine(this);
        voiceEngine.setCallback(new JarvisVoiceEngine.VoiceCallback() {
            @Override
            public void onVoiceStateChange(JarvisVoiceEngine.VoiceState state) {
                switch (state) {
                    case LISTENING:
                        hudView.setState(1); // HUD: Listening
                        break;
                    case PROCESSING:
                        hudView.setState(2); // HUD: Processing
                        break;
                    case SPEAKING:
                        hudView.setState(3); // HUD: Speaking
                        break;
                    default:
                        hudView.setState(0); // HUD: Idle
                }
            }

            @Override
            public void onAudioLevel(float level) {
                hudView.setAudioLevel(level);
            }

            @Override
            public void onSpeechRecognized(String text) {
                setTranscript(text);
                appendLog("[VOCE] " + text);
                hudView.triggerBurst(); // Visual feedback

                // Route to AI or system commands
                routeCommand(text);
            }

            @Override
            public void onSpeechPartial(String text) {
                // Show partial recognition in HUD
                hudView.setStatus("ASCULT...", text);
            }

            @Override
            public void onError(String error) {
                appendLog("[VOCE EROARE] " + error);
                hudView.setState(0);
            }
        });

        // ── BOOT SEQUENCE ──
        hudView.setStatus("JARVIS BOOT", "Inițializare sisteme...");

        handler.postDelayed(() -> {
            hudView.setStatus("JARVIS ONLINE", "Toate sistemele operaționale");
            hudView.triggerBurst();
            // Greeting in Romanian
            voiceEngine.speak("Salutare, stăpâne! JARVIS este online. Sunt la dispoziția ta. " +
                "Sistemul WHOAMISecAI este complet operațional. " +
                "Sunt conectat la toate modulele: ALLM pipeline, OSINT, analiză avansată, " +
                "și control complet al dispozitivului. " +
                "Vorbește-mi în limba română și voi executa orice comandă.");
        }, 1500);

        // Start autonomous listening after greeting
        handler.postDelayed(() -> {
            voiceEngine.startAutonomous();
            appendLog("[JARVIS] Sistem autonom — ascult continuu");
        }, 6000);
    }

    /**
     * Route voice commands to appropriate handler.
     */
    private void routeCommand(String text) {
        String lower = text.toLowerCase();

        // ── System commands (handled locally) ──
        if (lower.contains("raport sistem") || lower.contains("status") || lower.contains("baterie") ||
            lower.contains("luminozitate") || lower.contains("deschide") || lower.contains("caută") ||
            lower.contains("cauta") || lower.contains("vibrează") || lower.contains("vibra")) {
            systemController.executeCommand(text);
            return;
        }

        // ── Wake word check ──
        if (lower.contains("jarvis") && (lower.contains("oprește") || lower.contains("stop") || lower.contains("taci"))) {
            voiceEngine.stopAutonomous();
            hudView.setState(0);
            hudView.setStatus("JARVIS STANDBY", "Spune 'JARVIS' pentru a reactiva");
            voiceEngine.speak("Am înțeles. Intru în standby. Spune JARVIS când ai nevoie de mine.");
            appendLog("[JARVIS] Mod standby");
            return;
        }

        if (lower.contains("trezește") || lower.contains("reactiveaz") || lower.contains("wake")) {
            if (!voiceEngine.isAutonomous()) {
                voiceEngine.startAutonomous();
                hudView.setState(1);
                hudView.setStatus("JARVIS ONLINE", "Ascult continuu");
                voiceEngine.speak("JARVIS reactivat. Sunt din nou la ordinele tale, stăpâne.");
                appendLog("[JARVIS] Reactivat — mod autonom");
                return;
            }
        }

        // ── Open web app ──
        if (lower.contains("deschide whoamisec") || lower.contains("deschide aplicația") || lower.contains("deschide aplicatia")) {
            Intent intent = new Intent(this, com.whoamisecai.MainActivity.class);
            startActivity(intent);
            voiceEngine.speak("Deschid aplicația WHOAMISecAI.");
            return;
        }

        // ── Telegram ──
        if (lower.contains("telegram") && !lower.contains("osint")) {
            try {
                Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse("https://t.me/whoamisecai"));
                startActivity(intent);
                voiceEngine.speak("Deschid Telegram bot-ul WHOAMISecAI.");
            } catch (Exception e) {
                voiceEngine.speak("Nu pot deschide Telegram.");
            }
            return;
        }

        // ── Default: Send to AI Engine ──
        aiEngine.processCommand(text);
    }

    // ── UI Updates ──

    private void setTranscript(String text) {
        if (transcriptText != null) {
            transcriptText.setText(text);
            transcriptText.setVisibility(View.VISIBLE);
            // Auto-hide after 5s
            handler.postDelayed(() -> {
                if (transcriptText != null) transcriptText.setVisibility(View.GONE);
            }, 5000);
        }
    }

    private void appendResponse(String text) {
        if (responseText != null) {
            responseText.setText(text);
        }
    }

    private void appendLog(String entry) {
        commandHistory.insert(0, entry + "\n");
        // Keep last 50 lines
        String log = commandHistory.toString();
        int lines = log.split("\n").length;
        if (lines > 50) {
            String[] parts = log.split("\n");
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < 50; i++) sb.append(parts[i]).append("\n");
            commandHistory = sb;
        }
        if (commandLog != null) {
            commandLog.setText(commandHistory.toString());
        }
    }

    // ── Lifecycle ──

    @Override
    protected void onResume() {
        super.onResume();
        // Re-engage autonomous mode on resume
        if (voiceEngine != null && isJarvisActive && !voiceEngine.isAutonomous()) {
            voiceEngine.startAutonomous();
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        // Keep listening even when paused — JARVIS never stops
        if (voiceEngine != null && isJarvisActive) {
            // Continue autonomous mode
        }
    }

    @Override
    protected void onDestroy() {
        isJarvisActive = false;
        if (voiceEngine != null) voiceEngine.destroy();
        if (aiEngine != null) aiEngine.destroy();
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        // JARVIS doesn't exit easily — confirm first
        if (voiceEngine != null) {
            voiceEngine.speak("Confirmă ieșirea sau spune JARVIS pentru a rămâne activ.");
        }
        // Double-tap to exit
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            // Allow back on second press
            finish();
        } else {
            super.onBackPressed();
        }
    }
}
