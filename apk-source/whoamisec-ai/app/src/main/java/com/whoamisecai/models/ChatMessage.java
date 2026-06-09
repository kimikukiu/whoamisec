package com.whoamisecai.models;

public class ChatMessage {
    public enum Role { USER, ASSISTANT, SYSTEM }
    private final Role role;
    private final String content;
    private final long timestamp;
    private final boolean isBuilder;
    private final String model;

    public ChatMessage(Role role, String content) {
        this(role, content, false, "");
    }
    public ChatMessage(Role role, String content, boolean isBuilder, String model) {
        this.role = role;
        this.content = content;
        this.isBuilder = isBuilder;
        this.model = model;
        this.timestamp = System.currentTimeMillis();
    }
    public Role getRole() { return role; }
    public String getContent() { return content; }
    public long getTimestamp() { return timestamp; }
    public boolean isBuilder() { return isBuilder; }
    public String getModel() { return model; }
}
