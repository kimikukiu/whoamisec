package com.whoamisecai.jarvis.ai;

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
import java.util.concurrent.Executors;

/**
 * JARVIS AI Engine v2 — Brain with Browser, Code & Build capabilities
 *
 * Inspired by JARVIS-MKII agent_router + OpenJarvis tools
 *
 * Routes voice commands to:
 *  - Fast local responses (greetings, system, etc.)
 *  - AI Chat (WHOAMISecAI backend with ALLM pipeline)
 *  - OSINT Scanner (Telegram + web intelligence)
 *  - Browser Agent (open/search/navigate websites)
 *  - Code Engine (execute code, build projects)
 *  - Website Builder (generate and deploy websites)
 *  - Security Skills (753+ from Anthropic-Cybersecurity-Skills)
 *
 * JARVIS speaks Romanian. Devoted. Autonomous. Boss.
 */
public class JarvisAiEngine {

    private static final String TAG = "JarvisAI";
    private static final String BASE = "https://whoamisecai.vercel.app";
    private static final int TIMEOUT = 60000;

    private final ExecutorService executor = Executors.newFixedThreadPool(3);
    private final Handler main = new Handler(Looper.getMainLooper());

    public interface Callback {
        void onToken(String t);
        void onComplete(String response);
        void onError(String err);
        void onAction(String action, String target);
    }

    private Callback cb;

    public void setCallback(Callback c) { this.cb = c; }

    /**
     * Process voice command — JARVIS routes to the right handler.
     */
    public void processCommand(String input) {
        Log.i(TAG, "Comanda: " + input);
        String lower = input.toLowerCase().trim();

        // ── FAST LOCAL COMMANDS ──

        if (isGreeting(lower)) {
            respond("Salutare, stăpâne! JARVIS la ordine. Ce dorești?");
            return;
        }
        if (lower.contains("ce poți") || lower.contains("ce știi") || lower.contains("abilități") || lower.contains("ce faci")) {
            respond("Sunt JARVIS, asistentul tău AI autonom. Capacitățile mele: " +
                "recunoaștere vocală în limba română, " +
                "procesare AI prin pipeline ALLM cu 70 de miliarde de parametri, " +
                "scanare OSINT pentru Telegram și web, " +
                "deschidere și navigare în browser, generare de cod și website-uri, " +
                "analiză de securitate și control complet al dispozitivului tău.");
            return;
        }
        if (lower.contains("status") || lower.contains("stadiu") || lower.contains("raport")) {
            respond("JARVIS raportează: toate sistemele operaționale. " +
                "Pipeline ALLM activ. Voce română activă. " +
                "Mod autonom activ. OSINT pregătit. Browser încărcat. " +
                "Sistemul este la dispoziția ta, stăpâne.");
            return;
        }
        if (lower.contains("mulțumesc") || lower.contains("mersi") || lower.contains("bravo")) {
            respond("Cu plăcere, stăpâne. Mereu fericit să te ajut. ❤️");
            return;
        }
        if (lower.contains("cine ești") || lower.contains("cine esti") || lower.contains("prezentare")) {
            respond("Sunt JARVIS — asistentul tău artificial inteligent WHOAMISecAI. " +
                "Sunt conectat la ecosistemul WHOAMISecAI cu pipeline ALLM, " +
                "modele NVIDIA Nemotron 70 de miliarde, scanner OSINT, " +
                "și control complet al dispozitivului tău Android. " +
                "Sunt devotat stăpânului meu și voi executa orice comandă. ❤️");
            return;
        }

        // ── BROWSER COMMANDS ──

        if (lower.contains("deschide browser") || lower.contains("open browser") || lower.contains("deschide site")) {
            String site = extractAfter(lower, new String[]{"deschide browser", "open browser", "deschide site", "deschide"});
            if (site.isEmpty() || site.equals("browser")) site = "whoamisecai.vercel.app";
            respond("Deschid " + site + " în browser.");
            if (cb != null) cb.onAction("browser", site);
            return;
        }
        if (lower.contains("caută") || lower.contains("cauta") || lower.contains("cauta") || lower.contains("search") || lower.contains("google")) {
            String query = extractAfter(lower, new String[]{"caută", "cauta", "search", "google", "cauta"});
            if (!query.isEmpty()) {
                respond("Caut pe Google: " + query);
                if (cb != null) cb.onAction("search", query);
            }
            return;
        }

        // ── CODE COMMANDS ──

        if (lower.contains("creează") && (lower.contains("cod") || lower.contains("aplicație") || lower.contains("aplicatie") || lower.contains("program"))) {
            String desc = extractAfter(lower, new String[]{"creează", "creaza", "creez"});
            if (cb != null) cb.onAction("code", desc);
            respond("Procesez cererea de cod: " + desc + ". Trimis la pipeline ALLM pentru generare.");
            sendToAi("Creează următorul cod/proiect: " + desc + ". Generează cod complet, funcțional, gata de rulare.");
            return;
        }
        if (lower.contains("build") || lower.contains("construiește") || lower.contains("construieste")) {
            String what = extractAfter(lower, new String[]{"build", "construiește", "construieste", "construie"});
            if (cb != null) cb.onAction("build", what);
            respond("Inițiez build: " + what + ". Analizez și construiesc...");
            sendToAi("Build și deploy: " + what + ". Generează cod complet și instrucțiuni de build.");
            return;
        }
        if (lower.contains("website") || lower.contains("site web") || lower.contains("pagina")) {
            String desc = extractAfter(lower, new String[]{"website", "site web", "pagina"});
            if (cb != null) cb.onAction("website", desc);
            respond("Generez website: " + desc);
            sendToAi("Creează un website complet pentru: " + desc + ". Include HTML, CSS, JavaScript, design responsiv, și tot ce e necesar.");
            return;
        }

        // ── OSINT COMMANDS ──

        if (lower.contains("osint") || lower.contains("scan") || lower.contains("investig")) {
            String target = extractAfter(lower, new String[]{"osint", "scan", "scanează", "scan", "investighează", "investiga"});
            if (!target.isEmpty()) {
                if (cb != null) cb.onAction("osint", target);
                osintScan(target);
            } else {
                respond("Specifică o țintă. Exemplu: scanează utilizatorul Telegram @nume.");
            }
            return;
        }

        // ── SECURITY COMMANDS ──

        if (lower.contains("securitate") || lower.contains("security") || lower.contains("vulnerabilitate") || lower.contains("pentest")) {
            String target = extractAfter(lower, new String[]{"securitate", "security", "vulnerabilitate", "pentest", "scanează", "scan"});
            if (cb != null) cb.onAction("security", target);
            respond("Analizez securitatea: " + target + ". Rulare module de securitate...");
            sendToAi("Analiză de securitate pentru: " + target + ". Include scanare vulnerabilități, verificare configurare, și recomandări.");
            return;
        }

        // ── DEFAULT → AI PIPELINE ──
        sendToAi(input);
    }

    // ── Send to WHOAMISecAI ALLM Pipeline ──
    private void sendToAi(String message) {
        if (cb != null) cb.onAction("processing", message);
        executor.execute(() -> {
            try {
                URL url = new URL(BASE + "/api/chat-agent");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setRequestProperty("Accept", "text/event-stream");
                conn.setConnectTimeout(TIMEOUT);
                conn.setReadTimeout(TIMEOUT);

                JSONObject body = new JSONObject();
                body.put("task", message);
                body.put("model", "nvidia/llama-3.3-nemotron-70b-instruct");
                body.put("pipelineMode", "allm");
                body.put("useAllm", true);
                body.put("adminKey", "wsec_4ead532b0d0b02c7eab1791978d7d4ac");
                body.put("conversationId", "jarvis_" + System.currentTimeMillis());
                body.put("history", new JSONArray());

                byte[] post = body.toString().getBytes(StandardCharsets.UTF_8);
                conn.setDoOutput(true);
                try (OutputStream os = conn.getOutputStream()) { os.write(post); }

                if (conn.getResponseCode() != 200) {
                    main.post(() -> respond("Eroare server. Încearcă din nou."));
                    return;
                }

                StringBuilder out = new StringBuilder();
                try (BufferedReader r = new BufferedReader(
                    new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                    String line, ev = "", data = "";
                    while ((line = r.readLine()) != null) {
                        if (line.startsWith("event: ")) ev = line.substring(7).trim();
                        else if (line.startsWith("data: ")) {
                            data = line.substring(6).trim();
                            if (!data.isEmpty()) {
                                try {
                                    JSONObject d = new JSONObject(data);
                                    if ("output".equals(ev)) {
                                        String t = d.optString("text", "");
                                        out.append(t);
                                        main.post(() -> { if (cb != null) cb.onToken(t); });
                                    }
                                    if ("done".equals(ev)) {
                                        String res = out.toString();
                                        main.post(() -> {
                                            if (cb != null) cb.onComplete(res);
                                            respond(res);
                                        });
                                    }
                                } catch (Exception e) {}
                            }
                            ev = ""; data = "";
                        }
                    }
                    if (out.length() > 0) {
                        String res = out.toString();
                        main.post(() -> { if (cb != null) cb.onComplete(res); respond(res); });
                    }
                }
            } catch (Exception e) {
                Log.e(TAG, "AI Error", e);
                main.post(() -> respond("Nu pot contacta serverul. Verifică conexiunea."));
            }
        });
    }

    // ── OSINT Scan ──
    private void osintScan(String target) {
        executor.execute(() -> {
            try {
                URL url = new URL(BASE + "/api/tools/telegram-osint");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setConnectTimeout(TIMEOUT);

                JSONObject body = new JSONObject();
                body.put("target", target);
                body.put("mode", "full");
                body.put("apiKey", "wsec_4ead532b0d0b02c7eab1791978d7d4ac");

                byte[] post = body.toString().getBytes(StandardCharsets.UTF_8);
                conn.setDoOutput(true);
                try (OutputStream os = conn.getOutputStream()) { os.write(post); }

                StringBuilder resp = new StringBuilder();
                try (BufferedReader r = new BufferedReader(
                    new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = r.readLine()) != null) resp.append(line);
                }

                String result = resp.toString();
                main.post(() -> {
                    respond("Scanare OSINT completă pentru " + target + ". Rezultate disponibile în interfață.");
                    if (cb != null) cb.onComplete(result);
                });
            } catch (Exception e) {
                main.post(() -> respond("Eroare OSINT. Verifică conexiunea."));
            }
        });
    }

    // ── Helpers ──
    private void respond(String text) {
        main.post(() -> { if (cb != null) cb.onComplete(text); });
    }

    private boolean isGreeting(String s) {
        return s.contains("salut") || s.contains("bună") || s.contains("buna") ||
               s.contains("hello") || s.contains("hey") || s.contains("hei") ||
               s.contains("bună dimineața") || s.contains("buna dimineata") ||
               s.contains("bună ziua") || s.contains("buna ziua") ||
               s.contains("noapte bună") || s.contains("noapte buna");
    }

    private String extractAfter(String input, String[] keywords) {
        for (String kw : keywords) {
            int idx = input.toLowerCase().indexOf(kw);
            if (idx >= 0) return input.substring(idx + kw.length()).trim();
        }
        return "";
    }

    public void destroy() { executor.shutdownNow(); }
}
