package com.whoamisecai.models;

/**
 * WHOAMISecAI — Pipeline Phase Model (28 Phases)
 */
public class PipelinePhase {

    public enum Status {
        PENDING, RUNNING, DONE, ERROR
    }

    private final int number;
    private final String id;
    private final String name;
    private final String agent;
    private final String color;
    private Status status;
    private String detail;
    private long elapsedMs;

    public PipelinePhase(int number, String id, String name, String agent, String color) {
        this.number = number;
        this.id = id;
        this.name = name;
        this.agent = agent;
        this.color = color;
        this.status = Status.PENDING;
        this.detail = "";
        this.elapsedMs = 0;
    }

    public int getNumber() { return number; }
    public String getId() { return id; }
    public String getName() { return name; }
    public String getAgent() { return agent; }
    public String getColor() { return color; }
    public Status getStatus() { return status; }
    public void setStatus(Status status) { this.status = status; }
    public String getDetail() { return detail; }
    public void setDetail(String detail) { this.detail = detail; }
    public long getElapsedMs() { return elapsedMs; }
    public void setElapsedMs(long ms) { this.elapsedMs = ms; }

    public static PipelinePhase[] createAll() {
        return new PipelinePhase[]{
            p(1,  "context-analysis",      "Context Analysis",       "heimdall",   "#6366f1"),
            p(2,  "planning",              "Deep Planning",          "director",   "#8b5cf6"),
            p(3,  "architecting",          "Architecture Design",    "director",   "#a78bfa"),
            p(4,  "task-decomposition",    "Task Decomposition",      "john_kramer","#c084fc"),
            p(5,  "multi-model-validation","Multi-Model Validation",  "morpheus",   "#34d399"),
            p(6,  "coding",                "Code Generation",         "jarvis",     "#22d3ee"),
            p(7,  "code-synthesis",        "Code Synthesis",          "data",       "#38bdf8"),
            p(8,  "code-enhancement",      "Code Enhancement",        "data",       "#2dd4bf"),
            p(9,  "code-translation",      "Cross-Language Analysis", "morpheus",   "#a3e635"),
            p(10, "quality-review",        "Quality Review",          "data",       "#c084fc"),
            p(11, "security-audit",        "Security Audit",          "sherlock",   "#f97316"),
            p(12, "code-interpreter",      "Code Interpreter",        "data",       "#4ade80"),
            p(13, "executing",             "File Execution",          "jarvis",     "#60a5fa"),
            p(14, "test-generation",       "Test Generation",         "ripley",    "#f472b6"),
            p(15, "testing",               "Test Execution",          "ripley",    "#fbbf24"),
            p(16, "repairing",             "Self-Repair Loop",        "saul",       "#f87171"),
            p(17, "code-refactoring",      "Code Refactoring",        "data",       "#c084fc"),
            p(18, "code-optimization",     "Code Optimization",       "data",       "#2dd4bf"),
            p(19, "performance-check",     "Performance Check",        "data",       "#a78bfa"),
            p(20, "architecture-validation","Architecture Validation", "morpheus",  "#94a3b8"),
            p(21, "ensemble-review",       "Ensemble Review",         "morpheus",   "#34d399"),
            p(22, "devin-review",          "Devin Final Review",      "wick",       "#d946ef"),
            p(23, "deploying",             "Smart Deploy",            "wick",       "#10b981"),
            p(24, "packaging",             "Packaging",               "wick",       "#60a5fa"),
            p(25, "documentation",         "Documentation",           "davinci",    "#fb923c"),
            p(26, "accessibility-check",   "Accessibility Check",     "davinci",   "#94a3b8"),
            p(27, "monitoring-setup",       "Monitoring Setup",        "jarvis",     "#22d3ee"),
            p(28, "delivery",              "Delivery + Summary",       "wick",       "#d946ef"),
        };
    }

    private static PipelinePhase p(int num, String id, String name, String agent, String color) {
        return new PipelinePhase(num, id, name, agent, color);
    }
}
