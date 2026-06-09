package com.whoamisecai.models;

import java.util.Arrays;
import java.util.List;

public class AiModel {
    private final String id;
    private final String name;
    private final String provider;
    private final String category;

    public AiModel(String id, String name, String provider, String category) {
        this.id = id; this.name = name; this.provider = provider; this.category = category;
    }
    public String getId() { return id; }
    public String getName() { return name; }
    public String getProvider() { return provider; }
    public String getCategory() { return category; }

    public static List<AiModel> getAllModels() {
        return Arrays.asList(
            new AiModel("nvidia/llama-3.1-nemotron-70b-instruct","Nemotron 70B","NVIDIA","⚡ GPU-Accelerated"),
            new AiModel("nvidia/llama-3.3-nemotron-70b-instruct","Nemotron 3.3 70B","NVIDIA","⚡ GPU-Accelerated"),
            new AiModel("meta-llama/llama-4-maverick","Llama 4 Maverick","Meta","⚡ GPU-Accelerated"),
            new AiModel("meta/llama-3.3-70b-instruct","Llama 3.3 70B","Meta","⚡ GPU-Accelerated"),
            new AiModel("meta/llama-3.1-405b-instruct","Llama 3.1 405B","Meta","⚡ GPU-Accelerated"),
            new AiModel("deepseek-ai/deepseek-r1","DeepSeek R1","DeepSeek","⚡ GPU-Accelerated"),
            new AiModel("mistralai/mistral-large","Mistral Large","Mistral","⚡ GPU-Accelerated"),
            new AiModel("qwen/qwen2.5-72b-instruct","Qwen 2.5 72B","Qwen","⚡ GPU-Accelerated"),
            new AiModel("qwen/qwen3-235b-a22b-instruct","Qwen3 235B MoE","Qwen","⚡ GPU-Accelerated"),
            new AiModel("microsoft/phi-4","Phi-4","Microsoft","⚡ GPU-Accelerated"),
            new AiModel("anthropic/claude-opus-4","Claude Opus 4","Anthropic","🧠 Claude"),
            new AiModel("anthropic/claude-sonnet-4","Claude Sonnet 4","Anthropic","🧠 Claude"),
            new AiModel("anthropic/claude-haiku-4","Claude Haiku 4","Anthropic","🧠 Claude"),
            new AiModel("anthropic/claude-opus-4-5","Claude Opus 4.5","Anthropic","🧠 Claude"),
            new AiModel("anthropic/claude-3.5-sonnet","Claude 3.5 Sonnet","Anthropic","🧠 Claude"),
            new AiModel("anthropic/claude-sonnet-4-20250514","Claude Sonnet 4 (May 14)","Anthropic","🧠 Claude"),
            new AiModel("openai/gpt-4o","GPT-4o","OpenAI","⚡ GPT"),
            new AiModel("openai/gpt-4o-mini","GPT-4o Mini","OpenAI","⚡ GPT"),
            new AiModel("openai/o3","o3","OpenAI","⚡ GPT"),
            new AiModel("openai/o4-mini","o4-mini","OpenAI","⚡ GPT"),
            new AiModel("openai/gpt-4.1","GPT-4.1","OpenAI","⚡ GPT"),
            new AiModel("deepseek-chat","DeepSeek Chat","DeepSeek","🔍 DeepSeek"),
            new AiModel("deepseek-reasoner","DeepSeek R1","DeepSeek","🔍 DeepSeek"),
            new AiModel("google/gemini-2.5-pro","Gemini 2.5 Pro","Google","🌐 Gemini"),
            new AiModel("gemini-2.0-flash","Gemini 2.0 Flash","Google","🌐 Gemini"),
            new AiModel("xai/grok-3","Grok 3","xAI","🌀 Grok"),
            new AiModel("xai/grok-3-mini","Grok 3 Mini","xAI","🌀 Grok"),
            new AiModel("moonshot-v1-128k","Kimi 128K","Moonshot","📡 Kimi"),
            new AiModel("glm-4-plus","GLM-4 Plus","BigModel","🔬 GLM"),
            new AiModel("glm-4-flash","GLM-4 Flash","BigModel","🔬 GLM"),
            new AiModel("glm-z1-air","GLM-Z1 Air","BigModel","🔬 GLM"),
            new AiModel("mistral-large-latest","Mistral Large","Mistral","🌀 Mistral"),
            new AiModel("whoamisec-r1-671b","WHOAMISec R1 671B","WHOAMISec","🔒 Admin Only")
        );
    }
}
