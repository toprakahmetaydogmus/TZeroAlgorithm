import os
import re
import sys
import json
import tzero_mcp

def comprehensive_tdqs_audit():
    os.environ["TZERO_MCP_TOOL_MODE"] = "all"
    server = tzero_mcp.create_mcp_server()
    manager = getattr(server, "_tool_manager", server)
    tools = manager.list_tools() if hasattr(manager, "list_tools") else []
    
    print(f"Total tools to audit: {len(tools)}")
    
    issues = []
    
    for tool in tools:
        name = tool.name
        desc = tool.description or ""
        ann = getattr(tool, "annotations", None)
        params_dict = getattr(tool, "parameters", {})
        props = params_dict.get("properties", {}) if isinstance(params_dict, dict) else {}
        
        # 1. Purpose Clarity
        first_line = desc.split("\n")[0].strip()
        if not first_line:
            issues.append(f"[{name}] Purpose is empty")
        if name.lower() in first_line.lower()[:len(name) + 3]:
            issues.append(f"[{name}] Tautological opening: begins with tool name")
        if not any(w in first_line.lower() for w in ["distinguish", "rather than", "unlike", "instead of"]):
            issues.append(f"[{name}] Missing sibling differentiation in opening line")
            
        # 2. Usage Guidelines
        if "When to use:" not in desc:
            issues.append(f"[{name}] Missing 'When to use:'")
        if "When NOT to use:" not in desc:
            issues.append(f"[{name}] Missing 'When NOT to use:'")
        elif "instead" not in desc.lower() and "use " not in desc.lower():
            issues.append(f"[{name}] 'When NOT to use:' lacks 'instead' routing")
            
        # 3. Behavioral Transparency & Contradictions
        if "Behavior:" not in desc:
            issues.append(f"[{name}] Missing 'Behavior:' section")
        
        # Check destructive contradiction
        dest = getattr(ann, "destructive_hint", None)
        if dest is False:
            # Check for words like 'deletes', 'removes', 'destroys'
            for bad_word in ["deletes ", "permanently delete", "destroys "]:
                if bad_word in desc.lower():
                    issues.append(f"[{name}] CONTRADICTION: destructive_hint=False but description contains '{bad_word.strip()}'")
                    
        # Check open_world contradiction
        ow = getattr(ann, "open_world_hint", None)
        if ow is False:
            for cloud_word in ["external cloud", "remote endpoint", "pollinations.ai", "cloud llm"]:
                if cloud_word in desc.lower():
                    issues.append(f"[{name}] CONTRADICTION: open_world_hint=False but description mentions '{cloud_word}'")
        elif ow is True:
            if "100% offline" in desc.lower():
                issues.append(f"[{name}] CONTRADICTION: open_world_hint=True but claims '100% offline'")
                
        # 4. Parameters Semantics
        if "Parameters:" not in desc:
            issues.append(f"[{name}] Missing 'Parameters:' section")
        else:
            param_section = desc.split("Parameters:")[1]
            if "Behavior:" in param_section:
                param_section = param_section.split("Behavior:")[0]
            elif "Usage Guidelines:" in param_section:
                param_section = param_section.split("Usage Guidelines:")[0]
            elif "Returns:" in param_section:
                param_section = param_section.split("Returns:")[0]
                
            for p_name, p_schema in props.items():
                if f"`{p_name}`" not in param_section and f"'{p_name}'" not in param_section and f"{p_name} (" not in param_section and f"- {p_name}:" not in param_section:
                    issues.append(f"[{name}] Schema parameter '{p_name}' not documented in Parameters section")
                    
                # Check default consistency
                if "default" in p_schema:
                    schema_def = p_schema["default"]
                    # If default is boolean or int or str
                    # Let's check if the docstring mentions a contradictory default
                    if isinstance(schema_def, bool):
                        def_str = str(schema_def).lower()
                        # If docstring says default=True when schema_def is False
                        opp_str = "false" if schema_def else "true"
                        if f"default={opp_str}" in param_section.lower() or f"default: {opp_str}" in param_section.lower() or f"default='{opp_str}'" in param_section.lower():
                            issues.append(f"[{name}] Parameter '{p_name}' schema default is {schema_def} but docstring says opposite: {opp_str}")
                    elif isinstance(schema_def, int) and schema_def != 0:
                        pass
                        
        # 5. Returns section
        if "Returns:" not in desc:
            issues.append(f"[{name}] Missing 'Returns:' section")

    print("\n--- AUDIT RESULTS ---")
    if not issues:
        print("✅ PERFECT 5/5! No issues detected across all tools!")
    else:
        print(f"❌ Found {len(issues)} issues:")
        for iss in issues:
            print(f"  - {iss}")

if __name__ == "__main__":
    comprehensive_tdqs_audit()
