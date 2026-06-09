package com.whoamisecai.jarvis.hud

import android.animation.ValueAnimator
import android.content.Context
import android.graphics.*
import android.util.AttributeSet
import android.view.View
import kotlin.math.sin
import kotlin.math.cos
import kotlin.random.Random

/**
 * JARVIS Floating Particles View — Ambient background animation
 *
 * Creates floating green particles with subtle glow effect
 * for the JARVIS HUD background atmosphere.
 */
class JarvisParticlesView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    companion object {
        private const val NUM_PARTICLES = 30
        private const val PARTICLE_COLOR = Color.parseColor("#00ff41")
        private const val BG_COLOR = Color.parseColor("#0a0a0f")
    }

    private data class Particle(
        var x: Float = 0f,
        var y: Float = 0f,
        var vx: Float = 0f,
        var vy: Float = 0f,
        var size: Float = 0f,
        var alpha: Float = 0f,
        var life: Float = 0f,
        var maxLife: Float = 0f
    )

    private val particles = Array(NUM_PARTICLES) {
        Particle(
            x = Random.nextFloat(),
            y = Random.nextFloat(),
            vx = (Random.nextFloat() - 0.5f) * 0.001f,
            vy = (Random.nextFloat() - 0.5f) * 0.001f,
            size = Random.nextFloat() * 3f + 1f,
            alpha = Random.nextFloat() * 0.5f + 0.1f,
            life = Random.nextFloat(),
            maxLife = Random.nextFloat() * 0.5f + 0.5f
        )
    }

    private val bgPaint = Paint().apply { color = BG_COLOR }
    private val particlePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = PARTICLE_COLOR
        maskFilter = BlurMaskFilter(4f, BlurMaskFilter.Blur.NORMAL)
    }

    private val linePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(20, 0, 255, 65)
        strokeWidth = 1f
    }

    private var animator: ValueAnimator? = null

    init {
        setLayerType(LAYER_TYPE_SOFTWARE, null)
        startAnimation()
    }

    private fun startAnimation() {
        animator = ValueAnimator.ofFloat(0f, 1f).apply {
            duration = 32  // ~30fps
            repeatCount = ValueAnimator.INFINITE
            addUpdateListener {
                updateParticles()
                invalidate()
            }
            start()
        }
    }

    private fun updateParticles() {
        val w = width.toFloat()
        val h = height.toFloat()
        if (w == 0f || h == 0f) return

        for (p in particles) {
            // Move
            p.x += p.vx
            p.y += p.vy

            // Life cycle
            p.life += 0.005f
            if (p.life > p.maxLife) {
                p.life = 0f
                p.x = Random.nextFloat()
                p.y = Random.nextFloat()
                p.vx = (Random.nextFloat() - 0.5f) * 0.001f
                p.vy = (Random.nextFloat() - 0.5f) * 0.001f
            }

            // Alpha based on life
            val lifeRatio = p.life / p.maxLife
            p.alpha = when {
                lifeRatio < 0.1f -> lifeRatio * 10f * 0.4f
                lifeRatio > 0.8f -> (1f - lifeRatio) * 5f * 0.4f
                else -> 0.3f + sin(p.life * 10f) * 0.1f
            }

            // Wrap around edges
            if (p.x < -0.05f) p.x = 1.05f
            if (p.x > 1.05f) p.x = -0.05f
            if (p.y < -0.05f) p.y = 1.05f
            if (p.y > 1.05f) p.y = -0.05f
        }
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        val w = width.toFloat()
        val h = height.toFloat()
        if (w == 0f || h == 0f) return

        // Draw connection lines between close particles
        for (i in particles.indices) {
            for (j in i + 1 until particles.size) {
                val dx = (particles[i].x - particles[j].x) * w
                val dy = (particles[i].y - particles[j].y) * h
                val dist = Math.sqrt((dx * dx + dy * dy).toDouble()).toFloat()

                if (dist < 100f) {
                    val alpha = ((1f - dist / 100f) * 0.3f).toInt().coerceIn(0, 255)
                    linePaint.color = Color.argb(alpha, 0, 255, 65)
                    canvas.drawLine(
                        particles[i].x * w, particles[i].y * h,
                        particles[j].x * w, particles[j].y * h,
                        linePaint
                    )
                }
            }
        }

        // Draw particles
        for (p in particles) {
            val px = p.x * w
            val py = p.y * h
            val alpha = (p.alpha * 255).toInt().coerceIn(0, 255)
            particlePaint.color = Color.argb(alpha, 0, 255, 65)
            canvas.drawCircle(px, py, p.size, particlePaint)
        }
    }

    override fun onDetachedFromWindow() {
        super.onDetachedFromWindow()
        animator?.cancel()
    }
}
