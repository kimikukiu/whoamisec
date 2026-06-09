package com.whoamisecai.builder;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
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
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.recyclerview.widget.GridLayoutManager;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.whoamisecai.R;
import com.whoamisecai.adapters.AgentPanelAdapter;
import com.whoamisecai.adapters.ChatMessageAdapter;
import com.whoamisecai.api.AiClient;
import com.whoamisecai.models.Agent;
import com.whoamisecai.models.ChatMessage;
import com.whoamisecai.models.PipelinePhase;

import org.json.JSONArray;

import java.util.ArrayList;
import java.util.List;

/**
 * WHOAMISecAI BuilderActivity — Full 28-Phase Pipeline UI
 *
 * Features:
 *  - 28-phase horizontal progress bar with colored indicators
 *  - Agent panel showing all 11 Mission Control agents
 *  - Real-time terminal log
 *  - Chat messages for build interaction
 *  - Builder input + send
 *  - Stop/clear controls
 */
public class BuilderActivity extends Activity {

    private static final String TAG = "BuilderActivity";
    private static final String PREFS_NAME = "whoamisecai_prefs";
    private static final String KEY_ADMIN = "admin_key";
    private static final String KEY_MODEL = "selected_model";

    private Handler mainHandler;
    private SharedPreferences prefs;
    private AiClient aiClient;

    // ── UI ──
    private EditText builderInput;
    private LinearLayout phaseBarContainer;
    private TextView phaseLabel, phaseProgress, phaseAgentLabel;
    private ProgressBar overallProgress;
    private RecyclerView agentRecyclerView;
    private RecyclerView chatRecyclerView;
    private ScrollView terminalScroll;
    private LinearLayout terminalContainer;
    private Button sendBtn, stopBtn, clearBtn;
    private View agentPanelToggle;
    private LinearLayout agentPanelContainer;
    private TextView elapsedTime;

    // ── Data ──
    private PipelinePhase[] phases;
    private Agent[] agents;
    private List<ChatMessage> chatMessages;
    private ChatMessageAdapter chatAdapter;
    private boolean isBuilding = false;
    private long buildStartTime = 0;
    private Handler timerHandler;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_builder);

        mainHandler = new Handler(Looper.getMainLooper());
        prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        aiClient = new AiClient("https://whoamisecai.vercel.app", prefs.getString(KEY_ADMIN,
            "wsec_4ead532b0d0b02c7eab1791978d7d4ac"));

        initViews();
        initPhases();
        initAgents();
        initChat();
        initListeners();
    }

    private void initViews() {
        builderInput = findViewById(R.id.builder_input);
        phaseBarContainer = findViewById(R.id.phase_bar_container);
        phaseLabel = findViewById(R.id.phase_label);
        phaseProgress = findViewById(R.id.phase_progress);
        phaseAgentLabel = findViewById(R.id.phase_agent_label);
        overallProgress = findViewById(R.id.overall_progress);
        agentRecyclerView = findViewById(R.id.agent_recycler);
        chatRecyclerView = findViewById(R.id.builder_chat_recycler);
        terminalScroll = findViewById(R.id.terminal_scroll);
        terminalContainer = findViewById(R.id.terminal_container);
        sendBtn = findViewById(R.id.builder_send);
        stopBtn = findViewById(R.id.builder_stop);
        clearBtn = findViewById(R.id.builder_clear);
        agentPanelToggle = findViewById(R.id.agent_panel_toggle);
        agentPanelContainer = findViewById(R.id.agent_panel_container);
        elapsedTime = findViewById(R.id.elapsed_time);
    }

    private void initPhases() {
        phases = PipelinePhase.createAll();
        buildPhaseBar();
    }

    private void buildPhaseBar() {
        phaseBarContainer.removeAllViews();
        LayoutInflater inflater = LayoutInflater.from(this);

        for (PipelinePhase phase : phases) {
            View phaseView = inflater.inflate(R.layout.item_phase_dot, phaseBarContainer, false);
            FrameLayout dot = phaseView.findViewById(R.id.phase_dot);
            TextView num = phaseView.findViewById(R.id.phase_num);

            num.setText(String.valueOf(phase.getNumber()));

            int bgColor;
            switch (phase.getStatus()) {
                case RUNNING: bgColor = Color.parseColor("#f59e0b"); break;
                case DONE: bgColor = Color.parseColor("#10b981"); break;
                case ERROR: bgColor = Color.parseColor("#ef4444"); break;
                default: bgColor = Color.parseColor("#1a1a2e"); break;
            }
            dot.setBackgroundColor(bgColor);

            phaseView.setTag(phase);
            phaseBarContainer.addView(phaseView);
        }
    }

    private void updatePhaseBar() {
        for (int i = 0; i < phaseBarContainer.getChildCount(); i++) {
            View phaseView = phaseBarContainer.getChildAt(i);
            Object tag = phaseView.getTag();
            if (tag instanceof PipelinePhase) {
                PipelinePhase phase = (PipelinePhase) tag;
                FrameLayout dot = phaseView.findViewById(R.id.phase_dot);

                int bgColor;
                switch (phase.getStatus()) {
                    case RUNNING: bgColor = Color.parseColor("#f59e0b"); break;
                    case DONE: bgColor = Color.parseColor("#10b981"); break;
                    case ERROR: bgColor = Color.parseColor("#ef4444"); break;
                    default: bgColor = Color.parseColor("#1a1a2e"); break;
                }
                dot.setBackgroundColor(bgColor);
            }
        }
    }

    private void initAgents() {
        agents = Agent.createAll();
        agentRecyclerView.setLayoutManager(new GridLayoutManager(this, 2));
        AgentPanelAdapter adapter = new AgentPanelAdapter(this, agents);
        agentRecyclerView.setAdapter(adapter);
    }

    private void initChat() {
        chatMessages = new ArrayList<>();
        chatRecyclerView.setLayoutManager(new LinearLayoutManager(this));
        chatAdapter = new ChatMessageAdapter(this, chatMessages);
        chatRecyclerView.setAdapter(chatAdapter);
    }

    private void initListeners() {
        sendBtn.setOnClickListener(v -> sendBuildRequest());

        builderInput.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEND) {
                sendBuildRequest();
                return true;
            }
            return false;
        });

        stopBtn.setOnClickListener(v -> {
            isBuilding = false;
            stopBtn.setVisibility(View.GONE);
            sendBtn.setVisibility(View.VISIBLE);
            if (timerHandler != null) timerHandler.removeCallbacksAndMessages(null);
            appendTerminal("info", "⏹ Build stopped by user");
        });

        clearBtn.setOnClickListener(v -> {
            chatMessages.clear();
            chatAdapter.notifyDataSetChanged();
            terminalContainer.removeAllViews();
            resetAllPhases();
            resetAllAgents();
            phaseLabel.setText("IDLE");
            phaseProgress.setText("");
            phaseAgentLabel.setText("");
            overallProgress.setProgress(0);
            elapsedTime.setText("00:00");
        });

        agentPanelToggle.setOnClickListener(v -> {
            if (agentPanelContainer.getVisibility() == View.VISIBLE) {
                agentPanelContainer.setVisibility(View.GONE);
            } else {
                agentPanelContainer.setVisibility(View.VISIBLE);
            }
        });
    }

    private void sendBuildRequest() {
        String prompt = builderInput.getText().toString().trim();
        if (TextUtils.isEmpty(prompt)) return;
        if (isBuilding) return;

        isBuilding = true;
        buildStartTime = System.currentTimeMillis();
        sendBtn.setVisibility(View.GONE);
        stopBtn.setVisibility(View.VISIBLE);
        builderInput.setText("");

        // Add user message to chat
        chatMessages.add(new ChatMessage(ChatMessage.Role.USER, prompt));
        chatAdapter.notifyItemInserted(chatMessages.size() - 1);

        // Reset phases
        resetAllPhases();
        resetAllAgents();

        // Start timer
        startTimer();

        appendTerminal("command", "$ whoamisec-ide init \"" + prompt.substring(0, 30) + "\" --type project");
        appendTerminal("system", "● 28-Phase Neural Pipeline starting...");

        // Get selected model
        String model = prefs.getString(KEY_MODEL, "mistral-large-latest");

        // Call builder pipeline
        aiClient.buildProject(prompt, model, new JSONArray(),
            "android-build-" + System.currentTimeMillis(),
            "sb_" + System.currentTimeMillis(),
            new AiClient.BuilderCallback() {
                @Override
                public void onPhaseChange(String phase, int progress, String agent) {
                    setPhaseActive(phase);
                    overallProgress.setProgress(progress);
                    phaseLabel.setText(phase.toUpperCase());
                    phaseProgress.setText(progress + "%");
                    setAgentActive(agent);
                    appendTerminal("claude", "▶ Phase: " + phase.toUpperCase() + " (" + progress + "%)");
                }

                @Override
                public void onThinking(String message) {
                    phaseAgentLabel.setText(message);
                    appendTerminal("claude", "💬 " + message);
                }

                @Override
                public void onPlan(String plan) {
                    appendTerminal("claude", "📋 Plan generated");
                }

                @Override
                public void onFileGenerated(int index, int total, String name) {
                    appendTerminal("claude", "📄 File " + (index + 1) + "/" + total + ": " + name);
                }

                @Override
                public void onCodeStream(String filesJson) {
                    appendTerminal("claude", "✅ Code generation complete");
                }

                @Override
                public void onTerminalLine(String text, String type) {
                    appendTerminal(type, text);
                }

                @Override
                public void onTestResult(boolean passed, String output) {
                    if (passed) {
                        appendTerminal("claude", "✅ Tests PASSED");
                    } else {
                        appendTerminal("claude", "❌ Tests FAILED — initiating self-repair...");
                    }
                }

                @Override
                public void onRepair(int attempt, int max, String issue) {
                    appendTerminal("claude", "🔧 Self-repair " + attempt + "/" + max + ": " + issue);
                }

                @Override
                public void onQualityReview(int score, int suggestions) {
                    appendTerminal("claude", "📊 Quality: " + score + "/100 (" + suggestions + " suggestions)");
                }

                @Override
                public void onSecurityAudit(String severity, int vulns) {
                    appendTerminal("claude", "🛡️ Security: " + severity.toUpperCase() + " (" + vulns + " findings)");
                }

                @Override
                public void onDelivery(String summary, String repoUrl) {
                    isBuilding = false;
                    sendBtn.setVisibility(View.VISIBLE);
                    stopBtn.setVisibility(View.GONE);
                    overallProgress.setProgress(100);
                    phaseLabel.setText("DELIVERED");
                    if (timerHandler != null) timerHandler.removeCallbacksAndMessages(null);

                    markAllPhasesDone();
                    markAllAgentsDone();

                    String msg = "✅ BUILD COMPLETE\n\n" + summary;
                    if (!repoUrl.isEmpty()) msg += "\n🔗 " + repoUrl;
                    chatMessages.add(new ChatMessage(ChatMessage.Role.ASSISTANT, msg, true, ""));
                    chatAdapter.notifyItemInserted(chatMessages.size() - 1);

                    appendTerminal("claude", "🎉 " + summary);
                }

                @Override
                public void onError(String error) {
                    isBuilding = false;
                    sendBtn.setVisibility(View.VISIBLE);
                    stopBtn.setVisibility(View.GONE);
                    if (timerHandler != null) timerHandler.removeCallbacksAndMessages(null);
                    phaseLabel.setText("ERROR");
                    appendTerminal("claude", "❌ " + error);
                    chatMessages.add(new ChatMessage(ChatMessage.Role.ASSISTANT, "❌ Error: " + error));
                    chatAdapter.notifyItemInserted(chatMessages.size() - 1);
                }
            });
    }

    private void setPhaseActive(String phaseId) {
        for (PipelinePhase phase : phases) {
            if (phase.getStatus() == PipelinePhase.Status.RUNNING) {
                phase.setStatus(PipelinePhase.Status.DONE);
            }
            if (phase.getId().equals(phaseId)) {
                phase.setStatus(PipelinePhase.Status.RUNNING);
            }
        }
        updatePhaseBar();
    }

    private void markAllPhasesDone() {
        for (PipelinePhase phase : phases) {
            phase.setStatus(PipelinePhase.Status.DONE);
        }
        updatePhaseBar();
    }

    private void resetAllPhases() {
        for (PipelinePhase phase : phases) {
            phase.setStatus(PipelinePhase.Status.PENDING);
        }
        updatePhaseBar();
    }

    private void setAgentActive(String agentId) {
        for (Agent agent : agents) {
            if (agent.getId().equals(agentId)) {
                agent.setStatus(Agent.Status.ACTIVE);
            } else if (agent.getStatus() == Agent.Status.ACTIVE) {
                agent.setStatus(Agent.Status.DONE);
            }
        }
        ((AgentPanelAdapter) agentRecyclerView.getAdapter()).notifyDataSetChanged();
    }

    private void markAllAgentsDone() {
        for (Agent agent : agents) {
            agent.setStatus(Agent.Status.DONE);
        }
        ((AgentPanelAdapter) agentRecyclerView.getAdapter()).notifyDataSetChanged();
    }

    private void resetAllAgents() {
        for (Agent agent : agents) {
            agent.setStatus(Agent.Status.STANDBY);
            agent.setCurrentTask("");
        }
        ((AgentPanelAdapter) agentRecyclerView.getAdapter()).notifyDataSetChanged();
    }

    private void startTimer() {
        timerHandler = new Handler(Looper.getMainLooper());
        timerHandler.postDelayed(new Runnable() {
            @Override
            public void run() {
                if (isBuilding) {
                    long elapsed = System.currentTimeMillis() - buildStartTime;
                    int seconds = (int) (elapsed / 1000);
                    int mins = seconds / 60;
                    int secs = seconds % 60;
                    elapsedTime.setText(String.format("%02d:%02d", mins, secs));
                    timerHandler.postDelayed(this, 1000);
                }
            }
        }, 1000);
    }

    private void appendTerminal(String type, String text) {
        mainHandler.post(() -> {
            TextView line = new TextView(this);
            line.setText(text);
            line.setTextSize(11);
            line.setPadding(4, 2, 4, 2);

            switch (type) {
                case "claude": line.setTextColor(Color.parseColor("#c084fc")); break;
                case "command": line.setTextColor(Color.parseColor("#22d3ee")); break;
                case "system": line.setTextColor(Color.parseColor("#8b5cf6")); break;
                case "success": line.setTextColor(Color.parseColor("#10b981")); break;
                case "error": line.setTextColor(Color.parseColor("#f87171")); break;
                default: line.setTextColor(Color.parseColor("#a0a0b0")); break;
            }

            terminalContainer.addView(line);
            // Auto-scroll
            terminalScroll.post(() -> terminalScroll.fullScroll(ScrollView.FOCUS_DOWN));
        });
    }

    @Override
    protected void onDestroy() {
        if (timerHandler != null) timerHandler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }
}
