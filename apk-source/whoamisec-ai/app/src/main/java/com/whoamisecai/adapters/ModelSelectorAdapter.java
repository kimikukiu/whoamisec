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
import com.whoamisecai.models.AiModel;

import java.util.List;

public class ModelSelectorAdapter extends RecyclerView.Adapter<ModelSelectorAdapter.ViewHolder> {

    private final List<AiModel> models;
    private final Context context;
    private final String selectedModelId;
    private final OnModelSelectedListener listener;

    public interface OnModelSelectedListener {
        void onModelSelected(AiModel model);
    }

    public ModelSelectorAdapter(Context context, List<AiModel> models, String selectedModelId, OnModelSelectedListener listener) {
        this.context = context;
        this.models = models;
        this.selectedModelId = selectedModelId;
        this.listener = listener;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(context).inflate(R.layout.item_model, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        AiModel model = models.get(position);
        boolean isSelected = model.getId().equals(selectedModelId);

        holder.name.setText(model.getName());
        holder.provider.setText(model.getProvider());
        holder.category.setText(model.getCategory());

        if (isSelected) {
            holder.card.setBackgroundColor(0x1A8B5CF6);
            holder.name.setTextColor(Color.parseColor("#8b5cf6"));
        } else {
            holder.card.setBackgroundColor(0x0D0D14);
            holder.name.setTextColor(Color.parseColor("#ffffff"));
        }

        holder.card.setOnClickListener(v -> {
            if (listener != null) listener.onModelSelected(model);
        });
    }

    @Override
    public int getItemCount() { return models.size; }

    static class ViewHolder extends RecyclerView.ViewHolder {
        LinearLayout card;
        TextView name, provider, category;
        ViewHolder(View v) {
            super(v);
            card = v.findViewById(R.id.model_card);
            name = v.findViewById(R.id.model_name);
            provider = v.findViewById(R.id.model_provider);
            category = v.findViewById(R.id.model_category);
        }
    }
}
