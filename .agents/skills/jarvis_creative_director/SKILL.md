---
name: jarvis_creative_director
description: >-
  Synthesizes cinematic video prompts (Sora, Kling, Runway Gen-3), ultra-photorealistic image prompts (Midjourney v6.1, Flux.1 Pro), and viral 5-scene launch video storyboards directly from codebase features and AST.
  Activate when the user asks to generate video prompts, image prompts, launch storyboards, promotional media, or types "/creative" or "/storyboard".
---

# 🎬 /creative — T-Zero Jarvis Multi-Modal Creative Director

Synthesizes high-fidelity AI video generation prompts, photorealistic visual prompts, and complete 5-scene product launch storyboards directly from source code, technical features, or system architecture.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)  
Engine: T-Zero Jarvis Multi-Modal Director v5.1.0  
License: MIT  

---

## 🚀 Capabilities

1. **Cinematic Video Generation Prompts:**
   - Engineered for **OpenAI Sora**, **Kling 1.5**, **Runway Gen-3 Alpha**, and **Luma Dream Machine**.
   - Includes precise camera trajectories (e.g. 360° orbital sweep, FPV dive, slow dolly push-in), volumetric lighting, 60fps shutter motion physics, and audio SFX cues.

2. **Ultra-Photorealistic Visual Prompts:**
   - Engineered for **Midjourney v6.1**, **Flux.1 Pro**, **Imagen 3**, and **SD 3.5**.
   - Specifies exact optical profiles (Arri Alexa, Hasselblad H6D-100c, 85mm f/1.2), color science (Kodak Portra 400), micro-textures, and command-line parameters (`--ar 16:9 --v 6.1 --style raw`).

3. **Viral 5-Scene Tech Product Launch Storyboard:**
   - **Scene 1 (00:00-00:05):** The Hook & Pain Point (Context limit exceeded, token bloat).
   - **Scene 2 (00:05-00:11):** The Paradigm Shift (T-Zero Quantum ingestion & laser pruning).
   - **Scene 3 (00:11-00:18):** Core Technology (Zero-Leak security & Immutable Reality-Lock).
   - **Scene 4 (00:18-00:25):** The Breakthrough (95% token savings & 10x ROI explosion).
   - **Scene 5 (00:25-00:30):** The Call-to-Action (`npx -y tzero-mcp@latest`).

4. **Code-to-Campaign Synthesizer:**
   - Analyzes raw AST code blocks or file paths, detects the architectural theme (Security, AI, Cloud, Database), and automatically synthesizes a matching campaign prompt suite.

---

## 🛠️ Usage

### A. Via MCP Tool (`execute_codebase_workflow`)
```json
{
  "action": "creative",
  "query": "Autonomous Cyber-Security Sentinel & Zero-Leak Shield",
  "target": "tzero/tzero_guard.py"
}
```

### B. Via Terminal CLI
```bash
# Generate campaign from technical topic
tzero creative "Sub-Millisecond Neural Vector Cache"

# Generate campaign directly from code file AST
tzero creative tzero/tzero_guard.py
```
