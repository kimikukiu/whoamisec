package com.whoamisecai.adapters;

import android.content.Context;
import android.graphics.Color;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.whoamisecai.R;
import com.whoamisecai.models.ChatMessage;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class ChatMessageAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder> {

    private static final int TYPE_USER = 0;
    private static final int TYPE_ASSISTANT = 1;

    private final List<ChatMessage> messages;
    private final Context context;
    private final SimpleDateFormat timeFormat = new SimpleDateFormat("HH:mm", Locale.getDefault());

    public ChatMessageAdapter(Context context, List<ChatMessage> messages) {
        this.context = context;
        this.messages = messages;
    }

    @Override
    public int getItemViewType(int position) {
        return messages.get(position).getRole() == ChatMessage.Role.USER ? TYPE_USER : TYPE_ASSISTANT;
    }

    @NonNull
    @Override
    public RecyclerView.ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        if (viewType == TYPE_USER) {
            return new UserViewHolder(LayoutInflater.from(context).inflate(R.layout.item_chat_user, parent, false));
        }
        return new AssistantViewHolder(LayoutInflater.from(context).inflate(R.layout.item_chat_assistant, parent, false));
    }

    @Override
    public void onBindViewHolder(@NonNull RecyclerView.ViewHolder holder, int position) {
        ChatMessage msg = messages.get(position);
        String time = timeFormat.format(new Date(msg.getTimestamp()));

        if (holder instanceof UserViewHolder) {
            UserViewHolder h = (UserViewHolder) holder;
            h.content.setText(msg.getContent());
            h.time.setText(time);
        } else {
            AssistantViewHolder h = (AssistantViewHolder) holder;
            h.content.setText(msg.getContent());
            h.time.setText(time);
            if (msg.isBuilder()) {
                h.builderBadge.setVisibility(View.VISIBLE);
            } else {
                h.builderBadge.setVisibility(View.GONE);
            }
        }
    }

    @Override
    public int getItemCount() { return messages.size(); }

    static class UserViewHolder extends RecyclerView.ViewHolder {
        TextView content, time;
        UserViewHolder(View v) {
            super(v);
            content = v.findViewById(R.id.chat_msg_content);
            time = v.findViewById(R.id.chat_msg_time);
        }
    }

    static class AssistantViewHolder extends RecyclerView.ViewHolder {
        TextView content, time, builderBadge;
        AssistantViewHolder(View v) {
            super(v);
            content = v.findViewById(R.id.chat_msg_content);
            time = v.findViewById(R.id.chat_msg_time);
            builderBadge = v.findViewById(R.id.chat_builder_badge);
        }
    }
}
