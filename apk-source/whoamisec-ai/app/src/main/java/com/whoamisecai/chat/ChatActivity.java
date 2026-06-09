package com.whoamisecai.chat;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.TextUtils;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.whoamisecai.R;
import com.whoamisecai.adapters.ChatMessageAdapter;
import com.whoamisecai.adapters.ModelSelectorAdapter;
import com.whoamisecai.api.AiClient;
import com.whoamisecai.models.AiModel;
import com.whoamisecai.models.ChatMessage;

import java.util.ArrayList;
import java.util.List;

/**
 * WHOAMISecAI ChatActivity — Full AI Chat with 80+ Model Selector
 *
 * Features:
 *  - Chat interface with streaming responses
 *  - Model selector dialog (80+ models)
 *  - Pipeline mode selector (LLM/MLM/ALLM)
 *  - Chat history
 *  - Copy message
 */
public class ChatActivity extends Activity {

    private static final String TAG = "ChatActivity";
    private static final String PREFS_NAME = "whoamisecai_prefs";
    private static final String KEY_ADMIN = "admin_key";
    private static final String KEY_MODEL = "selected_model";
    private static final String KEY_PIPELINE = "pipeline_mode";

    private Handler mainHandler;
    private SharedPreferences prefs;
    private AiClient aiClient;

    // ── UI ──
    private RecyclerView chatRecyclerView;
    private EditText chatInput;
    private Button sendBtn;
    private TextView modelLabel;
    private Spinner pipelineSelector;
    private LinearLayout modelSelectorContainer;
    private RecyclerView modelRecyclerView;
    private TextView selectedModelName;
    private LinearLayout modelSelectorHeader;

    // ── Data ──
    private List<ChatMessage> messages;
    private ChatMessageAdapter chatAdapter;
    private List<AiModel> allModels;
    private String currentModel = "openai/gpt-4o";
    private boolean isLoading = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_chat_new);

        mainHandler = new Handler(Looper.getMainLooper());
        prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        aiClient = new AiClient("https://whoamisecai.vercel.app", prefs.getString(KEY_ADMIN,
            "wsec_4ead532b0d0b02c7eab1791978d7d4ac"));
        currentModel = prefs.getString(KEY_MODEL, "openai/gpt-4o");

        initViews();
        initChat();
        initModels();
        initListeners();
    }

    private void initViews() {
        chatRecyclerView = findViewById(R.id.chat_recycler);
        chatInput = findViewById(R.id.chat_input);
        sendBtn = findViewById(R.id.chat_send);
        modelLabel = findViewById(R.id.chat_model_label);
        pipelineSelector = findViewById(R.id.pipeline_selector);
        modelSelectorContainer = findViewById(R.id.model_selector_container);
        modelRecyclerView = findViewById(R.id.model_recycler);
        selectedModelName = findViewById(R.id.selected_model_name);
        modelSelectorHeader = findViewById(R.id.model_selector_header);

        modelLabel.setText(getModelDisplayName(currentModel));
    }

    private String getModelDisplayName(String modelId) {
        if (modelId == null) return "GPT-4o";
        String[] parts = modelId.split("/");
        return parts.length > 1 ? parts[parts.length - 1] : modelId;
    }

    private void initChat() {
        messages = new ArrayList<>();
        chatRecyclerView.setLayoutManager(new LinearLayoutManager(this));
        chatAdapter = new ChatMessageAdapter(this, messages);
        chatRecyclerView.setAdapter(chatAdapter);
    }

    private void initModels() {
        allModels = AiModel.getAllModels();
        modelRecyclerView.setLayoutManager(new LinearLayoutManager(this));
        ModelSelectorAdapter adapter = new ModelSelectorAdapter(this, allModels, currentModel,
            model -> {
                currentModel = model.getId();
                prefs.edit().putString(KEY_MODEL, model.getId()).apply();
                modelLabel.setText(model.getName());
                selectedModelName.setText(model.getName());
                modelSelectorContainer.setVisibility(View.GONE);
                Toast.makeText(this, "Model: " + model.getName(), Toast.LENGTH_SHORT).show();
            });
        modelRecyclerView.setAdapter(adapter);
    }

    private void initListeners() {
        sendBtn.setOnClickListener(v -> sendMessage());

        chatInput.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEND) {
                sendMessage();
                return true;
            }
            return false;
        });

        modelLabel.setOnClickListener(v -> {
            if (modelSelectorContainer.getVisibility() == View.VISIBLE) {
                modelSelectorContainer.setVisibility(View.GONE);
            } else {
                selectedModelName.setText(modelLabel.getText());
                modelSelectorContainer.setVisibility(View.VISIBLE);
            }
        });

        modelSelectorHeader.setOnClickListener(v -> {
            modelSelectorContainer.setVisibility(View.GONE);
        });
    }

    private void sendMessage() {
        String text = chatInput.getText().toString().trim();
        if (TextUtils.isEmpty(text) || isLoading) return;

        isLoading = true;
        chatInput.setText("");
        sendBtn.setEnabled(false);
        sendBtn.setBackgroundColor(Color.parseColor("#444455"));

        // Add user message
        messages.add(new ChatMessage(ChatMessage.Role.USER, text));
        chatAdapter.notifyItemInserted(messages.size() - 1);
        scrollToBottom();

        // Get pipeline mode
        String[] modeValues = getResources().getStringArray(R.array.pipeline_mode_values);
        int pos = pipelineSelector.getSelectedItemPosition();
        String pipelineMode = pos < modeValues.length ? modeValues[pos] : "llm";

        // Route based on pipeline mode
        if ("llm".equals(pipelineMode)) {
            // Direct chat completion
            aiClient.chatCompletion(text, currentModel, new AiClient.ChatCallback() {
                @Override public void onToken(String token) {
                    appendOrAddAssistant(token);
                }
                @Override public void onComplete(String fullResponse) {
                    finishResponse();
                }
                @Override public void onError(String error) {
                    messages.add(new ChatMessage(ChatMessage.Role.ASSISTANT, "❌ " + error));
                    chatAdapter.notifyDataSetChanged();
                    finishResponse();
                }
                @Override public void onPhase(String phase, String model, String status) {}
            });
        } else {
            // MLM / ALLM via /api/chat-agent
            aiClient.chat(text, currentModel, pipelineMode, new AiClient.ChatCallback() {
                @Override public void onToken(String token) {
                    appendOrAddAssistant(token);
                }
                @Override public void onComplete(String fullResponse) {
                    finishResponse();
                }
                @Override public void onError(String error) {
                    messages.add(new ChatMessage(ChatMessage.Role.ASSISTANT, "❌ " + error));
                    chatAdapter.notifyDataSetChanged();
                    finishResponse();
                }
                @Override public void onPhase(String phase, String model, String status) {}
            });
        }
    }

    private void appendOrAddAssistant(String token) {
        if (messages.isEmpty() || messages.get(messages.size() - 1).getRole() != ChatMessage.Role.ASSISTANT) {
            messages.add(new ChatMessage(ChatMessage.Role.ASSISTANT, token));
            chatAdapter.notifyItemInserted(messages.size() - 1);
        } else {
            ChatMessage last = messages.get(messages.size() - 1);
            String updated = last.getContent() + token;
            messages.set(messages.size() - 1, new ChatMessage(ChatMessage.Role.ASSISTANT, updated));
            chatAdapter.notifyItemChanged(messages.size() - 1);
        }
        scrollToBottom();
    }

    private void finishResponse() {
        isLoading = false;
        sendBtn.setEnabled(true);
        sendBtn.setBackgroundColor(Color.parseColor("#8b5cf6"));
        scrollToBottom();
    }

    private void scrollToBottom() {
        chatRecyclerView.post(() -> {
            int count = chatAdapter.getItemCount();
            if (count > 0) {
                chatRecyclerView.smoothScrollToPosition(count - 1);
            }
        });
    }
}
