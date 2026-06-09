package com.whoamisecai.adapters;

import android.content.Context;
import android.graphics.Color;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.whoamisecai.R;
import com.whoamisecai.models.Agent;

/**
 * RecyclerView adapter for 11 Mission Control Agents.
 * Each card shows: emoji, name, role, status badge.
 */
public class AgentPanelAdapter extends RecyclerView.Adapter<AgentPanelAdapter.ViewHolder> {

    private final Agent[] agents;
    private final Context context;

    public AgentPanelAdapter(Context context, Agent[] agents) {
        this.context = context;
        this.agents = agents;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(context).inflate(R.layout.item_agent_card, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        Agent agent = agents[position];

        holder.emoji.setText(agent.getEmoji());
        holder.name.setText(agent.getName());
        holder.role.setText(agent.getRole());

        int bgColor, statusColor, statusTextRes;
        switch (agent.getStatus()) {
            case ACTIVE:
                bgColor = 0x1A2D1B00;
                statusColor = Color.parseColor("#f59e0b");
                statusTextRes = R.string.agent_active;
                break;
            case DONE:
                bgColor = 0x1A065F46;
                statusColor = Color.parseColor("#10b981");
                statusTextRes = R.string.agent_done;
                break;
            default:
                bgColor = 0x1A1A1A2E;
                statusColor = Color.parseColor("#444455");
                statusTextRes = R.string.agent_standby;
                break;
        }

        holder.card.setBackgroundColor(bgColor);
        holder.statusBadge.setBackgroundColor(statusColor);
        holder.statusBadge.setText(statusTextRes);

        if (agent.getCurrentTask() != null && !agent.getCurrentTask().isEmpty()) {
            holder.task.setVisibility(View.VISIBLE);
            holder.task.setText(agent.getCurrentTask());
        } else {
            holder.task.setVisibility(View.GONE);
        }
    }

    @Override
    public int getItemCount() { return agents.length; }

    static class ViewHolder extends RecyclerView.ViewHolder {
        LinearLayout card;
        TextView emoji, name, role, statusBadge, task;

        ViewHolder(View itemView) {
            super(itemView);
            card = itemView.findViewById(R.id.agent_card);
            emoji = itemView.findViewById(R.id.agent_emoji);
            name = itemView.findViewById(R.id.agent_name);
            role = itemView.findViewById(R.id.agent_role);
            statusBadge = itemView.findViewById(R.id.agent_status_badge);
            task = itemView.findViewById(R.id.agent_task);
        }
    }
}
