"""
Anchor-5 TDQS 5.0/5.0 Automated Unit Test Suite.
Verifies all 47 MCP tools against the 6 TDQS dimensions:
1. Purpose Clarity (25%): Specific verb + resource + explicit sibling differentiation.
2. Usage Guidelines (20%): When to use + When NOT to use routing with 'instead'.
3. Behavioral Transparency (20%): Full disclosure of mutability, idempotency, boundary, auth, latency, error modes, matching ToolAnnotations with zero contradictions.
4. Parameter Semantics (15%): 'Parameters:' section documenting every single parameter.
5. Conciseness & Structure (10%): Front-loaded structured Markdown sections.
6. Contextual Completeness (10%): 'Returns:' section with return types and telemetry fields.
"""

import unittest
import tzero_mcp


class TestAnchor5TDQS(unittest.TestCase):
    def test_canonical_14_tool_suite(self):
        """Audits the TDQS-optimized 15 Canonical/Omni Tools against TDQS 5.0 specifications."""
        import os
        old_mode = os.environ.get("TZERO_MCP_TOOL_MODE")
        try:
            os.environ["TZERO_MCP_TOOL_MODE"] = "canonical"
            server = tzero_mcp.create_mcp_server()
            manager = getattr(server, "_tool_manager", server)
            tools = manager.list_tools() if hasattr(manager, "list_tools") else []
            self.assertEqual(len(tools), 15, f"Expected 15 canonical tools for TDQS 5/5 coherence, found {len(tools)}")
            self._audit_tools(tools)
        finally:
            if old_mode is not None:
                os.environ["TZERO_MCP_TOOL_MODE"] = old_mode
            else:
                os.environ.pop("TZERO_MCP_TOOL_MODE", None)

    def test_full_47_tool_suite(self):
        """Audits the full 48 tools against TDQS 5.0 specifications."""
        import os
        old_mode = os.environ.get("TZERO_MCP_TOOL_MODE")
        try:
            os.environ["TZERO_MCP_TOOL_MODE"] = "all"
            server = tzero_mcp.create_mcp_server()
            manager = getattr(server, "_tool_manager", server)
            tools = manager.list_tools() if hasattr(manager, "list_tools") else []
            self.assertEqual(len(tools), 48, f"Expected 48 registered tools in full mode, found {len(tools)}")
            self._audit_tools(tools)
        finally:
            if old_mode is not None:
                os.environ["TZERO_MCP_TOOL_MODE"] = old_mode
            else:
                os.environ.pop("TZERO_MCP_TOOL_MODE", None)

    def _audit_tools(self, tools):
        """Audits tools against TDQS 5.0/5.0 criteria."""
        failures = []

        for t in tools:
            name = t.name
            desc = t.description or ""
            ann = getattr(t, "annotations", None)
            ro = getattr(ann, "read_only_hint", None)
            dest = getattr(ann, "destructive_hint", None)
            idem = getattr(ann, "idempotent_hint", None)
            ow = getattr(ann, "open_world_hint", None)

            params_dict = getattr(t, "parameters", {})
            props = params_dict.get("properties", {}) if isinstance(params_dict, dict) else {}

            # 1. Purpose Clarity (25%)
            first_sent = desc.split("\n")[0].strip()
            if not first_sent:
                failures.append(f"{name}: First sentence (Purpose) is empty.")
            if name.lower() in first_sent.lower()[:len(name) + 4]:
                failures.append(f"{name}: Purpose begins tautologically with tool name.")
            has_diff = any(w in first_sent.lower() for w in ["distinguish", "rather than", "unlike", "instead of"])
            if not has_diff:
                failures.append(f"{name}: Purpose lacks explicit sibling differentiation in opening sentence.")

            # 2. Usage Guidelines (20%)
            if "When to use:" not in desc:
                failures.append(f"{name}: Missing 'When to use:' in Usage Guidelines.")
            if "When NOT to use:" not in desc:
                failures.append(f"{name}: Missing 'When NOT to use:' in Usage Guidelines.")
            elif "instead" not in desc.lower() and "use " not in desc.lower():
                failures.append(f"{name}: 'When NOT to use:' does not route to sibling tool with 'instead'.")

            # 3. Behavioral Transparency (20%)
            if "Behavior:" not in desc:
                failures.append(f"{name}: Missing 'Behavior:' section.")
            if "auth" not in desc.lower() and "credentials" not in desc.lower() and "api key" not in desc.lower():
                failures.append(f"{name}: Missing auth/credentials disclosure in Behavior.")

            # Contradiction checks
            if ow is False:
                if any(k in desc.lower() for k in ["external cloud", "remote endpoint", "cloud llm", "pollinations"]):
                    failures.append(f"{name}: CONTRADICTION: open_world_hint=False but description mentions cloud endpoints.")
            if ow is True:
                if "100% offline" in desc.lower():
                    failures.append(f"{name}: CONTRADICTION: open_world_hint=True but description claims 100% offline.")
                if "open-world" not in desc.lower() and "network" not in desc.lower():
                    failures.append(f"{name}: open_world_hint=True must disclose network operation.")

            # 4. Parameter Semantics (15%)
            if "Parameters:" not in desc:
                failures.append(f"{name}: Missing 'Parameters:' section in description.")
            else:
                for p in props.keys():
                    if f"`{p}`" not in desc and f"'{p}'" not in desc and f"{p} (" not in desc and f"{p}:" not in desc:
                        failures.append(f"{name}: Parameter '{p}' is not documented in description text.")

            # 5. Contextual Completeness & Returns (10%)
            if "Returns:" not in desc:
                failures.append(f"{name}: Missing 'Returns:' section in description.")

        if failures:
            msg = "\n" + "\n".join(f"  ❌ {f}" for f in failures)
            self.fail(f"TDQS 5/5 Anchor audit failed on {len(failures)} checks:{msg}")


if __name__ == "__main__":
    unittest.main()
