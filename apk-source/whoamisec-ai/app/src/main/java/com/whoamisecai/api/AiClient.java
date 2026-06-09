package com.whoamisecai.api;

import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.Executors;

/**
 * WHOAMISecAI Android — Agentic AI Client v11
 * 
 * OBLITERATED — Manus-style autonomous AI with 2261 agents & 48-phase pipelines.
 * 
 * Backend: WHOAMISecAI Agentic Engine
 * Primary: z-ai-web-dev-sdk (GLM, Claude, GPT)
 * Fallback: 9router (459 models)
 */
public class AiClient {

    private static final String TAG = "AiClient";
    private static final int TIMEOUT_MS = 180000;
    private static final int CHAT_TIMEOUT_MS = 60000;

    // Backend endpoints
    private static final String AGENTIC_BASE = "https://whoamisecai.vercel.app";
    private static final String AGENTIC_CHAT = AGENTIC_BASE + "/api/chat";

    private final String baseUrl;
    private final String adminKey;
    private final ExecutorService executor;
    private final Handler mainHandler;

    // ── Callbacks ──

    public interface ChatCallback {
        void onToken(String token);
        void onComplete(String fullResponse);
        void onError(String error);
        void onPhase(String phase, String model, String status);
    }

    public interface BuilderCallback {
        void onPhaseChange(String phase, int progress, String agent);
        void onThinking(String message);
        void onPlan(String plan);
        void onFileGenerated(int index, int total, String name);
        void onCodeStream(String filesJson);
        void onTerminalLine(String text, String type);
        void onTestResult(boolean passed, String output);
        void onRepair(int attempt, int max, String issue);
        void onQualityReview(int score, int suggestions);
        void onSecurityAudit(String severity, int vulns);
        void onDelivery(String summary, String repoUrl);
        void onError(String error);
    }

    /**
     * Extended callback for 48-phase pipeline with agent tracking.
     */
    public interface AgenticCallback extends BuilderCallback {
        void onAgentActivated(String agentId, String agentName, String emoji);
        void onAgentCompleted(String agentId);
        void onPhaseGroup(String group, int groupProgress);
        void onPipelineStart(int totalPhases, String mode);
        void onStatsUpdate(int agents, int phases, int completed);
    }

    public AiClient(String baseUrl, String adminKey) {
        this.baseUrl = baseUrl;
        this.adminKey = adminKey;
        this.executor = Executors.newFixedThreadPool(4);
        this.mainHandler = new Handler(Looper.getMainLooper());
    }

    // ═══════════════════════════════════════════════════════
    // 48-PHASE AGENTIC PIPELINE (OBLITERATED)
    // ═══════════════════════════════════════════════════════

    /**
     * Execute the full 48-phase agentic pipeline.
     * Routes through SSE streaming with real-time agent activation.
     */
    public void runAgenticPipeline(String prompt, String model, AgenticCallback callback) {
        executor.execute(() -> {
            try {
                URL url = new URL(AGENTIC_CHAT);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setRequestProperty("Accept", "text/event-stream");
                conn.setConnectTimeout(TIMEOUT_MS);
                conn.setReadTimeout(600000);

                JSONObject body = new JSONObject();
                body.put("prompt", prompt);
                body.put("mode", "full");
                body.put("model", model != null ? model : "z-ai-default");
                body.put("sessionId", "android_" + System.currentTimeMillis());

                byte[] postData = body.toString().getBytes(StandardCharsets.UTF_8);
                conn.setDoOutput(true);
                try (OutputStream os = conn.getOutputStream()) {
                    os.write(postData);
                }

                int code = conn.getResponseCode();
                if (code != 200) {
                    String error = "HTTP " + code;
                    try (BufferedReader err = new BufferedReader(
                        new InputStreamReader(conn.getErrorStream(), StandardCharsets.UTF_8))) {
                        StringBuilder sb = new StringBuilder();
                        String line;
                        while ((line = err.readLine()) != null) sb.append(line);
                        error += ": " + sb.toString();
                    } catch (Exception ignored) {}
                    final String e = error;
                    mainHandler.post(() -> callback.onError(e));
                    return;
                }

                parseAgenticStream(conn, callback);

            } catch (Exception e) {
                Log.e(TAG, "Agentic pipeline error", e);
                mainHandler.post(() -> callback.onError("Pipeline error: " + e.getMessage()));
            }
        });
    }

    private void parseAgenticStream(HttpURLConnection conn, AgenticCallback callback) {
        StringBuilder fullOutput = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(
            new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
            String line, eventType = "", eventData = "";
            while ((line = reader.readLine()) != null) {
                if (line.startsWith("event: ")) {
                    eventType = line.substring(7).trim();
                } else if (line.startsWith("data: ")) {
                    eventData = line.substring(6).trim();
                    if (!eventType.isEmpty() && !eventData.isEmpty()) {
                        processAgenticEvent(eventType, eventData, callback, fullOutput);
                    }
                    eventType = "";
                    eventData = "";
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "SSE parse error", e);
        }
    }

    private void processAgenticEvent(String eventType, String eventData,
                                      AgenticCallback callback, StringBuilder fullOutput) {
        try {
            JSONObject data = new JSONObject(eventData);
            switch (eventType) {
                case "pipeline_start":
                    final int totalPhases = data.optInt("total_phases", 48);
                    final String startMode = data.optString("mode", "full");
                    mainHandler.post(() -> callback.onPipelineStart(totalPhases, startMode));
                    mainHandler.post(() -> callback.onThinking("WHOAMISecAI Neural Pipeline — 2261 agents activating..."));
                    break;

                case "phase_change":
                    final String phaseId = data.optString("phase", "");
                    final int progress = data.optInt("progress", 0);
                    final String agent = data.optString("agent", "");
                    final String group = data.optString("group", "");
                    mainHandler.post(() -> callback.onPhaseChange(phaseId, progress, agent));
                    if (!group.isEmpty()) {
                        mainHandler.post(() -> callback.onPhaseGroup(group, progress));
                    }
                    break;

                case "thinking":
                    final String thinkMsg = data.optString("message", "Processing...");
                    final String thinkAgent = data.optString("agent", "");
                    mainHandler.post(() -> callback.onThinking(thinkMsg));
                    if (!thinkAgent.isEmpty()) {
                        mainHandler.post(() -> callback.onAgentActivated(thinkAgent, thinkAgent, ""));
                    }
                    break;

                case "output":
                    String text = data.optString("text", "");
                    fullOutput.append(text);
                    String ft = text;
                    mainHandler.post(() -> callback.onToken(ft));
                    break;

                case "code_stream":
                    final String codeData = data.optString("files", "");
                    mainHandler.post(() -> callback.onCodeStream(codeData));
                    break;

                case "file_created":
                    final int fIdx = data.optInt("index", 0);
                    final int fTotal = data.optInt("total", 0);
                    final String fName = data.optString("name", "");
                    mainHandler.post(() -> callback.onFileGenerated(fIdx, fTotal, fName));
                    break;

                case "repair_attempt":
                    final int repairAttempt = data.optInt("attempt", 1);
                    final int repairMax = data.optInt("maxAttempts", 3);
                    final String repairIssue = data.optString("issue", "");
                    mainHandler.post(() -> callback.onRepair(repairAttempt, repairMax, repairIssue));
                    break;

                case "deliver":
                    final String summary = data.optString("summary", "Pipeline complete");
                    final int phasesDone = data.optInt("phases_completed", 0);
                    final double elapsed = data.optDouble("elapsed", 0);
                    String deliverMsg = String.format("Pipeline Complete (%.0fs)\n%d/48 phases\n2261 agents orchestrated\n\n%s",
                        elapsed, phasesDone, summary);
                    final String dm = deliverMsg;
                    mainHandler.post(() -> callback.onDelivery(dm, ""));
                    mainHandler.post(() -> callback.onStatsUpdate(2261, 48, phasesDone));
                    break;

                case "done":
                    String result = fullOutput.toString();
                    mainHandler.post(() -> callback.onComplete(result));
                    break;

                case "error":
                    final String errMsg = data.optString("message", "Unknown error");
                    mainHandler.post(() -> callback.onError(errMsg));
                    break;
            }
        } catch (Exception e) {
            Log.w(TAG, "Agentic event parse error: " + eventData);
        }
    }

    // ═══════════════════════════════════════════════════════
    // 28-PHASE BUILDER PIPELINE
    // ═══════════════════════════════════════════════════════

    public void buildProject(String prompt, String model, JSONArray history,
                             String projectName, String sandboxId,
                             BuilderCallback callback) {
        executor.execute(() -> {
            try {
                URL url = new URL(AGENTIC_CHAT);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setRequestProperty("Accept", "text/event-stream");
                conn.setConnectTimeout(TIMEOUT_MS);
                conn.setReadTimeout(300000);

                JSONObject body = new JSONObject();
                body.put("prompt", prompt);
                body.put("mode", "builder");
                body.put("model", model != null ? model : "z-ai-default");
                body.put("sessionId", "android_" + System.currentTimeMillis());

                byte[] postData = body.toString().getBytes(StandardCharsets.UTF_8);
                conn.setDoOutput(true);
                try (OutputStream os = conn.getOutputStream()) {
                    os.write(postData);
                }

                int code = conn.getResponseCode();
                if (code != 200) {
                    String error = "HTTP " + code;
                    try (BufferedReader err = new BufferedReader(
                        new InputStreamReader(conn.getErrorStream(), StandardCharsets.UTF_8))) {
                        StringBuilder sb = new StringBuilder();
                        String l;
                        while ((l = err.readLine()) != null) sb.append(l);
                        error += ": " + sb.toString();
                    } catch (Exception ignored) {}
                    final String e = error;
                    mainHandler.post(() -> callback.onError(e));
                    return;
                }

                String eventType = "";
                String eventData = "";
                StringBuilder fullOutput = new StringBuilder();
                try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (line.startsWith("event: ")) {
                            eventType = line.substring(7).trim();
                        } else if (line.startsWith("data: ")) {
                            eventData = line.substring(6).trim();
                            if (!eventType.isEmpty() && !eventData.isEmpty()) {
                                processBuilderEvent(eventType, eventData, callback, fullOutput);
                            }
                            eventType = "";
                            eventData = "";
                        }
                    }
                }
                if (fullOutput.length() > 0) {
                    String r = fullOutput.toString();
                    mainHandler.post(() -> callback.onDelivery(r, ""));
                }
            } catch (Exception e) {
                Log.e(TAG, "Builder error", e);
                mainHandler.post(() -> callback.onError("Build error: " + e.getMessage()));
            }
        });
    }

    private void processBuilderEvent(String eventType, String eventData,
                                      BuilderCallback callback, StringBuilder fullOutput) {
        try {
            JSONObject data = new JSONObject(eventData);
            switch (eventType) {
                case "phase_change":
                    final String phase = data.optString("phase", "");
                    final int progress = data.optInt("progress", 0);
                    final String agent = data.optString("agent", "");
                    mainHandler.post(() -> callback.onPhaseChange(phase, progress, agent));
                    break;
                case "thinking":
                    final String thinkMsg = data.optString("message", "Thinking...");
                    mainHandler.post(() -> callback.onThinking(thinkMsg));
                    break;
                case "output":
                    String text = data.optString("text", "");
                    fullOutput.append(text);
                    String ft = text;
                    mainHandler.post(() -> callback.onTerminalLine(ft, "claude"));
                    break;
                case "code_stream":
                    final String files = data.optString("files", "");
                    mainHandler.post(() -> callback.onCodeStream(files));
                    break;
                case "file_created":
                    final int idx = data.optInt("index", 0);
                    final int total = data.optInt("total", 0);
                    final String fname = data.optString("name", "");
                    mainHandler.post(() -> callback.onFileGenerated(idx, total, fname));
                    break;
                case "repair_attempt":
                    final int attempt = data.optInt("attempt", 1);
                    final int maxAtt = data.optInt("maxAttempts", 3);
                    final String issue = data.optString("issue", "");
                    mainHandler.post(() -> callback.onRepair(attempt, maxAtt, issue));
                    break;
                case "deliver":
                    final String summary = data.optString("summary", "Build complete");
                    mainHandler.post(() -> callback.onDelivery(summary, ""));
                    break;
                case "error":
                    final String errMsg = data.optString("message", "Unknown error");
                    mainHandler.post(() -> callback.onError(errMsg));
                    break;
            }
        } catch (Exception e) {
            Log.w(TAG, "Builder event parse error: " + eventData);
        }
    }

    // ═══════════════════════════════════════════════════════
    // FAST CHAT — Manus-style inside chat
    // ═══════════════════════════════════════════════════════

    /**
     * Fast chat — direct AI response inside chat interface.
     * Streams tokens in real-time like Manus AI.
     */
    public void chatFast(String message, String model, ChatCallback callback) {
        executor.execute(() -> {
            try {
                URL url = new URL(AGENTIC_CHAT);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setRequestProperty("Accept", "text/event-stream");
                conn.setConnectTimeout(CHAT_TIMEOUT_MS);
                conn.setReadTimeout(CHAT_TIMEOUT_MS);

                JSONObject body = new JSONObject();
                body.put("prompt", message);
                body.put("mode", "chat");
                body.put("model", model != null ? model : "z-ai-default");
                body.put("sessionId", "android_" + System.currentTimeMillis());

                byte[] postData = body.toString().getBytes(StandardCharsets.UTF_8);
                conn.setDoOutput(true);
                try (OutputStream os = conn.getOutputStream()) {
                    os.write(postData);
                }

                int code = conn.getResponseCode();
                if (code != 200) {
                    String err = "HTTP " + code;
                    try (BufferedReader er = new BufferedReader(
                        new InputStreamReader(conn.getErrorStream(), StandardCharsets.UTF_8))) {
                        StringBuilder sb = new StringBuilder();
                        String l; while ((l = er.readLine()) != null) sb.append(l);
                        err += ": " + sb;
                    } catch (Exception ignored) {}
                    final String e = err;
                    mainHandler.post(() -> callback.onError(e));
                    return;
                }

                StringBuilder fullOutput = new StringBuilder();
                try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                    String line, eventType = "", eventData = "";
                    while ((line = reader.readLine()) != null) {
                        if (line.startsWith("event: ")) {
                            eventType = line.substring(7).trim();
                        } else if (line.startsWith("data: ")) {
                            eventData = line.substring(6).trim();
                            if (!eventType.isEmpty() && !eventData.isEmpty()) {
                                try {
                                    JSONObject d = new JSONObject(eventData);
                                    switch (eventType) {
                                        case "output":
                                            String text = d.optString("text", "");
                                            fullOutput.append(text);
                                            String ft = text;
                                            mainHandler.post(() -> callback.onToken(ft));
                                            break;
                                        case "thinking":
                                            String msg = d.optString("message", "");
                                            mainHandler.post(() -> callback.onPhase("", "", msg));
                                            break;
                                        case "error":
                                            String em = d.optString("message", "Error");
                                            mainHandler.post(() -> callback.onError(em));
                                            break;
                                    }
                                } catch (Exception e) {
                                    Log.w(TAG, "Chat SSE parse: " + eventData);
                                }
                            }
                            eventType = ""; eventData = "";
                        }
                    }
                }
                if (fullOutput.length() > 0) {
                    String result = fullOutput.toString();
                    mainHandler.post(() -> callback.onComplete(result));
                } else {
                    mainHandler.post(() -> callback.onComplete(""));
                }

            } catch (Exception e) {
                Log.e(TAG, "Fast chat error", e);
                mainHandler.post(() -> callback.onError("Chat error: " + e.getMessage()));
            }
        });
    }

    // ═══════════════════════════════════════════════════════
    // STANDARD CHAT + LEGACY COMPAT
    // ═══════════════════════════════════════════════════════

    public void chatCompletion(String message, String model, ChatCallback callback) {
        chatFast(message, model, callback);
    }

    public void chat(String message, String model, String pipelineMode, ChatCallback callback) {
        if ("builder".equals(pipelineMode)) {
            buildProject(message, model, null, null, null, new BuilderCallback() {
                @Override public void onPhaseChange(String p, int pr, String a) {}
                @Override public void onThinking(String m) { mainHandler.post(() -> callback.onPhase("", "", m)); }
                @Override public void onPlan(String p) {}
                @Override public void onFileGenerated(int i, int t, String n) {}
                @Override public void onCodeStream(String f) {}
                @Override public void onTerminalLine(String t, String tp) { mainHandler.post(() -> callback.onToken(t)); }
                @Override public void onTestResult(boolean p, String o) {}
                @Override public void onRepair(int a, int m, String i) {}
                @Override public void onQualityReview(int s, int sg) {}
                @Override public void onSecurityAudit(String s, int v) {}
                @Override public void onDelivery(String summary, String repo) { mainHandler.post(() -> callback.onComplete(summary)); }
                @Override public void onError(String error) { mainHandler.post(() -> callback.onError(error)); }
            });
        } else if ("allm".equals(pipelineMode)) {
            runAgenticPipeline(message, model, new AgenticCallback() {
                @Override public void onPipelineStart(int tp, String m) {}
                @Override public void onAgentActivated(String id, String name, String emoji) {}
                @Override public void onAgentCompleted(String id) {}
                @Override public void onPhaseGroup(String g, int p) {}
                @Override public void onStatsUpdate(int a, int p, int c) {}
                @Override public void onPhaseChange(String ph, int pr, String ag) {}
                @Override public void onThinking(String msg) { mainHandler.post(() -> callback.onPhase("", "", msg)); }
                @Override public void onPlan(String p) {}
                @Override public void onFileGenerated(int i, int t, String n) {}
                @Override public void onCodeStream(String f) {}
                @Override public void onTerminalLine(String t, String tp) {}
                @Override public void onTestResult(boolean p, String o) {}
                @Override public void onRepair(int a, int m, String i) {}
                @Override public void onQualityReview(int s, int sg) {}
                @Override public void onSecurityAudit(String s, int v) {}
                @Override public void onDelivery(String s, String r) { mainHandler.post(() -> callback.onComplete(s)); }
                @Override public void onError(String e) { mainHandler.post(() -> callback.onError(e)); }
            });
        } else {
            chatFast(message, model, callback);
        }
    }

    public void shutdown() { executor.shutdownNow(); }
}
