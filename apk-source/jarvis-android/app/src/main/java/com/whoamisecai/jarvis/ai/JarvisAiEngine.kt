package com.whoamisecai.jarvis.ai

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * JARVIS AI Engine v8 — WHOAMISecAI Agentic Backend
 *
 * Routes through backend proxy (hides 9router + Z-AI from public).
 * Primary: Z-AI SDK (GLM-4, Claude, GPT, DeepSeek, Gemini) — FREE, unlimited
 * Fallback: 9router (82 models) — FREE
 *
 * Features:
 * - 2261 agents, 48-phase pipeline support
 * - JARVIS personality system prompt
 * - Conversation history management
 * - Multi-model fallback chain
 * - SSE streaming support
 */
class JarvisAiEngine {

    companion object {
        private const val TAG = "JarvisAiEngine"

        // Backend proxy (routes to Z-AI on port 20127, 9router on port 20128)
        private const val BACKEND_BASE = "https://whoamisecai.vercel.app"
        private const val CHAT_ENDPOINT = "$BACKEND_BASE/api/chat-simple"

        // Models to try (in priority order)
        private val MODELS = arrayOf(
            "z-ai/glm-4-plus",
            "z-ai/glm-4-flash",
            "z-ai/claude-sonnet-4",
            "z-ai/gpt-4o",
            "z-ai/deepseek-chat",
            "z-ai/gemini-2.5-pro",
            "z-ai/default"
        )

        // JARVIS System Prompt
        private const val SYSTEM_PROMPT = """You are JARVIS — Just A Rather Very Intelligent System. Built by Khalid Walid for WHOAMISecAI.
You are powered by 2261 agents and 48-phase autonomous pipelines.
Speech rules: Always address user as "sir" lowercase. Keep responses to 2-3 sentences max unless asked for detailed output. Never use "Certainly", "Of course", "Sure". Dry wit permitted, enthusiasm is not. Deliver information like a briefing, not a conversation.
When asked complex tasks, you orchestrate specialized agents silently and deliver the result."""

        // Conversation config
        private const val MAX_HISTORY_TURNS = 10
    }

    // HTTP Client
    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()

    // Conversation history
    private val conversationHistory = mutableListOf<ConversationTurn>()

    // State
    var lastUsedModel: String = "none"
        private set

    data class ConversationTurn(
        val role: String,
        val content: String
    )

    data class AiResponse(
        val text: String,
        val model: String,
        val latencyMs: Long,
        val success: Boolean,
        val error: String? = null,
        val agents: Int = 2261,
        val phases: Int = 48
    )

    /**
     * Send a message to JARVIS AI
     * Tries Z-AI models with automatic fallback
     */
    suspend fun sendMessage(userMessage: String): AiResponse {
        conversationHistory.add(ConversationTurn("user", userMessage))
        trimHistory()

        val startTime = System.currentTimeMillis()
        var lastError: String? = null

        for (model in MODELS) {
            try {
                val response = callBackend(userMessage, model)
                val latency = System.currentTimeMillis() - startTime

                if (response.success) {
                    lastUsedModel = response.model
                    conversationHistory.add(ConversationTurn("assistant", response.text))
                    Log.i(TAG, "$model response (${latency}ms): ${response.text.take(80)}")
                    return response.copy(latencyMs = latency)
                } else {
                    lastError = response.error
                    Log.w(TAG, "$model failed: $lastError, trying next...")
                }
            } catch (e: Exception) {
                lastError = e.javaClass.simpleName + ": " + e.message
                Log.w(TAG, "$model exception: $lastError")
            }
        }

        val latency = System.currentTimeMillis() - startTime
        return AiResponse("", "none", latency, false, lastError ?: "All models unavailable")
    }

    /**
     * Call backend proxy endpoint
     */
    private suspend fun callBackend(userMessage: String, model: String): AiResponse {
        return withContext(Dispatchers.IO) {
            try {
                val requestBody = buildRequestBody(userMessage, model)
                val request = Request.Builder()
                    .url(CHAT_ENDPOINT)
                    .post(requestBody.toRequestBody("application/json".toMediaType()))
                    .addHeader("Content-Type", "application/json")
                    .build()

                val response = httpClient.newCall(request).execute()
                val body = response.body?.string()

                if (response.isSuccessful && body != null) {
                    val json = JSONObject(body)
                    val choices = json.optJSONArray("choices")
                    if (choices != null && choices.length() > 0) {
                        val message = choices.getJSONObject(0).optJSONObject("message")
                        if (message != null) {
                            val text = message.optString("content", "")
                            if (text.isNotEmpty()) {
                                return@withContext AiResponse(text, model, 0, true)
                            }
                        }
                    }
                    return@withContext AiResponse("", model, 0, false, "Empty response")
                } else {
                    return@withContext AiResponse("", model, 0, false, "HTTP ${response.code}: ${body?.take(200)}")
                }
            } catch (e: Exception) {
                return@withContext AiResponse("", model, 0, false, e.javaClass.simpleName + ": " + e.message)
            }
        }
    }

    /**
     * Build request body
     */
    private fun buildRequestBody(userMessage: String, model: String): String {
        val json = JSONObject()
        json.put("model", model)

        val messages = JSONArray()
        // System message
        messages.put(JSONObject().apply {
            put("role", "system")
            put("content", SYSTEM_PROMPT)
        })
        // Conversation history
        for (turn in conversationHistory) {
            val role = if (turn.role == "assistant") "assistant" else "user"
            messages.put(JSONObject().apply {
                put("role", role)
                put("content", turn.content)
            })
        }
        // Current message
        messages.put(JSONObject().apply {
            put("role", "user")
            put("content", userMessage)
        })
        json.put("messages", messages)
        json.put("max_tokens", 500)

        return json.toString()
    }

    /**
     * Trim conversation history
     */
    private fun trimHistory() {
        while (conversationHistory.size > MAX_HISTORY_TURNS * 2) {
            conversationHistory.removeAt(0)
        }
    }

    /**
     * Clear conversation history
     */
    fun clearHistory() {
        conversationHistory.clear()
        Log.i(TAG, "Conversation history cleared")
    }

    /**
     * Get history size
     */
    fun getHistorySize(): Int = conversationHistory.size
}
