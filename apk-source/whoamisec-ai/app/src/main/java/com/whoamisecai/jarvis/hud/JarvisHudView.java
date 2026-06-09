package com.whoamisecai.jarvis.hud;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.SweepGradient;
import android.util.AttributeSet;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * JARVIS HUD — MKII-Inspired Holographic Renderer
 *
 * Inspired by JARVIS-MKII (github.com/whoamisecai/JARVIS-MKII)
 * Complete Iron Man HUD experience on Android Canvas:
 *
 *  - Boot sequence (15-step staggered initialization)
 *  - Iron Man wireframe suit with 3D rotation
 *  - Arc reactor with 12 tick marks + pulsing glow
 *  - Rotating concentric arcs (5 rings, variable speed)
 *  - Radar sweep with gradient cone
 *  - Audio waveform + level meter
 *  - Corner brackets with pulse
 *  - Scanline + vignette + hex grid overlay
 *  - Alert ticker (scrolling status bar)
 *  - Particle burst system
 *  - Data streams (vertical)
 *  - State indicators (IDLE/LISTENING/PROCESSING/SPEAKING)
 *
 * Color palette: Cyan (#00D4FF), Teal (#00FFC8), Purple (#8B5CF6),
 *                Orange (#FF9500), Green (#00FF87), Red (#FF3B30)
 *
 * Optimized for 60fps on Android — all Canvas 2D, no OpenGL needed.
 */
public class JarvisHudView extends SurfaceView implements SurfaceHolder.Callback {

    // ── Colors ──
    private static final int CYAN       = 0xFF00D4FF;
    private static final int TEAL       = 0xFF00FFC8;
    private static final int PURPLE     = 0xFF8B5CF6;
    private static final int GREEN      = 0xFF00FF87;
    private static final int RED        = 0xFFFF3B30;
    private static final int ORANGE     = 0xFFFF9500;
    private static final int DIM_CYAN   = 0x1A00D4FF;
    private static final int MID_CYAN   = 0x4400D4FF;
    private static final int BG         = 0xFF000000;

    // ── State ──
    private volatile boolean running = false;
    private volatile float frame = 0f;
    private volatile float radarAngle = 0f;
    private volatile int breathPhase = 0;
    private volatile float audioLevel = 0f;
    private volatile String statusText = "";
    private volatile String subStatusText = "";
    private volatile int hudState = 0; // 0=idle 1=listening 2=processing 3=speaking
    private volatile int bootPhase = 0; // 0-14 boot sequence
    private volatile boolean bootComplete = false;
    private final Random rng = new Random();

    // ── Particles ──
    private final List<Particle> particles = new ArrayList<>();

    // ── Audio waveform ──
    private final float[] waveform = new float[64];
    private int waveIdx = 0;

    // ── Alert ticker ──
    private static final String[] ALERTS = {
        "SYS FEED — ALL SYSTEMS OPERATIONAL",
        "WHOAMISecAI v1.0 — ALLM PIPELINE ACTIVE",
        "OSINT MODULE READY — ADMIN ACCESS GRANTED",
        "JARVIS AI ONLINE — ROMANIAN VOICE ENGINE LOADED",
        "SECURITY: FIREWALL ACTIVE — THREAT LEVEL LOW",
        "NETWORK: SECURE CONNECTION — TLS 1.3",
        "AI MODELS: NVIDIA NEMOTRON 70B — READY",
        "MEMORY: OPTIMIZED — CACHE PRIMED",
        "AUTONOMOUS MODE: ACTIVE — CONTINUOUS LISTENING",
        "BROWSER MODULE: LOADED — READY TO NAVIGATE",
        "CODE ENGINE: COMPILER READY — PYTHON/JAVA/NODE",
        "OSINT: TELEGRAM SCANNER — STANDBY",
    };
    private int tickerOffset = 0;

    // ── Dimensions ──
    private int W, H, cx, cy, radius;

    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private Thread renderThread;

    public JarvisHudView(Context c) { super(c); init(); }
    public JarvisHudView(Context c, AttributeSet a) { super(c, a); init(); }
    public JarvisHudView(Context c, AttributeSet a, int d) { super(c, a, d); init(); }

    private void init() {
        setZOrderOnTop(true);
        getHolder().setFormat(PixelFormat.TRANSLUCENT);
        getHolder().addCallback(this);
        for (int i = 0; i < waveform.length; i++) waveform[i] = 0f;
    }

    @Override
    public void surfaceCreated(SurfaceHolder h) {
        W = getWidth(); H = getHeight();
        cx = W / 2; cy = H / 2;
        radius = Math.min(cx, cy) - 50;
        running = true;
        bootPhase = 0; bootComplete = false;
        renderThread = new Thread(this::loop);
        renderThread.start();
    }
    @Override public void surfaceChanged(SurfaceHolder h, int f, int w, int ht) {
        W = w; H = ht; cx = w/2; cy = ht/2; radius = Math.min(cx,cy)-50;
    }
    @Override public void surfaceDestroyed(SurfaceHolder h) {
        running = false;
        try { if (renderThread != null) renderThread.interrupt(); } catch (Exception e) {}
    }

    // ── Public API ──

    public void setAudioLevel(float level) {
        audioLevel = Math.min(1f, Math.max(0f, level));
        waveform[waveIdx % waveform.length] = audioLevel * (0.5f + rng.nextFloat() * 0.5f);
        waveIdx++;
    }

    public void setStatus(String main, String sub) {
        statusText = main != null ? main : "";
        subStatusText = sub != null ? sub : "";
    }

    public void setState(int state) {
        hudState = state;
        switch (state) {
            case 0: setStatus("JARVIS ONLINE", "Sistem pregatit — astept comanda"); break;
            case 1: setStatus("ASCULT...", "Procesez voce romana"); break;
            case 2: setStatus("PROCESEZ...", "Analizez comanda"); break;
            case 3: setStatus("RASPUND...", "JARVIS vorbeste"); break;
        }
    }

    public void triggerBurst() {
        for (int i = 0; i < 15; i++) particles.add(new Particle(cx, cy, rng));
        while (particles.size() > 50) particles.remove(0);
    }

    public boolean isBootComplete() { return bootComplete; }

    // ── Render Loop ──

    private void loop() {
        while (running) {
            Canvas c = null;
            try {
                c = getHolder().lockCanvas();
                if (c != null) {
                    frame += 0.016f;
                    radarAngle += 0.035f;
                    breathPhase++;
                    tickerOffset = (tickerOffset + 1) % (ALERTS.length * 40);
                    // Boot sequence
                    if (!bootComplete) {
                        bootPhase = Math.min(bootPhase + 1, 150);
                        if (bootPhase >= 150) bootComplete = true;
                    }
                    drawAll(c);
                }
            } catch (Exception e) {}
            finally { if (c != null) try { getHolder().unlockCanvasAndPost(c); } catch (Exception e) {} }
            try { Thread.sleep(16); } catch (Exception e) { break; }
        }
    }

    private void drawAll(Canvas c) {
        c.drawColor(BG);
        float boot = Math.min(1f, bootPhase / 150f); // 0..1 boot progress

        drawHexGrid(c, boot * 0.15f);
        drawScanlines(c);
        drawCornerBrackets(c, boot);
        drawRotatingArcs(c, boot);
        drawRadarSweep(c, boot * 0.6f);
        drawInnerRing(c, boot * 0.7f);
        drawArcReactor(c, boot * 0.8f);
        drawSuitWireframe(c, boot * 0.5f);
        drawDataStreams(c, boot * 0.4f);
        drawParticles(c, boot);
        drawWaveform(c, boot * 0.9f);
        drawCornerInfo(c, boot);
        drawTicker(c, boot);
        drawStatusOverlay(c, boot);
        drawStateDots(c, boot);
        drawVignette(c);
    }

    // ── HEX GRID (subtle background) ──
    private void drawHexGrid(Canvas c, float alpha) {
        if (alpha <= 0) return;
        paint.setColor(applyAlpha(0x00D4FF, (int)(10 * alpha)));
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(0.5f);
        float r = 28f;
        float h = (float)(Math.sqrt(3) * r);
        for (int row = -1; row < H / h + 1; row++) {
            for (int col = -1; col < W / (r*2) + 1; col++) {
                float x = col * r * 1.5f;
                float y = row * h + (col % 2 == 0 ? 0 : h / 2);
                Path hex = new Path();
                for (int i = 0; i < 6; i++) {
                    double a = Math.PI / 3 * i - Math.PI / 6;
                    float hx = x + r * (float) Math.cos(a);
                    float hy = y + r * (float) Math.sin(a);
                    if (i == 0) hex.moveTo(hx, hy); else hex.lineTo(hx, hy);
                }
                hex.close();
                c.drawPath(hex, paint);
            }
        }
    }

    // ── SCANLINES ──
    private void drawScanlines(Canvas c) {
        paint.setColor(0x08000000);
        paint.setStyle(Paint.Style.FILL);
        for (int y = 0; y < H; y += 4) {
            c.drawRect(0, y, W, 2, paint);
        }
        // Moving scan bar
        float scanY = (float)((frame * 80) % H);
        paint.setColor(0x0A00D4FF);
        c.drawRect(0, scanY, W, 2, paint);
    }

    // ── CORNER BRACKETS ──
    private void drawCornerBrackets(Canvas c, float alpha) {
        if (alpha <= 0) return;
        paint.setStrokeWidth(2f);
        paint.setStyle(Paint.Style.STROKE);
        int a = (int)(255 * alpha * (0.7f + 0.3f * (float)Math.sin(frame * 3)));
        paint.setColor(applyAlpha(0x00D4FF, a));
        int m = 16, len = 50;
        // TL
        c.drawLine(m, m, m+len, m, paint); c.drawLine(m, m, m, m+len, paint);
        // TR
        c.drawLine(W-m, m, W-m-len, m, paint); c.drawLine(W-m, m, W-m, m+len, paint);
        // BL
        c.drawLine(m, H-m, m+len, H-m, paint); c.drawLine(m, H-m, m, H-m-len, paint);
        // BR
        c.drawLine(W-m, H-m, W-m-len, H-m, paint); c.drawLine(W-m, H-m, W-m, H-m-len, paint);
    }

    // ── ROTATING ARCS (5 concentric rings) ──
    private void drawRotatingArcs(Canvas c, float alpha) {
        if (alpha <= 0) return;
        paint.setStyle(Paint.Style.STROKE);
        float baseR = radius + 25;
        for (int i = 0; i < 5; i++) {
            float r = baseR + i * 12f;
            float speed = (i % 2 == 0 ? 1 : -1) * (0.3f + i * 0.15f);
            float start = frame * speed * 60 + i * 72f;
            float sweep = 40f + 25f * (float)Math.sin(frame * speed + i);
            // Glow intensity based on state
            float glow = (hudState == 3 || hudState == 1) ? 1.5f : 1f;
            int a = (int)(Math.min(255, (60 + 30 * Math.sin(frame * 2 + i * 1.5)) * alpha * glow));
            paint.setColor(applyAlpha(0x00D4FF, a));
            paint.setStrokeWidth(hudState == 3 ? 3f : 2f);
            RectF rect = new RectF(cx-r, cy-r, cx+r, cy+r);
            c.drawArc(rect, start, sweep, false, paint);
        }
    }

    // ── RADAR SWEEP ──
    private void drawRadarSweep(Canvas c, float alpha) {
        if (alpha <= 0) return;
        float r = radius - 15;
        // Sweep cone
        for (int i = 0; i < 40; i++) {
            float a = radarAngle - (float)Math.toRadians(i * 1.5);
            int al = (int)((hudState == 1 ? 50 : 15) * alpha - i);
            if (al <= 0) break;
            paint.setColor(applyAlpha(0x00D4FF, al));
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(1f);
            c.drawLine(cx, cy, cx + r * (float)Math.cos(a), cy + r * (float)Math.sin(a), paint);
        }
        // Concentric circles
        paint.setColor(applyAlpha(0x00D4FF, (int)(20 * alpha)));
        paint.setStrokeWidth(0.5f);
        for (int i = 1; i <= 5; i++) {
            c.drawCircle(cx, cy, r * i / 5, paint);
        }
        // Cross hairs
        c.drawLine(cx - r, cy, cx + r, cy, paint);
        c.drawLine(cx, cy - r, cx, cy + r, paint);
    }

    // ── INNER RING with tick marks ──
    private void drawInnerRing(Canvas c, float alpha) {
        if (alpha <= 0) return;
        float r = radius * 0.55f;
        int col = hudState == 2 ? PURPLE : (hudState == 3 ? GREEN : CYAN);
        paint.setColor(applyAlpha(col, (int)(200 * alpha)));
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(2f);
        c.drawCircle(cx, cy, r, paint);
        // 72 tick marks
        paint.setStrokeWidth(1f);
        for (int i = 0; i < 72; i++) {
            float a = (float)Math.toRadians(i * 5);
            float len = i % 6 == 0 ? 14f : 5f;
            float x1 = cx + r * (float)Math.cos(a);
            float y1 = cy + r * (float)Math.sin(a);
            float x2 = cx + (r + len) * (float)Math.cos(a);
            float y2 = cy + (r + len) * (float)Math.sin(a);
            paint.setColor(applyAlpha(col, (int)(i % 6 == 0 ? 180 * alpha : 60 * alpha)));
            c.drawLine(x1, y1, x2, y2, paint);
        }
    }

    // ── ARC REACTOR ──
    private void drawArcReactor(Canvas c, float alpha) {
        if (alpha <= 0) return;
        float breath = 1f + 0.18f * (float)Math.sin(breathPhase * 0.04f);
        float coreR = 30f * breath;
        int col = hudState == 1 ? ORANGE : (hudState == 2 ? PURPLE : (hudState == 3 ? GREEN : CYAN));
        // Glow layers
        for (int i = 4; i >= 0; i--) {
            float gr = coreR + i * 10;
            int a = (int)((40 - i * 8) * alpha * (hudState >= 2 ? 1.5f : 1f));
            paint.setColor(applyAlpha(col, Math.max(0, a)));
            paint.setStyle(Paint.Style.FILL);
            c.drawCircle(cx, cy, gr, paint);
        }
        // Core
        paint.setColor(applyAlpha(col, (int)(255 * alpha)));
        c.drawCircle(cx, cy, coreR, paint);
        // Inner rings
        paint.setColor(applyAlpha(0x000000, (int)(200 * alpha)));
        c.drawCircle(cx, cy, coreR * 0.6f, paint);
        paint.setColor(applyAlpha(col, (int)(200 * alpha)));
        c.drawCircle(cx, cy, coreR * 0.4f, paint);
        // 12 tick marks around reactor
        paint.setStrokeWidth(1.5f);
        paint.setColor(applyAlpha(col, (int)(150 * alpha)));
        for (int i = 0; i < 12; i++) {
            float a = (float)Math.toRadians(i * 30 + frame * 20);
            float x1 = cx + coreR * 0.7f * (float)Math.cos(a);
            float y1 = cy + coreR * 0.7f * (float)Math.sin(a);
            float x2 = cx + coreR * 1.15f * (float)Math.cos(a);
            float y2 = cy + coreR * 1.15f * (float)Math.sin(a);
            c.drawLine(x1, y1, x2, y2, paint);
        }
        // Spoke lines
        paint.setStrokeWidth(0.5f);
        paint.setColor(applyAlpha(col, (int)(80 * alpha)));
        for (int i = 0; i < 6; i++) {
            float a = (float)Math.toRadians(i * 60 + frame * 10);
            c.drawLine(cx, cy, cx + coreR * 2.5f * (float)Math.cos(a),
                       cy + coreR * 2.5f * (float)Math.sin(a), paint);
        }
    }

    // ── SUIT WIREFRAME (simplified Iron Man silhouette) ──
    private void drawSuitWireframe(Canvas c, float alpha) {
        if (alpha <= 0.1f) return;
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(1.5f);
        int suitAlpha = (int)(35 * alpha);
        int col = hudState == 3 ? GREEN : CYAN;
        paint.setColor(applyAlpha(col, suitAlpha));
        float scale = radius * 0.35f;
        float suitCx = cx;
        float suitCy = cy - scale * 0.2f;
        float rot = (float)Math.sin(frame * 0.3) * 0.1f; // subtle 3D rotation
        // Head (circle)
        c.drawCircle(suitCx, suitCy - scale * 1.5f, scale * 0.25f, paint);
        // Eyes (glowing)
        paint.setColor(applyAlpha(col, (int)(suitAlpha * 2)));
        float eyeSpread = scale * 0.1f;
        c.drawLine(suitCx - eyeSpread - 4, suitCy - scale * 1.55f,
                   suitCx - eyeSpread + 4, suitCy - scale * 1.55f, paint);
        c.drawLine(suitCx + eyeSpread - 4, suitCy - scale * 1.55f,
                   suitCx + eyeSpread + 4, suitCy - scale * 1.55f, paint);
        // Torso
        paint.setColor(applyAlpha(col, suitAlpha));
        Path torso = new Path();
        torso.moveTo(suitCx - scale * 0.35f, suitCy - scale * 1.25f);
        torso.lineTo(suitCx - scale * 0.45f, suitCy - scale * 0.4f);
        torso.lineTo(suitCx - scale * 0.3f, suitCy + scale * 0.3f);
        torso.lineTo(suitCx - scale * 0.15f, suitCy + scale * 0.6f);
        torso.lineTo(suitCx + scale * 0.15f, suitCy + scale * 0.6f);
        torso.lineTo(suitCx + scale * 0.3f, suitCy + scale * 0.3f);
        torso.lineTo(suitCx + scale * 0.45f, suitCy - scale * 0.4f);
        torso.lineTo(suitCx + scale * 0.35f, suitCy - scale * 1.25f);
        c.drawPath(torso, paint);
        // Arms
        c.drawLine(suitCx - scale * 0.45f, suitCy - scale * 0.8f,
                   suitCx - scale * 0.7f, suitCy + scale * 0.1f, paint);
        c.drawLine(suitCx - scale * 0.7f, suitCy + scale * 0.1f,
                   suitCx - scale * 0.6f, suitCy + scale * 0.7f, paint);
        c.drawLine(suitCx + scale * 0.45f, suitCy - scale * 0.8f,
                   suitCx + scale * 0.7f, suitCy + scale * 0.1f, paint);
        c.drawLine(suitCx + scale * 0.7f, suitCy + scale * 0.1f,
                   suitCx + scale * 0.6f, suitCy + scale * 0.7f, paint);
        // Legs
        c.drawLine(suitCx - scale * 0.15f, suitCy + scale * 0.6f,
                   suitCx - scale * 0.3f, suitCy + scale * 1.5f, paint);
        c.drawLine(suitCx + scale * 0.15f, suitCy + scale * 0.6f,
                   suitCx + scale * 0.3f, suitCy + scale * 1.5f, paint);
        // Arc reactor on chest (glowing)
        paint.setColor(applyAlpha(col, (int)(suitAlpha * 2.5f)));
        c.drawCircle(suitCx, suitCy - scale * 0.6f, scale * 0.08f, paint);
    }

    // ── DATA STREAMS (vertical lines) ──
    private void drawDataStreams(Canvas c, float alpha) {
        if (alpha <= 0) return;
        paint.setColor(applyAlpha(0x00D4FF, (int)(20 * alpha)));
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(0.5f);
        for (int i = 0; i < 8; i++) {
            float x = cx + radius * 0.85f + i * 12;
            if (x > W - 20) break;
            float y1 = cy - 40 + i * 8;
            float y2 = cy + 40 - i * 8;
            c.drawLine(x, y1, x + 15, y1 + 15, paint);
            c.drawLine(x + 15, y1 + 15, x + 15, y2 - 15, paint);
        }
        for (int i = 0; i < 8; i++) {
            float x = cx - radius * 0.85f - i * 12;
            if (x < 20) break;
            float y1 = cy - 40 + i * 8;
            float y2 = cy + 40 - i * 8;
            c.drawLine(x, y1, x - 15, y1 + 15, paint);
            c.drawLine(x - 15, y1 + 15, x - 15, y2 - 15, paint);
        }
    }

    // ── PARTICLES ──
    private void drawParticles(Canvas c, float alpha) {
        paint.setStyle(Paint.Style.FILL);
        List<Particle> dead = new ArrayList<>();
        for (Particle p : particles) {
            p.update();
            if (p.life <= 0) { dead.add(p); continue; }
            int col = p.color == 0 ? CYAN : (p.color == 1 ? GREEN : PURPLE);
            paint.setColor(applyAlpha(col, (int)(255 * p.life * alpha)));
            c.drawCircle(p.x, p.y, p.size * p.life, paint);
        }
        particles.removeAll(dead);
    }

    // ── WAVEFORM ──
    private void drawWaveform(Canvas c, float alpha) {
        if (alpha <= 0) return;
        int baseY = H - 80;
        int waveW = W - 100;
        int startX = 50;
        int barW = waveW / waveform.length;
        paint.setStyle(Paint.Style.FILL);
        for (int i = 0; i < waveform.length; i++) {
            int idx = (waveIdx - waveform.length + i + waveform.length * 10) % waveform.length;
            float val = waveform[idx];
            float barH = val * 35f + 1f;
            int x = startX + i * barW;
            int col = hudState == 1 ? ORANGE : (hudState == 3 ? GREEN : CYAN);
            int a = (int)(Math.min(255, (80 + 175 * val)) * alpha);
            paint.setColor(applyAlpha(col, a));
            c.drawRect(x, baseY - barH, x + barW - 1, baseY, paint);
        }
        // Level meter
        paint.setColor(applyAlpha(0x00D4FF, (int)(50 * alpha)));
        paint.setStyle(Paint.Style.STROKE);
        c.drawRect(startX, baseY + 6, startX + waveW, baseY + 12, paint);
        int col2 = hudState == 1 ? ORANGE : GREEN;
        paint.setColor(applyAlpha(col2, (int)(180 * alpha)));
        paint.setStyle(Paint.Style.FILL);
        c.drawRect(startX, baseY + 6, startX + audioLevel * waveW, baseY + 12, paint);
        // Label
        paint.setColor(applyAlpha(0x00D4FF, (int)(60 * alpha)));
        paint.setTextSize(9f);
        paint.setTextAlign(Paint.Align.LEFT);
        c.drawText("AUDIO INPUT [RO-ROMANIAN]", (float)startX, (float)(baseY + 24), paint);
    }

    // ── CORNER INFO PANELS ──
    private void drawCornerInfo(Canvas c, float alpha) {
        if (alpha <= 0) return;
        paint.setTextSize(9f);
        int a = (int)(120 * alpha);
        // Top-left
        paint.setTextAlign(Paint.Align.LEFT);
        paint.setColor(applyAlpha(0x00D4FF, a));
        c.drawText("WHOAMISecAI JARVIS v1.0", 28f, 34f, paint);
        paint.setColor(applyAlpha(0x00D4FF, (int)(80 * alpha)));
        c.drawText("Pipeline: ALLM | Admin: MASTER", 28f, 48f, paint);
        c.drawText("Voice: RO-ROMANIAN | Autonomous: ON", 28f, 60f, paint);
        // Top-right
        paint.setTextAlign(Paint.Align.RIGHT);
        paint.setColor(applyAlpha(0x00D4FF, a));
        String[] states = {"IDLE", "ASCULT", "PROCESEZ", "RASPUND"};
        c.drawText("Stare: " + states[hudState], (float)(W - 28), 34f, paint);
        paint.setColor(applyAlpha(0x00D4FF, (int)(80 * alpha)));
        c.drawText("Frame: " + (int)frame + " | Radar: " + (int)(Math.toDegrees(radarAngle) % 360), (float)(W - 28), 48f, paint);
        c.drawText("Audio: " + (int)(audioLevel * 100) + "%", (float)(W - 28), 60f, paint);
    }

    // ── TICKER BAR (scrolling alerts) ──
    private void drawTicker(Canvas c, float alpha) {
        if (alpha <= 0) return;
        int barH = 22;
        int y = H - 28;
        // Background
        paint.setColor(applyAlpha(0x00D4FF, (int)(12 * alpha)));
        paint.setStyle(Paint.Style.FILL);
        c.drawRect(0, y, W, y + barH, paint);
        // Green LIVE dot
        paint.setColor(applyAlpha(0x00FF87, (int)(200 * alpha)));
        c.drawCircle(14, y + barH / 2, 3f, paint);
        // "SYS FEED" label
        paint.setColor(applyAlpha(0x00D4FF, (int)(120 * alpha)));
        paint.setTextSize(8f);
        paint.setTextAlign(Paint.Align.LEFT);
        c.drawText("SYS FEED", 22f, y + barH / 2f + 3f, paint);
        // Scrolling text
        paint.setColor(applyAlpha(0x00D4FF, (int)(90 * alpha)));
        float textX = 80 - (tickerOffset % (W + 400));
        for (int t = 0; t < ALERTS.length * 2; t++) {
            String alert = ALERTS[t % ALERTS.length];
            float tw = paint.measureText(alert + "   ///   ");
            if (textX + tw < 0) { textX += tw; continue; }
            if (textX > W) break;
            c.drawText(alert + "   ///   ", textX, y + barH / 2f + 3f, paint);
            textX += tw;
        }
    }

    // ── STATUS OVERLAY ──
    private void drawStatusOverlay(Canvas c, float alpha) {
        if (alpha <= 0 || statusText.isEmpty()) return;
        paint.setTextAlign(Paint.Align.CENTER);
        paint.setShadowLayer(10f, 0, 0, CYAN);
        paint.setTextSize(20f);
        paint.setColor(applyAlpha(CYAN, (int)(230 * alpha)));
        c.drawText(statusText, (float)cx, 88f, paint);
        if (!subStatusText.isEmpty()) {
            paint.setTextSize(12f);
            paint.setColor(applyAlpha(CYAN, (int)(150 * alpha)));
            c.drawText(subStatusText, (float)cx, 106f, paint);
        }
        paint.setShadowLayer(0, 0, 0, 0);
    }

    // ── STATE DOTS ──
    private void drawStateDots(Canvas c, float alpha) {
        if (alpha <= 0) return;
        int y = 116;
        int spacing = 22;
        int totalW = 3 * spacing;
        int startX = cx - totalW / 2;
        int[] colors = {CYAN, ORANGE, PURPLE, GREEN};
        for (int i = 0; i < 4; i++) {
            boolean active = (i == hudState);
            paint.setColor(applyAlpha(colors[i], active ? (int)(255 * alpha) : (int)(40 * alpha)));
            paint.setStyle(Paint.Style.FILL);
            c.drawCircle(startX + i * spacing, y, active ? 4f : 2.5f, paint);
            if (active) {
                paint.setStyle(Paint.Style.STROKE);
                paint.setStrokeWidth(1f);
                c.drawCircle(startX + i * spacing, y, 7f, paint);
            }
        }
    }

    // ── VIGNETTE ──
    private void drawVignette(Canvas c) {
        // Simple corner darkening
        int gradR = Math.max(W, H);
        for (int i = 0; i < 5; i++) {
            float r = gradR * (0.85f + i * 0.04f);
            paint.setColor(applyAlpha(0x000000, 15 - i * 3));
            paint.setStyle(Paint.Style.FILL);
            c.drawCircle(cx, cy, r, paint);
        }
    }

    // ── Helpers ──
    private static int applyAlpha(int rgb, int alpha) {
        return (Math.max(0, Math.min(255, alpha)) << 24) | (rgb & 0x00FFFFFF);
    }

    private static class Particle {
        float x, y, vx, vy, life, size;
        int color;
        Particle(float cx, float cy, Random rng) {
            x = cx; y = cy;
            double a = rng.nextDouble() * Math.PI * 2;
            float s = 1.5f + rng.nextFloat() * 4f;
            vx = (float)Math.cos(a) * s;
            vy = (float)Math.sin(a) * s;
            life = 1f;
            size = 1.5f + rng.nextFloat() * 3f;
            color = rng.nextInt(3);
        }
        void update() { x += vx; y += vy; life -= 0.018f; }
    }
}
