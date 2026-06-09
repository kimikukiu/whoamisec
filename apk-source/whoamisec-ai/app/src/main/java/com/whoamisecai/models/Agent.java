package com.whoamisecai.models;

/**
 * WHOAMISecAI — Agent Model for Mission Control
 * 
 * Represents one of 11 Mission Control agents with status tracking.
 */
public class Agent {

    public enum Status {
        STANDBY, ACTIVE, DONE
    }

    private final String id;
    private final String name;
    private final String emoji;
    private final String role;
    private Status status;
    private String currentTask;

    public Agent(String id, String name, String emoji, String role) {
        this.id = id;
        this.name = name;
        this.emoji = emoji;
        this.role = role;
        this.status = Status.STANDBY;
        this.currentTask = "";
    }

    public String getId() { return id; }
    public String getName() { return name; }
    public String getEmoji() { return emoji; }
    public String getRole() { return role; }
    public Status getStatus() { return status; }
    public void setStatus(Status status) { this.status = status; }
    public String getCurrentTask() { return currentTask; }
    public void setCurrentTask(String task) { this.currentTask = task; }

    /**
     * Factory: Create all 11 Mission Control agents.
     */
    public static Agent[] createAll() {
        return new Agent[]{
            new Agent("director_fury", "Director Fury", "🛡️", "Mission Control — Orchestrates all agents"),
            new Agent("heimdall", "Heimdall", "👁️", "Context Analysis — Scans project scope & constraints"),
            new Agent("john_kramer", "John Kramer", "🧩", "Task Decomposition — Breaks plan into subtasks"),
            new Agent("morpheus", "Morpheus", "🔀", "Multi-Model Validation — Cross-validates with 3 models"),
            new Agent("sherlock", "Sherlock Holmes", "🔍", "Security Audit — Vulnerability scanning & OWASP"),
            new Agent("data", "Data", "🧠", "Code Synthesis — Deep reasoning & refinement"),
            new Agent("saul", "Saul Goodman", "🩹", "Self-Repair — Auto-fixes code errors"),
            new Agent("jarvis", "JARVIS", "⚙️", "Code Generation & Execution — Builds files"),
            new Agent("ripley", "Ripley", "🐛", "Test Generation & Execution — Validates code"),
            new Agent("davinci", "Da Vinci", "🎨", "Documentation & A11y — README, API docs, a11y"),
            new Agent("wick", "John Wick", "⚔️", "Deploy & Delivery — Final handoff & packaging"),
        };
    }
}
