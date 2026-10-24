import os
import json
import tzero_mcp

os.environ["TZERO_MCP_TOOL_MODE"] = "all"
server = tzero_mcp.create_mcp_server()
manager = getattr(server, "_tool_manager", server)
tools = {t.name: t for t in manager.list_tools()}

target_tools = [
    "jarvis_consolidate_memory",
    "jarvis_hybrid_search",
    "jarvis_minhash_similarity",
    "trace_symbol_call_chain",
    "generate_smart_micro_patch",
    "jarvis_causal_chain_query",
    "jarvis_latent_press_compress",
    "compress_stream_tokens",
    "find_code_duplicity",
    "generate_architecture_blueprint",
    "generate_repo_map",
    "generate_zero_waste_prompt_context",
    "get_token_savings_metrics"
]

for name in target_tools:
    t = tools.get(name)
    if not t:
        print(f"MISSING: {name}")
        continue
    print(f"==================================================")
    print(f"TOOL: {name}")
    print(f"ANNOTATIONS: {t.annotations}")
    print(f"PARAMETERS SCHEMA:")
    print(json.dumps(t.parameters, indent=2))
    print(f"DESCRIPTION:")
    print(t.description)
    print(f"==================================================\n")
