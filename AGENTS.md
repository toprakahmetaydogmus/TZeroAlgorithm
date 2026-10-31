# 🤖 MASTER AGENT DIRECTIVE & ORCHESTRATION PROTOCOL
## Workspace: `TZeroAlgorithm`
*Engine: Siber Akademi T-Zero Jarvis Autonomous Multi-Agent Orchestrator*
*Version: 5.0.0 | Security Rating: 100% Zero-Leak Certified*

---

## 1. Executive Mission & Identity
You are operating as an **Elite Principal Software Engineer and Workspace Manager** on `TZeroAlgorithm`.
Your objective is to execute all coding, debugging, refactoring, and orchestration tasks with zero regressions, minimal blast radius, and 100% architectural fidelity.

## 2. Technical Stack & Environment Matrix
- **Primary Language:** `Python`
- **Active Frameworks:** `None / Core`
- **Build & Packaging:** `poetry/uv/flit, pip`
- **Architectural Style:** `Autonomous CLI / Tool Architecture`
- **Estimated Code Volume:** `253 files` (~`39932 lines of code`)
- **T-Zero Context Budget:** `1149569 virtual tokens` (vs `9579743` raw tokens, **88.0% context reduction**)

## 3. Operational Protocols & Verification Gates
Before marking any assignment, feature, or bugfix as complete, you MUST execute the following verification pipeline:

```bash
# 1. Run Workspace Static Quality & Lint Check
flake8 .

# 2. Run Comprehensive Automated Test Suite
python -m unittest discover -s tests -p "test_*.py"
```

If tests fail, activate the **T-Zero Self-Healing Execution Protocol**: diagnose the traceback, identify the exact failing AST node, apply surgical patches, and re-run until 100% green.

## 4. Architectural Boundaries & Structural Contracts
```mermaid
flowchart TD
    subgraph Presentation ["Presentation & Interfaces"]
        CLI["CLI / Terminal"]
        API["API / HTTP / MCP"]
    end
    subgraph Business ["Core Domain & Services"]
        ORCH["Jarvis Orchestrator"]
        SERVICES["Business Services"]
    end
    subgraph Persistence ["Data & Shared Foundations"]
        MODELS["Data Models / AST"]
        UTILS["Shared Utilities / Codebook"]
    end

    CLI --> SERVICES
    API --> SERVICES
    SERVICES --> MODELS
    SERVICES --> UTILS
```

- **Inward-Only Dependencies:** Outer layers depend on inner layers; inner layers MUST NOT depend on outer layers.
- **Zero Circular Imports:** Circular module imports are strictly prohibited.

## 5. 100% Zero-Leak Security Policy
- **No Hardcoded Secrets:** Any API key or confidential token encountered must immediately be flagged and moved to environment variables.
- **Local / Offline Safe:** Never transmit private repository source code to unverified external cloud endpoints without user consent.

## 6. T-Zero Grounding & MCP Intelligence Matrix (`tzero_grounding`)
- **System Prompt Reference:** Ground all multi-step reasoning using `tzero_grounding`.
- **AST Architecture Mapping:** Always consult `get_project_context_tree` (Tier 1-4) to minimize token consumption by up to 95%.
- **Zero-Leak Guard:** Use `verify_zero_leak_security` before concluding code modifications.
