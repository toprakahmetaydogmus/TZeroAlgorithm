---
name: tzero-arch
description: >-
  Generate complete system architecture specification (ARCHITECTURE.md) with live Mermaid component diagrams.
  Activate when the user types "/tzero-arch" or asks for system architecture blueprint.
---

# /tzero-arch — System Architecture Blueprint Generator

Generate an enterprise-grade architectural specification:
1. Module decomposition and layer boundaries.
2. Inter-module import topology.
3. Interactive Mermaid diagram showing system component relationships.
4. Auto-exports or updates `ARCHITECTURE.md`.

## Execution
Call the `generate_architecture_blueprint` MCP tool on the target path (default: `.`).
