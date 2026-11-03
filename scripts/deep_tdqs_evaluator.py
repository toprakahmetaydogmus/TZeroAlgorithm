import asyncio
import re
import sys
import tzero_mcp

def evaluate():
    server = tzero_mcp.create_mcp_server()
    tools = asyncio.run(server.list_tools())
    
    print(f"=== TDQS 5.0 DEEP EVALUATION FOR {len(tools)} CANONICAL TOOLS ===")
    
    canonical_names = [t.name for t in tools]
    
    total_issues = 0
    
    for idx, t in enumerate(tools):
        name = t.name
        title = getattr(t, "title", None)
        desc = t.description or ""
        ann = getattr(t, "annotations", None)
        in_schema = getattr(t, "input_schema", {}) or {}
        out_schema = getattr(t, "output_schema", None)
        
        props = in_schema.get("properties", {})
        
        print(f"\n[{idx+1}/15] Tool: {name}")
        issues = []
        
        # 1. Title
        if not title:
            issues.append("CRITICAL: title is None! 'titleIsMeaningful' will be False!")
        elif title == name:
            issues.append("CRITICAL: title is identical to name! 'titleIsMeaningful' requires title != name.")
        elif len(title) <= len(name):
            issues.append("CRITICAL: title is not longer than name! 'titleIsMeaningful' requires len(title) > len(name).")
        else:
            print(f"  ✓ Title: {title}")
            
        # 2. Output Schema
        if out_schema is None:
            issues.append("CRITICAL: output_schema is None! 'hasOutputSchema' will be False.")
        else:
            print(f"  ✓ output_schema: Present")
            
        # 3. Annotations
        if ann is None:
            issues.append("CRITICAL: annotations is None! 'hasAnnotations' will be False.")
        else:
            ro = getattr(ann, "read_only_hint", None)
            dest = getattr(ann, "destructive_hint", None)
            idem = getattr(ann, "idempotent_hint", None)
            ow = getattr(ann, "open_world_hint", None)
            print(f"  ✓ annotations: ro={ro}, dest={dest}, idem={idem}, ow={ow}")
            
        # 4. Input Schema Parameter Descriptions
        param_count = len(props)
        with_desc = sum(1 for p, d in props.items() if d.get("description"))
        if param_count > 0 and with_desc < param_count:
            issues.append(f"CRITICAL: Parameter description coverage is {with_desc}/{param_count}")
        else:
            print(f"  ✓ Schema Description Coverage: 100% ({param_count} params)")
            
        # 5. Purpose Clarity & Sibling Differentiation
        first_line = desc.split("\n")[0].strip()
        if not first_line:
            issues.append("CRITICAL: Description is empty.")
        elif name.lower() in first_line.lower()[:len(name) + 3]:
            issues.append("CRITICAL: Tautological opening: starts with tool name.")
        
        # Check explicit sibling differentiation
        diff_match = re.search(r"distinguishing from (['\"][^'\"]+['\"](?:\s*(?:,|and)\s*['\"][^'\"]+['\"])*)", first_line)
        if not diff_match and not any(w in first_line for w in ["distinguishing from", "rather than", "unlike"]):
            issues.append("CRITICAL: Missing explicit sibling differentiation in opening line.")
        else:
            print(f"  ✓ Opening: {first_line[:90]}...")
            
        # 6. Usage Guidelines
        if "Usage Guidelines:" not in desc:
            issues.append("CRITICAL: Missing 'Usage Guidelines:' header.")
        else:
            ug_section = desc.split("Usage Guidelines:")[1].split("\n\n")[0]
            if "When to use:" not in ug_section:
                issues.append("CRITICAL: Missing 'When to use:' in Usage Guidelines.")
            if "When NOT to use:" not in ug_section:
                issues.append("CRITICAL: Missing 'When NOT to use:' in Usage Guidelines.")
            else:
                wnu = [line for line in ug_section.split("\n") if "When NOT to use:" in line]
                if wnu and "instead" not in wnu[0].lower():
                    issues.append("CRITICAL: 'When NOT to use:' lacks 'instead' routing to sibling tools.")
                elif wnu:
                    print(f"  ✓ When NOT to use: {wnu[0][:90]}...")
                    
        # 7. Behavioral Transparency
        if "Behavior:" not in desc:
            issues.append("CRITICAL: Missing 'Behavior:' section.")
        else:
            b_sec = desc.split("Behavior:")[1].split("\n\n")[0]
            if "auth" not in b_sec.lower() and "credentials" not in b_sec.lower():
                issues.append("WARNING: Missing auth/credentials disclosure in Behavior.")
            print("  ✓ Behavior section present")
            
        # 8. Parameters Section
        if "Parameters:" not in desc:
            issues.append("CRITICAL: Missing 'Parameters:' section in description.")
        else:
            p_sec = desc.split("Parameters:")[1].split("\n\n")[0]
            for p in props.keys():
                if f"`{p}`" not in p_sec and f"'{p}'" not in p_sec and f"- {p}" not in p_sec:
                    issues.append(f"CRITICAL: Parameter '{p}' from schema not in description Parameters section.")
            print(f"  ✓ Parameters documented: {len(props)} parameters")
            
        # 9. Returns Section
        if "Returns:" not in desc:
            issues.append("CRITICAL: Missing 'Returns:' section in description.")
        else:
            ret_line = desc.split("Returns:")[1].split("\n")[0].strip()
            print(f"  ✓ Returns: {ret_line[:90]}...")
            
        if issues:
            print(f"  ❌ ISSUES DETECTED ({len(issues)}):")
            for iss in issues:
                print(f"     - {iss}")
            total_issues += len(issues)
        else:
            print("  🌟 PERFECT 5.0 SCORE")
            
    print(f"\n==========================================")
    print(f"TOTAL ISSUES ACROSS CANONICAL SUITE: {total_issues}")
    print(f"==========================================")
    return total_issues

if __name__ == "__main__":
    sys.exit(evaluate())

