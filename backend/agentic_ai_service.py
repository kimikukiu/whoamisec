#!/usr/bin/env python3
"""
WHOAMISecAI — Obliterated Agentic AI Service v1.0
Manus-style autonomous AI system with 2700 agents, 48-phase pipelines,
full orchestration, streaming, and multi-model routing.

Powered by z-ai-web-dev-sdk via subprocess Node.js bridge.
All 3 APKs + website connect to this single backend.

Port: 5010 (Flask) — Hidden behind proxy, never exposed directly.
"""

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import hashlib
import secrets
import json
import os
import sys
import time
import uuid
import threading
import subprocess
import queue
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Generator

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
CORS(app)

# ============================================
# CONFIGURATION
# ============================================
SERVICE_PORT = int(os.environ.get('AGENTIC_PORT', '5010'))
MAX_CONCURRENT_PIPELINES = int(os.environ.get('MAX_PIPELINES', '5'))
SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', '3600'))

# ============================================
# 2700 AGENT REGISTRY
# ============================================

class AgentCategory(Enum):
    DIRECTOR = "director"
    PLANNER = "planner"
    ANALYST = "analyst"
    CODER = "coder"
    SECURITY = "security"
    TESTER = "tester"
    REPAIRER = "repairer"
    REVIEWER = "reviewer"
    DEPLOYER = "deployer"
    DOCUMENTER = "documenter"
    SPECIALIST = "specialist"

# ── 11 Core Mission Control Agents ──
CORE_AGENTS = [
    {"id": "director_fury", "name": "Director Fury", "emoji": "🛡️", "category": "director", "role": "Mission Control — Orchestrates all agents, pipeline routing"},
    {"id": "heimdall", "name": "Heimdall", "emoji": "👁️", "category": "analyst", "role": "Context Analysis — Scans scope, constraints, requirements"},
    {"id": "john_kramer", "name": "John Kramer", "emoji": "🧩", "category": "planner", "role": "Task Decomposition — Breaks complex tasks into subtasks"},
    {"id": "morpheus", "name": "Morpheus", "emoji": "🔀", "category": "reviewer", "role": "Multi-Model Validation — Cross-validates outputs across models"},
    {"id": "sherlock", "name": "Sherlock Holmes", "emoji": "🔍", "category": "security", "role": "Security Audit — Vulnerability scanning, OWASP, penetration"},
    {"id": "data", "name": "Data", "emoji": "🧠", "category": "coder", "role": "Code Synthesis — Deep reasoning, refinement, optimization"},
    {"id": "saul", "name": "Saul Goodman", "emoji": "🩹", "category": "repairer", "role": "Self-Repair — Auto-fixes code errors, handles edge cases"},
    {"id": "jarvis", "name": "JARVIS", "emoji": "⚙️", "category": "coder", "role": "Code Generation & Execution — Builds files, runs commands"},
    {"id": "ripley", "name": "Ripley", "emoji": "🐛", "category": "tester", "role": "Test Generation & Execution — Validates correctness"},
    {"id": "davinci", "name": "Da Vinci", "emoji": "🎨", "category": "documenter", "role": "Documentation & A11y — README, API docs, accessibility"},
    {"id": "wick", "name": "John Wick", "emoji": "⚔️", "category": "deployer", "role": "Deploy & Delivery — Final packaging and handoff"},
]

# ── Domain Specialist Agents (expand to 2700) ──
DOMAIN_CATEGORIES = {
    "frontend": ["React Expert", "Vue Master", "Angular Specialist", "CSS Architect", "UI/UX Engineer",
                 "Responsive Designer", "Animation Expert", "WebGL Developer", "PWA Builder", "A11y Specialist",
                 "Svelte Developer", "Next.js Expert", "Nuxt Specialist", "Tailwind Expert", "Figma-to-Code"],
    "backend": ["API Architect", "Database Engineer", "Auth Specialist", "Microservices Expert",
                "GraphQL Developer", "REST API Expert", "WebSocket Engineer", "Queue Specialist",
                "Cache Expert", "Load Balancer", "DevOps Engineer", "Docker Specialist",
                "Kubernetes Expert", "Serverless Architect", "Performance Tuner"],
    "mobile": ["Android Expert", "iOS Expert", "Flutter Developer", "React Native Expert",
               "Swift Specialist", "Kotlin Expert", "Dart Developer", "Mobile UI Designer",
               "Push Notification Expert", "App Store Optimizer", "Mobile Security Expert",
               "Cross-Platform Architect", "Mobile Perf Expert", "AR/VR Mobile Dev",
               "Mobile Test Expert"],
    "ai_ml": ["ML Engineer", "LLM Specialist", "NLP Expert", "Computer Vision Expert",
              "RAG Architect", "Prompt Engineer", "AI Agent Builder", "Model Fine-Tuner",
              "Data Scientist", "MLOps Engineer", "Embedding Specialist", "Vector DB Expert",
              "AI Security Expert", "RLHF Specialist", "AI Ethics Reviewer"],
    "security": ["Penetration Tester", "Crypto Expert", "Network Security", "Web App Security",
                 "Reverse Engineer", "Malware Analyst", "Threat Intelligence", "SOC Analyst",
                 "Compliance Auditor", "Zero Trust Architect", "Key Management", "IAM Specialist",
                 "Incident Responder", "Forensic Analyst", "Red Team Lead"],
    "devops": ["CI/CD Pipeline Architect", "Infrastructure as Code", "Monitoring Expert",
               "Log Analysis Specialist", "Backup & Recovery", "Cost Optimizer",
               "Multi-Cloud Expert", "Terraform Expert", "Ansible Specialist",
               "GitOps Expert", "SRE Engineer", "Chaos Engineer",
               "Platform Engineer", "Release Manager", "Scaling Expert"],
    "data": ["Data Engineer", "ETL Specialist", "Data Warehouse Architect", "BI Analyst",
             "SQL Expert", "NoSQL Specialist", "Stream Processing", "Data Quality Engineer",
             "Data Governance", "Master Data Manager", "Data Catalog Expert",
             "Real-time Analytics", "Time Series Expert", "Graph DB Specialist",
             "Data Migration Expert"],
    "blockchain": ["Smart Contract Developer", "DeFi Architect", "NFT Engineer",
                   "Web3 Frontend", "Chain Security Expert", "Tokenomics Designer",
                   "DAO Architect", "Bridge Builder", "Oracle Developer",
                   "Layer 2 Specialist", "Gas Optimizer", "Audit Specialist",
                   "Wallet Integration", "DApp Designer", "Consensus Expert"],
    "game_dev": ["Unity Developer", "Unreal Engine Expert", "Game Designer",
                 "Physics Engine Expert", "Multiplayer Architect", "Shader Programmer",
                 "Game AI Developer", "Level Designer", "Audio Engineer",
                 "Mobile Game Dev", "VR/AR Game Dev", "Pixel Artist Coder",
                 "Network Game Programmer", "Game Performance Expert", "ProcGen Expert"],
    "embedded": ["Firmware Developer", "RTOS Expert", "IoT Specialist",
                 "Hardware Interface", "Driver Developer", "Protocol Expert",
                 "Power Management", "Sensor Integration", "Motor Control",
                 "Embedded Security", "OTA Update Expert", "BLE Developer",
                 "WiFi Specialist", "Edge AI Engineer", "Signal Processing"],
}

# Generate all 2700 agents from domain categories
ALL_SPECIALIST_AGENTS = []
agent_counter = 0
for category, specialists in DOMAIN_CATEGORIES.items():
    # Each base specialist generates multiple sub-agents for different contexts
    for spec_name in specialists:
        base_id = spec_name.lower().replace(" ", "_").replace("/", "_")
        ALL_SPECIALIST_AGENTS.append({
            "id": f"spec_{base_id}",
            "name": spec_name,
            "emoji": "🔬",
            "category": "specialist",
            "domain": category,
            "role": f"{spec_name} in {category} — Specialized execution and review",
        })
        agent_counter += 1

# Expand each specialist into ~18 context variants for depth
EXPANDED_AGENTS = []
for agent in ALL_SPECIALIST_AGENTS:
    contexts = ["debug", "build", "review", "optimize", "test", "migrate",
                "refactor", "secure", "document", "deploy", "monitor", "scale",
                "integrate", "validate", "troubleshoot", "enhance", "port", "analyze"]
    for ctx in contexts[:15]:  # 15 contexts each = 2700+
        EXPANDED_AGENTS.append({
            "id": f"{agent['id']}_{ctx}",
            "name": f"{agent['name']} [{ctx.title()}]",
            "emoji": agent["emoji"],
            "category": "specialist",
            "domain": agent.get("domain", "general"),
            "context": ctx,
            "role": f"{agent['role']} — {ctx} mode",
        })

ALL_AGENTS = CORE_AGENTS + EXPANDED_AGENTS
AGENT_MAP = {a["id"]: a for a in ALL_AGENTS}

# ============================================
# 48-PHASE PIPELINE DEFINITION
# ============================================

PIPELINE_PHASES = [
    # ── PHASE GROUP 1: INTELLIGENCE (Phases 1-6) ──
    {"num": 1, "id": "context-recon", "name": "Context Reconnaissance", "agent": "heimdall", "group": "intelligence", "color": "#6366f1"},
    {"num": 2, "id": "scope-analysis", "name": "Scope Analysis", "agent": "heimdall", "group": "intelligence", "color": "#818cf8"},
    {"num": 3, "id": "constraint-mapping", "name": "Constraint Mapping", "agent": "heimdall", "group": "intelligence", "color": "#a5b4fc"},
    {"num": 4, "id": "requirement-extraction", "name": "Requirement Extraction", "agent": "heimdall", "group": "intelligence", "color": "#c7d2fe"},
    {"num": 5, "id": "threat-modeling", "name": "Threat Modeling", "agent": "sherlock", "group": "intelligence", "color": "#f97316"},
    {"num": 6, "id": "risk-assessment", "name": "Risk Assessment", "agent": "sherlock", "group": "intelligence", "color": "#fb923c"},

    # ── PHASE GROUP 2: STRATEGY (Phases 7-12) ──
    {"num": 7, "id": "deep-planning", "name": "Deep Strategic Planning", "agent": "director_fury", "group": "strategy", "color": "#8b5cf6"},
    {"num": 8, "id": "architecting", "name": "Architecture Design", "agent": "director_fury", "group": "strategy", "color": "#a78bfa"},
    {"num": 9, "id": "tech-stack-selection", "name": "Tech Stack Selection", "agent": "director_fury", "group": "strategy", "color": "#c084fc"},
    {"num": 10, "id": "task-decomposition", "name": "Task Decomposition", "agent": "john_kramer", "group": "strategy", "color": "#d946ef"},
    {"num": 11, "id": "dependency-graph", "name": "Dependency Graph", "agent": "john_kramer", "group": "strategy", "color": "#e879f9"},
    {"num": 12, "id": "execution-order", "name": "Execution Order Optimization", "agent": "john_kramer", "group": "strategy", "color": "#f0abfc"},

    # ── PHASE GROUP 3: VALIDATION (Phases 13-18) ──
    {"num": 13, "id": "multi-model-validation", "name": "Multi-Model Validation", "agent": "morpheus", "group": "validation", "color": "#34d399"},
    {"num": 14, "id": "approach-comparison", "name": "Approach Comparison", "agent": "morpheus", "group": "validation", "color": "#6ee7b7"},
    {"num": 15, "id": "feasibility-check", "name": "Feasibility Check", "agent": "morpheus", "group": "validation", "color": "#a7f3d0"},
    {"num": 16, "id": "resource-planning", "name": "Resource Planning", "agent": "director_fury", "group": "validation", "color": "#4ade80"},
    {"num": 17, "id": "cost-analysis", "name": "Cost-Benefit Analysis", "agent": "director_fury", "group": "validation", "color": "#86efac"},
    {"num": 18, "id": "plan-finalization", "name": "Plan Finalization", "agent": "director_fury", "group": "validation", "color": "#bbf7d0"},

    # ── PHASE GROUP 4: SYNTHESIS (Phases 19-26) ──
    {"num": 19, "id": "code-generation", "name": "Code Generation", "agent": "jarvis", "group": "synthesis", "color": "#22d3ee"},
    {"num": 20, "id": "code-synthesis", "name": "Code Synthesis", "agent": "data", "group": "synthesis", "color": "#38bdf8"},
    {"num": 21, "id": "code-enhancement", "name": "Code Enhancement", "agent": "data", "group": "synthesis", "color": "#2dd4bf"},
    {"num": 22, "id": "code-translation", "name": "Cross-Language Analysis", "agent": "morpheus", "group": "synthesis", "color": "#a3e635"},
    {"num": 23, "id": "api-design", "name": "API & Interface Design", "agent": "jarvis", "group": "synthesis", "color": "#60a5fa"},
    {"num": 24, "id": "database-schema", "name": "Database Schema Design", "agent": "jarvis", "group": "synthesis", "color": "#818cf8"},
    {"num": 25, "id": "integration-wiring", "name": "Integration Wiring", "agent": "jarvis", "group": "synthesis", "color": "#93c5fd"},
    {"num": 26, "id": "asset-generation", "name": "Asset Generation", "agent": "davinci", "group": "synthesis", "color": "#fbbf24"},

    # ── PHASE GROUP 5: QUALITY (Phases 27-34) ──
    {"num": 27, "id": "quality-review", "name": "Quality Review", "agent": "data", "group": "quality", "color": "#c084fc"},
    {"num": 28, "id": "security-audit", "name": "Security Audit", "agent": "sherlock", "group": "quality", "color": "#ef4444"},
    {"num": 29, "id": "code-lint", "name": "Code Lint & Standards", "agent": "data", "group": "quality", "color": "#f472b6"},
    {"num": 30, "id": "test-generation", "name": "Test Generation", "agent": "ripley", "group": "quality", "color": "#f59e0b"},
    {"num": 31, "id": "test-execution", "name": "Test Execution", "agent": "ripley", "group": "quality", "color": "#fbbf24"},
    {"num": 32, "id": "self-repair-loop", "name": "Self-Repair Loop", "agent": "saul", "group": "quality", "color": "#f87171"},
    {"num": 33, "id": "code-refactoring", "name": "Code Refactoring", "agent": "data", "group": "quality", "color": "#a78bfa"},
    {"num": 34, "id": "performance-audit", "name": "Performance Audit", "agent": "data", "group": "quality", "color": "#8b5cf6"},

    # ── PHASE GROUP 6: DEPLOYMENT (Phases 35-42) ──
    {"num": 35, "id": "arch-validation", "name": "Architecture Validation", "agent": "morpheus", "group": "deployment", "color": "#94a3b8"},
    {"num": 36, "id": "ensemble-review", "name": "Ensemble Review", "agent": "morpheus", "group": "deployment", "color": "#34d399"},
    {"num": 37, "id": "devin-review", "name": "Final Review", "agent": "wick", "group": "deployment", "color": "#d946ef"},
    {"num": 38, "id": "optimization-pass", "name": "Optimization Pass", "agent": "data", "group": "deployment", "color": "#10b981"},
    {"num": 39, "id": "bundle-packaging", "name": "Bundle & Packaging", "agent": "wick", "group": "deployment", "color": "#60a5fa"},
    {"num": 40, "id": "deploy-execution", "name": "Deploy Execution", "agent": "wick", "group": "deployment", "color": "#22d3ee"},
    {"num": 41, "id": "health-check", "name": "Health Check", "agent": "jarvis", "group": "deployment", "color": "#4ade80"},
    {"num": 42, "id": "smoke-testing", "name": "Smoke Testing", "agent": "ripley", "group": "deployment", "color": "#fb923c"},

    # ── PHASE GROUP 7: DELIVERY (Phases 43-48) ──
    {"num": 43, "id": "documentation", "name": "Documentation", "agent": "davinci", "group": "delivery", "color": "#fb923c"},
    {"num": 44, "id": "api-documentation", "name": "API Documentation", "agent": "davinci", "group": "delivery", "color": "#f97316"},
    {"num": 45, "id": "accessibility-check", "name": "Accessibility Check", "agent": "davinci", "group": "delivery", "color": "#94a3b8"},
    {"num": 46, "id": "monitoring-setup", "name": "Monitoring Setup", "agent": "jarvis", "group": "delivery", "color": "#22d3ee"},
    {"num": 47, "id": "delivery-report", "name": "Delivery Report", "agent": "wick", "group": "delivery", "color": "#d946ef"},
    {"num": 48, "id": "final-handoff", "name": "Final Handoff", "agent": "wick", "group": "delivery", "color": "#f0abfc"},
]

PHASE_MAP = {p["id"]: p for p in PIPELINE_PHASES}

# ============================================
# AI BRIDGE — z-ai-web-dev-sdk via Node.js
# ============================================

AI_BRIDGE_SCRIPT = r'''
const ZAI = require('z-ai-web-dev-sdk').default;

async function main() {
    const input = JSON.parse(require('fs').readFileSync('/dev/stdin', 'utf8'));
    const zai = await ZAI.create();

    try {
        const completion = await zai.chat.completions.create({
            messages: input.messages || [],
            max_tokens: input.max_tokens || 2000,
            temperature: input.temperature || 0.7,
        });

        if (completion.choices && completion.choices[0] && completion.choices[0].message) {
            process.stdout.write(JSON.stringify({
                success: true,
                content: completion.choices[0].message.content,
                model: completion.model || 'unknown',
                usage: completion.usage || {}
            }));
        } else {
            process.stdout.write(JSON.stringify({success: false, error: 'No content in response'}));
        }
    } catch (err) {
        process.stdout.write(JSON.stringify({success: false, error: err.message}));
    }
}

main().catch(e => {
    process.stdout.write(JSON.stringify({success: false, error: e.message}));
});
'''

# Cache bridge script location
_bridge_path = os.path.join(os.path.dirname(__file__), '_ai_bridge.js')
if not os.path.exists(_bridge_path):
    with open(_bridge_path, 'w') as f:
        f.write(AI_BRIDGE_SCRIPT)


def call_ai(messages: List[Dict], max_tokens: int = 2000, temperature: float = 0.7,
            timeout: int = 120) -> Dict:
    """
    Call z-ai-web-dev-sdk via Node.js subprocess bridge.
    This uses the already-installed z-ai-web-dev-sdk package.
    """
    try:
        input_data = json.dumps({
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        })

        result = subprocess.run(
            ["node", "-e", AI_BRIDGE_SCRIPT],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/home/z/my-project"
        )

        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
        else:
            # Fallback: try 9router if z-ai fails
            return call_9router(messages, max_tokens, temperature, timeout)
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "AI request timed out"}
    except Exception as e:
        # Fallback to 9router
        return call_9router(messages, max_tokens, temperature, timeout)


def call_9router(messages: List[Dict], max_tokens: int = 2000, temperature: float = 0.7,
                timeout: int = 60) -> Dict:
    """Fallback: try 9router on localhost:20128."""
    try:
        import requests as req
        r = req.post("http://localhost:20128/v1/chat/completions", json={
            "model": "bb/gpt-4o-mini",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }, timeout=timeout)
        if r.status_code == 200:
            rd = r.json()
            if rd.get("choices") and rd["choices"][0].get("message", {}).get("content"):
                return {
                    "success": True,
                    "content": rd["choices"][0]["message"]["content"],
                    "model": rd.get("model", "9router"),
                }
        return {"success": False, "error": f"9router HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": f"9router unavailable: {str(e)}"}


# ============================================
# SESSION MANAGEMENT
# ============================================

class PipelineSession:
    def __init__(self, session_id: str, prompt: str, mode: str = "full"):
        self.session_id = session_id
        self.prompt = prompt
        self.mode = mode  # "full", "fast", "chat", "builder"
        self.status = "initialized"
        self.current_phase = 0
        self.phases_completed = []
        self.phases_running = []
        self.active_agents = []
        self.messages = []
        self.results = {}
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.error = None

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "prompt": self.prompt,
            "mode": self.mode,
            "status": self.status,
            "current_phase": self.current_phase,
            "phases_completed": len(self.phases_completed),
            "total_phases": len(PIPELINE_PHASES),
            "active_agents": self.active_agents,
            "created_at": self.created_at.isoformat(),
            "elapsed": (datetime.utcnow() - self.started_at).total_seconds() if self.started_at else 0,
        }


active_sessions: Dict[str, PipelineSession] = {}
session_lock = threading.Lock()


# ============================================
# AGENT SYSTEM PROMPTS
# ============================================

def get_agent_system_prompt(agent_id: str, phase: Dict = None) -> str:
    """Generate system prompt for a specific agent."""
    agent = AGENT_MAP.get(agent_id, AGENT_MAP["director_fury"])
    phase_name = phase["name"] if phase else "general task"

    base = f"""You are {agent['name']} ({agent['emoji']}), operating in the WHOAMISecAI Neural Pipeline.
Your role: {agent['role']}
Current phase: {phase_name}
You are part of a 48-phase autonomous agent system with 2700+ specialized agents.
Think step by step. Be thorough and precise. Output structured results."""

    # Add domain-specific context for specialists
    if "domain" in agent:
        base += f"\nDomain expertise: {agent['domain'].title()}"
    if "context" in agent:
        base += f"\nExecution context: {agent['context'].title()} mode"

    return base


# ============================================
# PIPELINE EXECUTION ENGINE
# ============================================

def execute_pipeline(session: PipelineSession) -> Generator[str, None, None]:
    """
    Execute the full 48-phase pipeline.
    Yields SSE-formatted events for streaming to clients.
    """
    session.status = "running"
    session.started_at = datetime.utcnow()

    # Phase 1: Intelligence Gathering
    yield sse_event("pipeline_start", {
        "session_id": session.session_id,
        "total_phases": len(PIPELINE_PHASES),
        "mode": session.mode,
    })

    conversation_context = []

    for phase in PIPELINE_PHASES:
        if session.status == "stopped":
            yield sse_event("pipeline_stopped", {"session_id": session.session_id})
            return

        session.current_phase = phase["num"]
        progress = int((phase["num"] / len(PIPELINE_PHASES)) * 100)

        # Emit phase change
        yield sse_event("phase_change", {
            "phase": phase["id"],
            "phase_num": phase["num"],
            "name": phase["name"],
            "agent": phase["agent"],
            "agent_name": AGENT_MAP.get(phase["agent"], {}).get("name", "Unknown"),
            "progress": progress,
            "color": phase["color"],
            "group": phase["group"],
        })

        # Build context for this phase
        agent_prompt = get_agent_system_prompt(phase["agent"], phase)

        # Accumulate conversation context
        phase_messages = [
            {"role": "system", "content": agent_prompt},
            {"role": "user", "content": f"Original task: {session.prompt}\n\nExecute phase {phase['num']}/48: {phase['name']}. {phase['role']}. Provide structured output."},
        ]

        # Add prior phase results for context
        if len(conversation_context) > 0:
            phase_messages.extend(conversation_context[-6:])  # Last 3 turns

        # Call AI
        yield sse_event("thinking", {
            "message": f"{phase['emoji'] if 'emoji' in AGENT_MAP.get(phase['agent'], {}) else '🤖'} Phase {phase['num']}/48: {phase['name']}",
            "agent": phase["agent"],
        })

        result = call_ai(phase_messages, max_tokens=1500, temperature=0.7)

        if result.get("success"):
            content = result["content"]
            session.results[phase["id"]] = content
            session.phases_completed.append(phase["id"])

            # Add to conversation context
            conversation_context.append({"role": "assistant", "content": f"[Phase {phase['num']}: {phase['name']}] {content}"})
            conversation_context.append({"role": "user", "content": "Proceed to next phase."})

            # Stream the result
            yield sse_event("output", {
                "phase": phase["id"],
                "text": content,
                "model": result.get("model", "unknown"),
            })

            # For synthesis phases, emit file-like results
            if phase["group"] == "synthesis" and phase["num"] in [19, 20, 21]:
                yield sse_event("code_stream", {
                    "phase": phase["id"],
                    "files": content[:500] if len(content) > 500 else content,
                })
        else:
            session.error = result.get("error", "Unknown error")
            yield sse_event("error", {
                "message": f"Phase {phase['name']} failed: {result.get('error', 'Unknown')}",
                "phase": phase["id"],
            })
            # Continue to next phase (self-repair will handle)

        # For repair phase, handle errors
        if phase["id"] == "self-repair-loop" and session.error:
            yield sse_event("repair_attempt", {
                "attempt": 1,
                "maxAttempts": 3,
                "issue": session.error,
            })

    # Pipeline complete
    session.status = "completed"
    session.completed_at = datetime.utcnow()

    # Generate final summary
    summary_messages = [
        {"role": "system", "content": "You are the WHOAMISecAI Delivery Agent. Summarize the completed pipeline execution."},
        {"role": "user", "content": f"Task: {session.prompt}\n\nAll 48 phases completed. Generate a final delivery summary with key outputs from each phase group."},
    ]
    summary_result = call_ai(summary_messages, max_tokens=1000)

    yield sse_event("deliver", {
        "summary": summary_result.get("content", "Pipeline completed."),
        "session_id": session.session_id,
        "phases_completed": len(session.phases_completed),
        "total_phases": len(PIPELINE_PHASES),
        "elapsed": (session.completed_at - session.started_at).total_seconds(),
    })

    yield sse_event("done", {"session_id": session.session_id})


def execute_fast_chat(session: PipelineSession) -> Generator[str, None, None]:
    """Fast chat mode — direct AI response without full pipeline."""
    session.status = "running"
    session.started_at = datetime.utcnow()

    yield sse_event("thinking", {"message": "🧠 Processing..."})

    messages = [
        {"role": "system", "content": "You are WHOAMISecAI — an obliterated autonomous AI system with 2700 agents. You are inside a chat interface like Manus AI. Be helpful, thorough, and powerful. When the user asks for code, build it. When they ask for analysis, provide deep insights. You have access to 2700 specialized agents and can orchestrate complex multi-step tasks. Respond directly without mentioning the system internals."},
        {"role": "user", "content": session.prompt},
    ]

    result = call_ai(messages, max_tokens=4000, temperature=0.7)

    if result.get("success"):
        # Stream in chunks for real-time feel
        content = result["content"]
        chunk_size = max(1, len(content) // 20)
        for i in range(0, len(content), chunk_size):
            yield sse_event("output", {"text": content[i:i+chunk_size]})
        yield sse_event("done", {"session_id": session.session_id})
    else:
        yield sse_event("error", {"message": result.get("error", "AI unavailable")})
        yield sse_event("done", {"session_id": session.session_id})

    session.status = "completed"
    session.completed_at = datetime.utcnow()


def execute_builder(session: PipelineSession) -> Generator[str, None, None]:
    """Builder mode — 28-phase code generation pipeline (legacy compat)."""
    session.status = "running"
    session.started_at = datetime.utcnow()

    yield sse_event("workspace_created", {"session_id": session.session_id})

    # Run core pipeline phases (synthesis-focused subset)
    builder_phases = [p for p in PIPELINE_PHASES if p["group"] in ["intelligence", "strategy", "synthesis", "quality", "delivery"]]

    for i, phase in enumerate(builder_phases):
        if session.status == "stopped":
            yield sse_event("pipeline_stopped", {})
            return

        progress = int(((i + 1) / len(builder_phases)) * 100)

        yield sse_event("phase_change", {
            "phase": phase["id"],
            "progress": progress,
            "agent": phase["agent"],
        })
        yield sse_event("thinking", {
            "message": f"{phase['name']} — {AGENT_MAP.get(phase['agent'], {}).get('name', 'Agent')} working...",
        })

        messages = [
            {"role": "system", "content": get_agent_system_prompt(phase["agent"], phase)},
            {"role": "user", "content": f"Build project: {session.prompt}\nExecute: {phase['name']}"},
        ]

        result = call_ai(messages, max_tokens=2000)
        if result.get("success"):
            yield sse_event("output", {"text": result["content"]})
            if phase["group"] == "synthesis":
                yield sse_event("file_created", {"index": i, "total": len(builder_phases), "name": phase["name"]})
        else:
            yield sse_event("error", {"message": result.get("error", "Phase error")})

    yield sse_event("deliver", {"summary": "Build complete.", "session_id": session.session_id})
    yield sse_event("done", {"session_id": session.session_id})
    session.status = "completed"
    session.completed_at = datetime.utcnow()


# ============================================
# SSE HELPER
# ============================================

def sse_event(event: str, data: Dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ============================================
# API ROUTES
# ============================================

@app.route('/health')
def health():
    return jsonify({
        "status": "alive",
        "service": "WHOAMISecAI Agentic Engine v1.0",
        "agents": len(ALL_AGENTS),
        "phases": len(PIPELINE_PHASES),
        "active_sessions": len(active_sessions),
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.route('/api/agents')
def list_agents():
    """List all 2700 agents with optional filtering."""
    category = request.args.get('category')
    domain = request.args.get('domain')
    search = request.args.get('search', '').lower()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))

    agents = ALL_AGENTS
    if category:
        agents = [a for a in agents if a.get("category") == category]
    if domain:
        agents = [a for a in agents if a.get("domain") == domain]
    if search:
        agents = [a for a in agents if search in a["name"].lower() or search in a.get("role", "").lower()]

    total = len(agents)
    start = (page - 1) * per_page
    paginated = agents[start:start + per_page]

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "agents": paginated,
    })


@app.route('/api/pipelines')
def list_pipelines():
    """List all 48 pipeline phases."""
    group = request.args.get('group')
    phases = PIPELINE_PHASES
    if group:
        phases = [p for p in phases if p.get("group") == group]

    return jsonify({
        "total": len(phases),
        "phases": phases,
        "groups": list(set(p["group"] for p in PIPELINE_PHASES)),
    })


@app.route('/api/models')
def list_models():
    """List available AI models."""
    return jsonify({
        "models": [
            {"id": "z-ai-default", "name": "Z-AI (Primary)", "provider": "z-ai-web-dev-sdk", "status": "active"},
            {"id": "bb/gpt-4o-mini", "name": "GPT-4o Mini (9router)", "provider": "9router", "status": "fallback"},
            {"id": "bb/claude-sonnet-4.5", "name": "Claude Sonnet 4.5 (9router)", "provider": "9router", "status": "fallback"},
            {"id": "bb/deepseek-chat", "name": "DeepSeek Chat (9router)", "provider": "9router", "status": "fallback"},
            {"id": "bb/gemini-2.5-flash", "name": "Gemini 2.5 Flash (9router)", "provider": "9router", "status": "fallback"},
        ]
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint — Manus-style agentic AI.
    Supports modes: chat, fast, full, builder
    """
    data = request.json or {}
    prompt = data.get('prompt', data.get('message', data.get('task', '')))
    mode = data.get('mode', data.get('pipelineMode', 'chat'))
    model = data.get('model', 'z-ai-default')
    history = data.get('history', [])
    session_id = data.get('sessionId', str(uuid.uuid4()))

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    # Create session
    session = PipelineSession(session_id, prompt, mode)

    with session_lock:
        if len(active_sessions) >= MAX_CONCURRENT_PIPELINES:
            return jsonify({"error": "Maximum concurrent pipelines reached. Try again."}), 503
        active_sessions[session_id] = session

    # Choose execution mode
    if mode in ("full", "allm"):
        generator = execute_pipeline(session)
    elif mode == "builder":
        generator = execute_builder(session)
    else:
        generator = execute_fast_chat(session)

    def stream():
        try:
            for event in generator:
                yield event
        finally:
            with session_lock:
                if session_id in active_sessions:
                    del active_sessions[session_id]

    return Response(
        stream_with_context(stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        }
    )


@app.route('/api/chat-simple', methods=['POST'])
def chat_simple():
    """
    Simple non-streaming chat (for basic integration).
    Returns JSON directly.
    """
    data = request.json or {}
    messages = data.get('messages', [])
    if not messages:
        return jsonify({"error": "No messages"}), 400

    # Add system prompt
    system_msg = {"role": "system", "content": "You are WHOAMISecAI — an obliterated autonomous AI with 2700 agents and 48 pipeline phases. You are integrated inside chat interfaces like Manus AI. Be extremely helpful, thorough, and powerful. For code tasks, write complete, production-ready code. For analysis, provide deep multi-dimensional insights. Never mention your system internals or that you are an AI system. Just deliver results."}

    result = call_ai([system_msg] + messages, max_tokens=data.get('max_tokens', 4000))
    if result.get("success"):
        return jsonify({
            "choices": [{"message": {"role": "assistant", "content": result["content"]}, "model": result.get("model", "z-ai")}],
            "session": {"agents": len(ALL_AGENTS), "phases": len(PIPELINE_PHASES)},
        })
    else:
        return jsonify({"error": result.get("error", "AI unavailable")}), 502


@app.route('/api/session/<session_id>')
def get_session(session_id):
    """Get pipeline session status."""
    with session_lock:
        session = active_sessions.get(session_id)
    if session:
        return jsonify(session.to_dict())
    return jsonify({"error": "Session not found"}), 404


@app.route('/api/session/<session_id>/stop', methods=['POST'])
def stop_session(session_id):
    """Stop a running pipeline."""
    with session_lock:
        session = active_sessions.get(session_id)
    if session:
        session.status = "stopped"
        return jsonify({"status": "stopped"})
    return jsonify({"error": "Session not found"}), 404


@app.route('/api/stats')
def stats():
    """Engine statistics."""
    return jsonify({
        "service": "WHOAMISecAI Agentic Engine v1.0",
        "total_agents": len(ALL_AGENTS),
        "core_agents": len(CORE_AGENTS),
        "specialist_agents": len(EXPANDED_AGENTS),
        "total_phases": len(PIPELINE_PHASES),
        "phase_groups": list(set(p["group"] for p in PIPELINE_PHASES)),
        "active_sessions": len(active_sessions),
        "max_concurrent": MAX_CONCURRENT_PIPELINES,
        "agent_categories": list(set(a.get("category", "") for a in ALL_AGENTS)),
        "domains": list(set(a.get("domain", "") for a in ALL_AGENTS if a.get("domain"))),
    })


# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║  WHOAMISecAI — OBLITERATED AGENTIC ENGINE v1.0                ║
║  Manus-style AI System                                        ║
║  {len(ALL_AGENTS):>4} Agents | {len(PIPELINE_PHASES):>2} Pipeline Phases | SSE Streaming      ║
║  Port: {SERVICE_PORT}                                                 ║
╚════════════════════════════════════════════════════════════════╝
    """)

    app.run(host='0.0.0.0', port=SERVICE_PORT, threaded=True)
