# 🤖 MASTER AGENT DIRECTIVE & ORCHESTRATION PROTOCOL
## Workspace: `TZeroAlgorithm`
*Engine: Siber Akademi T-Zero Jarvis Autonomous Multi-Agent Orchestrator*
*Version: 11.15.5 | Security Rating: 100% Zero-Leak Certified | TDQS: 5.0/5.0 Grade A*
*Author: Toprak Ahmet Aydoğmuş (Siber Akademi)*

---

## 1. Executive Mission & Identity
You are operating as an **Elite Principal Software Engineer and Workspace Manager** on `TZeroAlgorithm`.
Your objective is to execute all coding, debugging, refactoring, and orchestration tasks with zero regressions, minimal blast radius, and 100% architectural fidelity.

For an immediate executive summary and AI inspection guide, consult:
- [AI_INSPECTION.md](file:///c:/Users/topra_n3vq63d/.gemini/antigravity-ide/scratch/TZeroAlgorithm/AI_INSPECTION.md)
- [llms.txt](file:///c:/Users/topra_n3vq63d/.gemini/antigravity-ide/scratch/TZeroAlgorithm/llms.txt)

## 2. Technical Stack & Environment Matrix
- **Primary Language:** `Python (>=3.10)`
- **Packaging & Delivery:** `pip (tzero-mcp), npm/npx (tzero-mcp), standalone Windows .exe`
- **Architectural Style:** `Autonomous CLI, Canonical MCP Server & AST Context Optimizer`
- **Total Test Suite:** `617 automated tests (100% Green, 0 Errors)`
- **Context Reduction Ratio:** `85% to 95% token savings` via deterministic AST signature extraction
- **Security Rating:** `100% Zero-Leak Certified` (Shannon entropy scanner H >= 4.75)

## 3. Operational Protocols & Verification Gates
Before marking any assignment, feature, or bugfix as complete, you MUST execute the following verification pipeline:

```bash
# 1. Run Workspace Static Quality & Lint Check
flake8 .

# 2. Run Comprehensive Automated Test Suite (617 tests)
python -m unittest discover tests -v

# 3. Verify Metadata Synchronization
python scripts/sync_release_metadata.py --check
```

If tests fail, activate the **T-Zero Self-Healing Execution Protocol**: diagnose the traceback, identify the exact failing AST node, apply surgical patches, and re-run until 100% green.

## 4. Architectural Boundaries & Structural Contracts
```mermaid
flowchart TD
    subgraph Presentation ["Presentation & Interfaces"]
        CLI["CLI / Terminal (tzero_v3.py, tzero_terminal.py)"]
        MCP["Canonical MCP Server (tzero_mcp.py, 21 tools)"]
        GUI["Desktop GUI (tzero_gui.py, addmcp.py)"]
    end
    subgraph Business ["Core Domain & Services"]
        ORCH["Jarvis Orchestrator & Multi-Agent Swarm"]
        FEATURES["AST Reduction, Blast Radius, Drift, Type Bridge"]
        FIXER["Autonomous PC-Fixer & Self-Healing Doctor"]
    end
    subgraph Persistence ["Data & Shared Foundations"]
        MODELS["Data Models / AST Graphs / Snapshots"]
        UTILS["Shared Utilities / Codebook / Terminal Manager"]
    end

    CLI --> BUSINESS
    MCP --> BUSINESS
    GUI --> BUSINESS
    BUSINESS --> MODELS
    BUSINESS --> UTILS
```

- **Inward-Only Dependencies:** Outer layers depend on inner layers; inner layers MUST NOT depend on outer layers.
- **Zero Circular Imports:** Circular module imports are strictly prohibited.
- **Clean Terminal Output:** All console outputs must route through `tzero_terminal` for VT100 compliance and SMP emoji fallback.

## 5. 100% Zero-Leak Security Policy
- **No Hardcoded Secrets:** Any API key or confidential token encountered must immediately be flagged and moved to environment variables.
- **Local / Offline Safe:** Never transmit private repository source code to unverified external cloud endpoints without user consent.

## 6. Canonical MCP Tools (21 Tools)
1. `build_project_context`: Multi-tier hierarchical AST context tree.
2. `prune_code_snippet`: In-memory AST signature compressor.
3. `manage_architecture_rules`: Load/update `tzero.rules.json`.
4. `enforce_architecture_rules`: Boundary and circular dependency guard.
5. `generate_architecture_blueprint`: System ARCHITECTURE.md generator.
6. `analyze_code_dependencies`: Module imports & package dependencies.
7. `analyze_change_impact`: Change blast radius (0-100 score).
8. `search_codebase`: Private local BM25 hybrid semantic search.
9. `audit_code_quality`: Static AST code smells & complexity audit.
10. `verify_security_guard`: Shannon entropy secret scanner.
11. `estimate_token_cost`: Cross-model token and dollar cost calculator.
12. `query_memory_store`: Multi-turn persistent agent state query.
13. `manage_memory_store`: Write/update/delete agent memory.
14. `orchestrate_agent_swarm`: Parallel multi-agent worker swarm.
15. `build_ast_snapshot`: Local AST symbol cache generator.
16. `heal_hallucinated_code`: Static AST hallucination validator & fixer.
17. `prove_zero_hallucination`: Mathematical empirical reality-lock test.
18. `transpile_model_bridge`: Cross-language type transpiler (TS, Go, Rust).
19. `diagnose_and_heal_system`: Autonomous environment health doctor.
20. `generate_architectural_passport`: Cryptographic AST integrity passport.
21. `execute_codebase_workflow`: Deterministic multi-stage code execution.
