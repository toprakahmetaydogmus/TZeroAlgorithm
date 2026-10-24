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

    for prop_name, prop_val in props.items():
        is_req = prop_name in required
        p_type = prop_val.get("type", "")
        # Find matching line in param_lines
        matched_line = None
        for line in param_lines:
            if f"`{prop_name}`" in line:
                matched_line = line
                break
        
        if not matched_line:
            issues.append(f"[{name}] Parameter '{prop_name}' missing from docstring Parameters section.")
            continue
            
        # Check required/optional
        if is_req and "required" not in matched_line.lower():
            issues.append(f"[{name}] Parameter '{prop_name}' is required in schema but not marked required in docstring: '{matched_line}'")
        elif not is_req and "optional" not in matched_line.lower():
            issues.append(f"[{name}] Parameter '{prop_name}' is optional in schema but not marked optional in docstring: '{matched_line}'")

        # Check default value
        if not is_req and "default" in prop_val:
            def_val = prop_val["default"]
            # Check if default is mentioned in docstring line
            if "default=" not in matched_line.lower() and "default:" not in matched_line.lower():
                issues.append(f"[{name}] Parameter '{prop_name}' has default={repr(def_val)} in schema but no default mentioned in docstring line: '{matched_line}'")

print(f"\n--- TOTAL STRICT TDQS AUDIT FINDINGS: {len(issues)} ---")
for iss in issues:
    print(iss)
