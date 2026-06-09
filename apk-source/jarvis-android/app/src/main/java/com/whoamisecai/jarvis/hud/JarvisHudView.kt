package com.whoamisecai.jarvis.hud

import android.animation.ValueAnimator
import android.content.Context
import android.graphics.*
import android.util.AttributeSet
import android.view.View
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * JARVIS HUD View — Circular audio level indicator with arc reactor style
 *
 * Visual elements:
 * - Outer ring with glow effect (reacts to audio level)
 * - Inner rotating arc (scanning animation)
 * - Center text/icon
 * - Audio level waveform bars around the ring
 * - Particle effects when speaking
 */
class JarvisHudView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    companion object {
        private const val RING_COLOR = Color.parseColor("#00ff41")
        private const val RING_DIM_COLOR = Color.parseColor("#1a3a1a")
        private const val BG_COLOR = Color.parseColor("#0a0a0f")
        private const val ERROR_COLOR = Color.parseColor("#ff4444")
        private const val PROCESSING_COLOR = Color.parseColor("#06b6d4")
        private const val NUM_BARS = 64
        private const val ROTATION_SPEED = 2f  // degrees per frame
    }

    // Audio level (0.0 to 1.0)
    var audioLevel: Float = 0f
        set(value) {
            field = value.coerceIn(0f, 1f)
            invalidate()
        }

    // State
    enum class HudState {
        IDLE, LISTENING, PROCESSING, SPEAKING, ERROR, FALLBACK
    }

    var hudState: HudState = HudState.IDLE
        set(value) {
            field = value
            stateColor = when (value) {
                HudState.IDLE -> RING_DIM_COLOR
                HudState.LISTENING -> RING_COLOR
                HudState.PROCESSING -> PROCESSING_COLOR
                HudState.SPEAKING -> RING_COLOR
                HudState.ERROR -> ERROR_COLOR
                HudState.FALLBACK -> Color.parseColor("#ffaa00")
            }
            invalidate()
        }

    private var stateColor: Int = RING_DIM_COLOR

    // Animation
    private var rotationAngle = 0f
    private var pulsePhase = 0f
    private val barLevels = FloatArray(NUM_BARS) { 0f }

    // Paints
    private val ringPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 3f
        color = RING_COLOR
    }

    private val glowPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 8f
        maskFilter = BlurMaskFilter(15f, BlurMaskFilter.Blur.OUTER)
        color = RING_COLOR
    }

    private val innerRingPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 2f
        color = RING_DIM_COLOR
    }

    private val barPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
        color = RING_COLOR
    }

    private val centerPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        textSize = 14f
        typeface = Typeface.MONOSPACE
        textAlign = Paint.Align.CENTER
    }

    private val bgPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = BG_COLOR
    }

    // Scanning arc paint
    private val scanPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 2f
        color = RING_COLOR
    }

    private val scanGlowPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 6f
        maskFilter = BlurMaskFilter(8f, BlurMaskFilter.Blur.OUTER)
        color = RING_COLOR
    }

    // Animator
    private var animator: ValueAnimator? = null

    init {
        setLayerType(LAYER_TYPE_SOFTWARE, null) // Needed for BlurMaskFilter
        startAnimation()
    }

    private fun startAnimation() {
        animator = ValueAnimator.ofFloat(0f, 360f).apply {
            duration = 8000
            repeatCount = ValueAnimator.INFINITE
            addUpdateListener {
                rotationAngle = it.animatedValue as Float
                pulsePhase = (System.currentTimeMillis() % 3000) / 3000f * (2 * Math.PI).toFloat()
                updateBarLevels()
                invalidate()
            }
            start()
        }
    }

    /**
     * Generate audio visualization bars with some organic movement
     */
    private fun updateBarLevels() {
        for (i in barLevels.indices) {
            val baseLevel = audioLevel
            val waveOffset = sin((i / NUM_BARS.toFloat() * Math.PI * 4) + pulsePhase).toFloat()
            val noise = (Math.random() * 0.1f - 0.05f)
            val target = when (hudState) {
                HudState.IDLE -> (0.05f + waveOffset * 0.03f).coerceIn(0f, 1f)
                HudState.LISTENING -> (baseLevel * 0.8f + waveOffset * 0.15f + noise).coerceIn(0f, 1f)
                HudState.PROCESSING -> {
                    val processingWave = sin(System.currentTimeMillis() / 200f + i * 0.3f).toFloat()
                    (0.3f + processingWave * 0.2f).coerceIn(0f, 1f)
                }
                HudState.SPEAKING -> {
                    val speakWave = sin(System.currentTimeMillis() / 150f + i * 0.5f).toFloat()
                    (0.2f + speakWave * 0.3f + baseLevel * 0.2f).coerceIn(0f, 1f)
                }
                HudState.ERROR -> {
                    val errorFlash = if (Math.random() > 0.7f) 0.8f else 0.1f
                    errorFlash
                }
                HudState.FALLBACK -> {
                    val fallbackWave = sin(System.currentTimeMillis() / 300f + i * 0.4f).toFloat()
                    (0.15f + fallbackWave * 0.15f + baseLevel * 0.4f).coerceIn(0f, 1f)
                }
            }
            // Smooth transition
            barLevels[i] = barLevels[i] * 0.7f + target * 0.3f
        }
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        val cx = width / 2f
        val cy = height / 2f
        val outerRadius = (minOf(width, height) / 2f - 20f)
        val innerRadius = outerRadius * 0.7f
        val barStartRadius = outerRadius * 0.75f
        val barMaxHeight = outerRadius * 0.22f

        // Background circle
        canvas.drawCircle(cx, cy, outerRadius + 10, bgPaint)

        // Draw waveform bars around the ring
        for (i in 0 until NUM_BARS) {
            val angle = (i / NUM_BARS.toFloat() * 360f) - 90f
            val rad = Math.toRadians(angle.toDouble())

            val x1 = cx + (barStartRadius * cos(rad)).toFloat()
            val y1 = cy + (barStartRadius * sin(rad)).toFloat()

            val barHeight = barLevels[i] * barMaxHeight
            val x2 = cx + ((barStartRadius + barHeight) * cos(rad)).toFloat()
            val y2 = cy + ((barStartRadius + barHeight) * sin(rad)).toFloat()

            barPaint.color = if (barLevels[i] > 0.5f) stateColor else {
                val alpha = (barLevels[i] * 2 * 255).toInt()
                Color.argb(alpha.coerceIn(0, 255),
                    Color.red(stateColor),
                    Color.green(stateColor),
                    Color.blue(stateColor))
            }

            canvas.drawLine(x1, y1, x2, y2, barPaint)
        }

        // Outer ring
        ringPaint.color = stateColor
        ringPaint.alpha = if (hudState == HudState.IDLE) 60 else 200
        canvas.drawCircle(cx, cy, outerRadius, ringPaint)

        // Glow on outer ring (only when active)
        if (hudState != HudState.IDLE) {
            glowPaint.color = stateColor
            glowPaint.alpha = (audioLevel * 150 + 30).toInt().coerceIn(0, 255)
            canvas.drawCircle(cx, cy, outerRadius, glowPaint)
        }

        // Inner ring
        innerRingPaint.color = stateColor
        innerRingPaint.alpha = 100
        canvas.drawCircle(cx, cy, innerRadius, innerRingPaint)

        // Scanning arc (rotates continuously)
        if (hudState == HudState.LISTENING || hudState == HudState.FALLBACK) {
            val scanAngle = rotationAngle
            val arcRect = RectF(
                cx - innerRadius, cy - innerRadius,
                cx + innerRadius, cy + innerRadius
            )

            scanPaint.color = stateColor
            scanGlowPaint.color = stateColor

            canvas.drawArc(arcRect, scanAngle, 60f, false, scanPaint)
            canvas.drawArc(arcRect, scanAngle, 60f, false, scanGlowPaint)

            // Opposite arc
            canvas.drawArc(arcRect, scanAngle + 180f, 40f, false, scanPaint)
        }

        // Processing spinning segments
        if (hudState == HudState.PROCESSING) {
            val arcRect = RectF(
                cx - innerRadius * 0.9f, cy - innerRadius * 0.9f,
                cx + innerRadius * 0.9f, cy + innerRadius * 0.9f
            )

            scanPaint.color = PROCESSING_COLOR
            scanGlowPaint.color = PROCESSING_COLOR

            for (j in 0 until 3) {
                val angle = rotationAngle * 2f + j * 120f
                canvas.drawArc(arcRect, angle, 30f, false, scanPaint)
            }
        }

        // Center text
        val centerText = when (hudState) {
            HudState.IDLE -> "JARVIS"
            HudState.LISTENING -> if (audioLevel > 0.1f) "●" else "○"
            HudState.PROCESSING -> "◎"
            HudState.SPEAKING -> "◆"
            HudState.ERROR -> "⚠"
            HudState.FALLBACK -> "◈"
        }

        centerPaint.color = stateColor
        centerPaint.textSize = when (hudState) {
            HudState.IDLE -> 24f
            else -> 32f
        }

        val textY = cy - (centerPaint.descent() + centerPaint.ascent()) / 2
        canvas.drawText(centerText, cx, textY, centerPaint)

        // Status label below center
        if (hudState != HudState.IDLE) {
            centerPaint.textSize = 10f
            centerPaint.color = Color.argb(150,
                Color.red(stateColor),
                Color.green(stateColor),
                Color.blue(stateColor))
            val statusLabel = hudState.name
            canvas.drawText(statusLabel, cx, cy + 25, centerPaint)
        }

        // Pulse effect on idle
        if (hudState == HudState.IDLE) {
            val pulseRadius = outerRadius * (1.0f + sin(pulsePhase) * 0.02f)
            ringPaint.alpha = (30 + sin(pulsePhase) * 20).toInt().coerceIn(0, 255)
            canvas.drawCircle(cx, cy, pulseRadius, ringPaint)
        }
    }

    override fun onDetachedFromWindow() {
        super.onDetachedFromWindow()
        animator?.cancel()
    }

    /**
     * Get diagnostics info
     */
    fun getDiagnostics(): String {
        return "HudView: state=$hudState, audioLevel=${"%.2f".format(audioLevel)}, " +
                "bars=${barLevels.take(5).map { "%.2f".format(it) }}"
    }
}
