package com.whoamisecai.jarvis.voice

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat

/**
 * JARVIS Voice Service — Foreground service for continuous voice recognition
 *
 * Keeps the voice engine running in the background as a foreground service.
 * This ensures the microphone stays active and the app is not killed by
 * the Android system's battery optimization.
 */
class JarvisVoiceService : Service() {

    companion object {
        private const val TAG = "JarvisVoiceService"
        private const val NOTIFICATION_ID = 1001
        private const val CHANNEL_ID = "jarvis_voice_channel"
        private const val CHANNEL_NAME = "JARVIS Voice Service"
    }

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "JARVIS Voice Service created")
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification())
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(TAG, "Voice Service started")
        updateNotification("JARVIS Active — Listening")
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        Log.i(TAG, "JARVIS Voice Service destroyed")
    }

    /**
     * Create notification channel for Android O+
     */
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                CHANNEL_NAME,
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "JARVIS voice recognition service"
                setShowBadge(false)
                enableLights(false)
                enableVibration(false)
            }

            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }

    /**
     * Build the foreground notification
     */
    private fun buildNotification(statusText: String = "JARVIS Active"): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("JARVIS")
            .setContentText(statusText)
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setOngoing(true)
            .setSilent(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .build()
    }

    /**
     * Update notification text
     */
    fun updateNotification(text: String) {
        val notificationManager = getSystemService(NotificationManager::class.java)
        notificationManager.notify(NOTIFICATION_ID, buildNotification(text))
    }
}
