import os
import re
import json
import tzero_mcp

os.environ["TZERO_MCP_TOOL_MODE"] = "all"
server = tzero_mcp.create_mcp_server()
manager = getattr(server, "_tool_manager", server)
tools = manager.list_tools()

print(f"Total tools loaded: {len(tools)}")

DESTRUCTIVE_KEYWORDS = ["delete", "deletes", "deleting", "deletion", "remove", "removes", "removing", "destroy", "destroys", "purge", "purges", "wipe", "wipes"]
EXTERNAL_KEYWORDS = ["openai", "anthropic", "gpt-4", "claude-3", "external api", "third-party", "cloud api"]

issues = []

for t in tools:
    name = t.name
    desc = t.description or ""
    ann = getattr(t, "annotations", None)
    schema = getattr(t, "parameters", {}) or {}
    props = schema.get("properties", {})
    required = schema.get("required", [])

    # Check 1: Structure sections
    if "Parameters:" not in desc and props:
        issues.append(f"[{name}] Missing 'Parameters:' section in description while properties exist.")
    if "Behavior:" not in desc:
        issues.append(f"[{name}] Missing 'Behavior:' section in description.")
    if "Usage Guidelines:" not in desc:
        issues.append(f"[{name}] Missing 'Usage Guidelines:' section in description.")
    if "When to use:" not in desc:
        issues.append(f"[{name}] Missing 'When to use:' in Usage Guidelines.")
    if "When NOT to use:" not in desc:
        issues.append(f"[{name}] Missing 'When NOT to use:' in Usage Guidelines.")
    if "Returns:" not in desc:
        issues.append(f"[{name}] Missing 'Returns:' section in description.")

    # Check 2: Purpose distinguishes from siblings
    first_sentence = desc.split("\n\n")[0]
    if "distinguishing from" not in first_sentence:
        issues.append(f"[{name}] Purpose sentence lacks 'distinguishing from' sibling routing formula.")

    # Check 3: Destructive contradictions
    if ann and getattr(ann, "destructive_hint", False) is False:
        for kw in DESTRUCTIVE_KEYWORDS:
            matches = re.finditer(rf"\b{kw}\b", desc, re.IGNORECASE)
            for m in matches:
                start = max(0, m.start() - 25)
                end = min(len(desc), m.end() + 25)
                snippet = desc[start:end].replace("\n", " ")
                issues.append(f"[{name}] Contains destructive keyword '{kw}' when destructive_hint=False: '...{snippet}...'")

    # Check 4: External / open_world contradictions
    if ann and getattr(ann, "open_world_hint", False) is False:
        for kw in EXTERNAL_KEYWORDS:
            matches = re.finditer(rf"\b{kw}\b", desc, re.IGNORECASE)
            for m in matches:
                start = max(0, m.start() - 25)
                end = min(len(desc), m.end() + 25)
                snippet = desc[start:end].replace("\n", " ")
                issues.append(f"[{name}] Mentions external/cloud keyword '{kw}' when open_world_hint=False: '...{snippet}...'")

    # Check 5: Parameters consistency
    param_section_match = re.search(r"Parameters:\n(.*?)(?=\n\n|\n[A-Z]|$)", desc, re.DOTALL)
    param_lines = param_section_match.group(1).strip().split("\n") if param_section_match else []
    
    desc_param_names = set()
    for line in param_lines:
        m = re.match(r"- `([a-zA-Z0-9_]+)`", line.strip())
        if m:
            desc_param_names.add(m.group(1))

    schema_param_names = set(props.keys())

    missing_in_desc = schema_param_names - desc_param_names
    extra_in_desc = desc_param_names - schema_param_names

    if missing_in_desc:
        issues.append(f"[{name}] Schema parameter(s) missing from description: {missing_in_desc}")
    if extra_in_desc:
        issues.append(f"[{name}] Description lists parameter(s) not in schema: {extra_in_desc}")

    # Check defaults in description vs schema
    for prop_name, prop_val in props.items():
        if "default" in prop_val:
            default_val = prop_val["default"]
            for line in param_lines:
                if f"`{prop_name}`" in line:
                    # check if default is mentioned
                    if "default=" not in line.lower() and "default:" not in line.lower() and default_val is not None:
                        issues.append(f"[{name}] Parameter '{prop_name}' has schema default={repr(default_val)} but description does not state default: '{line.strip()}'")

print(f"\n--- ACCURATE AUDIT RESULTS: {len(issues)} issues found ---")
for iss in issues:
    print(iss)
