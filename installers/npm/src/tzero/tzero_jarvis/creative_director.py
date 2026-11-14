# -*- coding: utf-8 -*-
"""
T-ZERO JARVIS MULTI-MODAL CREATIVE DIRECTOR & PROMPT ENGINE
------------------------------------------------------------
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 5.1.0 | License: MIT

Autonomous creative director that synthesizes ultra-photorealistic image prompts
(Midjourney v6.1, Flux.1 Pro, Imagen 3) and cinematic video generation prompts
(OpenAI Sora, Kling 1.5, Runway Gen-3 Alpha, Luma Dream Machine), as well as
viral 5-scene tech product launch storyboards directly from source code and AST.
"""

from __future__ import annotations

import os
import re
import ast
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class VideoPromptSpec:
    tool: str
    prompt: str
    negative_prompt: str
    camera_movement: str
    lighting: str
    fps: int
    aspect_ratio: str
    duration_seconds: int
    audio_sfx_cue: str


@dataclass
class PhotoPromptSpec:
    engine: str
    prompt: str
    negative_prompt: str
    camera_lens: str
    lighting_setup: str
    color_grade: str
    aspect_ratio: str
    parameters: str


@dataclass
class StoryboardScene:
    scene_number: int
    timecode: str
    scene_title: str
    visual_description: str
    camera_direction: str
    voiceover_script: str
    on_screen_text: str
    audio_sfx: str
    video_prompt: str


class JarvisCreativeDirector:
    """Enterprise multi-modal prompt synthesis and storyboard director."""

    LENS_PROFILES = {
        "cinematic": "Arri Alexa Mini LF, 35mm Cooke Anamorphic /i Prime f/2.0, shallow depth of field, anamorphic oval bokeh",
        "portrait": "Hasselblad H6D-100c, HC 100mm f/2.2, natural skin texture, subsurface scattering, catchlight in eyes",
        "macro": "Canon EOS R5, Canon RF 100mm f/2.8L Macro IS USM, 1.4x magnification, razor-sharp micro details",
        "architectural": "Sony A7R V, Sony FE 16-35mm f/2.8 GM II, architectural perspective correction, rectilinear sharpness",
        "cyberpunk": "RED V-Raptor 8K VV, Zeiss Master Prime 50mm T1.3, blue streak anamorphic flares, diffused volumetric neon glow"
    }

    LIGHTING_PROFILES = {
        "golden_hour": "Warm low-angle sun, long dramatic shadows, atmospheric golden haze, volumetric god rays",
        "cybernetic_neon": "Bioluminescent cyan and electric violet rim lighting, high-contrast dark environment, diffused reflection",
        "studio_high_key": "Clean 3-point softbox lighting, 5600K daylight balanced, crisp white reflections, zero harsh shadows",
        "dramatic_noir": "Chiaroscuro, single key rim light, deep crushing blacks, haze and dust motes illuminated in beams",
        "tech_cleanroom": "Recessed linear LED ceiling panels, sterile cool 6500K diffuse illumination, polished floor reflections"
    }

    CAMERA_MOTIONS = [
        "Slow cinematic push-in (dolly track) accelerating into a hyper-dynamic tracking shot",
        "360-degree orbital sweep around the subject with subtle vertigo Zolly focal zoom",
        "Smooth low-altitude FPV drone flythrough skimming millimetres above the surface",
        "Top-down 90-degree crane drop transitioning to eye-level heroic reveal",
        "Handheld cinema verite with subtle organic camera shake and whip-pan transition"
    ]

    @classmethod
    def generate_video_prompt(
        cls,
        topic: str,
        style: str = "cinematic",
        duration: int = 5,
        camera_work: Optional[str] = None,
        lighting: Optional[str] = None,
        audio_mood: Optional[str] = None
    ) -> VideoPromptSpec:
        """Synthesize high-fidelity prompt for Sora, Kling, Runway Gen-3, Luma."""
        chosen_camera = camera_work or cls.CAMERA_MOTIONS[0]
        chosen_light = lighting or cls.LIGHTING_PROFILES.get(style, cls.LIGHTING_PROFILES["cybernetic_neon"] if "cyber" in style else cls.LIGHTING_PROFILES["golden_hour"])
        sfx = audio_mood or "Sub-bass riser crescendo with futuristic mechanical servo clicks and ambient stereo synthesizer"

        # Build prompt
        prompt_parts = [
            f"Cinematic 8K masterpiece video of {topic}.",
            f"Visual Dynamics: Hyper-detailed, realistic motion physics, photorealistic rendering with 60fps shutter motion blur.",
            f"Camera Direction: {chosen_camera}.",
            f"Lighting & Atmosphere: {chosen_light}.",
            f"Color & Tone: 35mm film grain, cinematic Kodak Vision3 500T color grading, HDR 10-bit wide color gamut.",
            f"No jitter, no morphing artifacts, seamless fluid transitions, professional movie cinematography."
        ]
        full_prompt = " ".join(prompt_parts)

        negative = "low quality, blurry, deformed, morphing, glitchy, oversaturated, amateur video, watermark, text overlay, stuttering frames"

        return VideoPromptSpec(
            tool="Sora / Kling 1.5 / Runway Gen-3 / Luma Dream Machine",
            prompt=full_prompt,
            negative_prompt=negative,
            camera_movement=chosen_camera,
            lighting=chosen_light,
            fps=60,
            aspect_ratio="16:9",
            duration_seconds=duration,
            audio_sfx_cue=sfx
        )

    @classmethod
    def generate_photo_prompt(
        cls,
        subject: str,
        style: str = "portrait",
        lens_type: str = "cinematic",
        lighting_style: str = "golden_hour",
        aspect_ratio: str = "16:9",
        negative_extra: str = ""
    ) -> PhotoPromptSpec:
        """Synthesize ultra-photorealistic image generation prompt for Midjourney v6.1 / Flux.1."""
        lens = cls.LENS_PROFILES.get(lens_type, cls.LENS_PROFILES["cinematic"])
        lighting = cls.LIGHTING_PROFILES.get(lighting_style, cls.LIGHTING_PROFILES["golden_hour"])

        prompt_core = (
            f"Award-winning editorial photograph of {subject}. "
            f"Captured with {lens}. "
            f"Lighting: {lighting}. "
            f"Hyper-detailed textures, ray-traced reflections, authentic skin and material pores, natural chromatic dispersion. "
            f"Masterpiece composition, Vogue / National Geographic award winner, shot on 35mm film, uncompressed RAW capture."
        )

        neg = "cgi, 3d render, plastic skin, anime, illustration, bad anatomy, deformed limbs, blurry, low resolution, watermark, signature"
        if negative_extra:
            neg += f", {negative_extra}"

        params = f"--ar {aspect_ratio} --v 6.1 --style raw --stylize 250"

        return PhotoPromptSpec(
            engine="Midjourney v6.1 / Flux.1 Pro / Imagen 3",
            prompt=prompt_core,
            negative_prompt=neg,
            camera_lens=lens,
            lighting_setup=lighting,
            color_grade="Kodak Portra 400 Color Science",
            aspect_ratio=aspect_ratio,
            parameters=params
        )

    @classmethod
    def generate_launch_storyboard(
        cls,
        product_name: str,
        core_feature: str,
        metric_highlight: str = "95% Token Reduction & 0 Hallucinations",
        target_audience: str = "AI Engineers, Tech Leads & DevOps"
    ) -> List[StoryboardScene]:
        """Creates a viral 5-scene 30-second tech launch video storyboard."""
        scenes = [
            StoryboardScene(
                scene_number=1,
                timecode="00:00 - 00:05",
                scene_title="The Hook: Context Window Overload",
                visual_description="A frustrated AI developer at a futuristic multi-monitor battlestation. Red warning alerts flash: 'CONTEXT LIMIT EXCEEDED - 100K TOKENS WASTED'. Holographic code flies chaotically out of control.",
                camera_direction="Fast macro zoom onto the developer's intense eyes reflecting red code cascades, camera pans back violently.",
                voiceover_script="Your AI agents are choking on bloated codebases, burning millions of tokens and hallucinating fake functions.",
                on_screen_text="STOP WASTING TOKENS",
                audio_sfx="Heavy low-pass glitch beat, distorted digital alarm, sub-bass drop.",
                video_prompt="Cinematic shot of dark neon office, developer facing glowing red holographic terminals flashing 'ERROR', camera fast zoom into eyes, 8k, photorealistic, anamorphic lens flare."
            ),
            StoryboardScene(
                scene_number=2,
                timecode="00:05 - 00:11",
                scene_title="The Paradigm Shift: T-Zero Ingestion",
                visual_description=f"A sleek metallic cube engraved with the glowing cyan '{product_name}' logo activates. Laser scanning beams pulse across the messy code forest, pruning 95% of fluff instantly into pure crystal AST signatures.",
                camera_direction="Dynamic 360-degree orbital sweep around the glowing T-Zero core as shockwave ripples outward.",
                voiceover_script=f"Meet {product_name}: The world's first deterministic AST context compressor and reality-lock engine.",
                on_screen_text=f"ENTER {product_name.upper()}",
                audio_sfx="Futuristic laser initialization sweep, high-frequency crystal resonance, metallic lock-in click.",
                video_prompt=f"Futuristic dark studio, glowing cyan quantum cube labeled '{product_name}' emitting coherent blue laser lattice, compressing chaotic code into crystal lattices, cinematic, 60fps."
            ),
            StoryboardScene(
                scene_number=3,
                timecode="00:11 - 00:18",
                scene_title="The Core Tech: Zero-Leak & Reality-Lock",
                visual_description="Split holographic HUD. Left side: Zero-Leak Security Shield scanning secrets in real time. Right side: Immutable AST Grounding Contract locking Claude, Cursor, and ChatGPT into zero-hallucination reality.",
                camera_direction="Split-screen horizontal slide tracking forward with volumetric light beams between the two panels.",
                voiceover_script="Pre-flight reality locks guarantee zero hallucinations before writing code, backed by 100% Zero-Leak security.",
                on_screen_text="100% REALITY-LOCK | ZERO LEAK",
                audio_sfx="Crisp mechanical shutter snaps, data transfer swooshes, positive validation chord.",
                video_prompt="Holographic cybernetic dashboard floating in mid-air displaying green checkmarks, AST hierarchy tree glowing neon green, cinematic depth of field, high-tech interface, 8k."
            ),
            StoryboardScene(
                scene_number=4,
                timecode="00:18 - 00:25",
                scene_title="The Breakthrough: Provable ROI & Speed",
                visual_description=f"A vibrant 3D holographic telemetry graph explodes with stats: '{metric_highlight}', 10x faster inference, $0 API cost on local engine. Millions of raw tokens shrink to compact gold AST tokens.",
                camera_direction="Ascending crane shot rising above the metric towers, lens catching golden volumetric light flare.",
                voiceover_script="Cut context window costs by up to 95%, speed up agent loops by 10x, and keep your intellectual property offline.",
                on_screen_text=f"PROVEN: {metric_highlight.upper()}",
                audio_sfx="Uplifting electronic synthesizer build-up, punchy acoustic kick, crowd whisper.",
                video_prompt="Glowing golden bar charts and telemetry data rising from dark reflective glass floor, numbers counting up rapidly, cinematic cinematic lighting, golden hour rays, 8k."
            ),
            StoryboardScene(
                scene_number=5,
                timecode="00:25 - 00:30",
                scene_title="Call to Action: Launch with T-Zero",
                visual_description=f"Heroic lockup of '{product_name}' logo, URL, and VS Code / Cursor / Windsurf / Antigravity integration icons. A single terminal command glows: 'npx -y tzero-mcp@latest'.",
                camera_direction="Gentle slow push-in, fading smoothly to solid obsidian background with subtle particle aura.",
                voiceover_script=f"Transform your autonomous AI coding stack today. Install {product_name} in 30 seconds.",
                on_screen_text=f"npx -y {product_name.lower()}-mcp@latest\ngithub.com/toprakahmetaydogmus/TZeroAlgorithm",
                audio_sfx="Subwoofer final hit, pristine chime decay, silence.",
                video_prompt=f"Minimalist luxury tech reveal, glowing cyan '{product_name}' logo on matte titanium surface, soft ambient studio lighting, clean terminal prompt, 8k resolution."
            )
        ]
        return scenes

    @classmethod
    def synthesize_from_code(cls, code: str, file_name: str = "module.py") -> Dict[str, Any]:
        """Analyzes code AST and synthesizes matched video and photo campaign prompts."""
        symbols = []
        docstrings = []
        is_security = False
        is_ai = False
        is_db = False

        code_lower = code.lower()
        if any(w in code_lower for w in ["token", "compress", "ast", "prompt", "llm"]):
            is_ai = True
        if any(w in code_lower for w in ["secret", "leak", "security", "guard", "crypto", "auth"]):
            is_security = True
        if any(w in code_lower for w in ["db", "sqlite", "cache", "store", "query", "sql"]):
            is_db = True

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    symbols.append(node.name)
                    doc = ast.get_docstring(node)
                    if doc:
                        docstrings.append(doc.splitlines()[0])
        except Exception:
            symbols = [line.strip().split()[1] for line in code.splitlines() if line.strip().startswith(("def ", "class "))]

        # Determine theme
        if is_security:
            theme = "Autonomous Cyber-Security Sentinel & Zero-Leak Shield"
            style = "cyberpunk"
            lighting = "cybernetic_neon"
        elif is_ai:
            theme = "Quantum AST Compression Engine & Neural Token Optimizer"
            style = "cinematic"
            lighting = "golden_hour"
        elif is_db:
            theme = "Sub-Millisecond High-Throughput Data Backbone"
            style = "architectural"
            lighting = "tech_cleanroom"
        else:
            theme = f"Elite Developer Utility Architecture ({file_name})"
            style = "cinematic"
            lighting = "golden_hour"

        top_symbols = ", ".join(symbols[:5]) if symbols else "Core Architecture"

        video_spec = cls.generate_video_prompt(
            topic=f"Future of AI computing: {theme} executing operations with symbols ({top_symbols})",
            style=style,
            lighting=cls.LIGHTING_PROFILES.get(lighting)
        )

        photo_spec = cls.generate_photo_prompt(
            subject=f"Futuristic physical AI supercomputer server processing {theme}, glowing fiber optics, titanium chassis",
            style="cinematic",
            lens_type="cinematic",
            lighting_style=lighting
        )

        storyboard = cls.generate_launch_storyboard(
            product_name="T-Zero",
            core_feature=theme,
            metric_highlight="95% Context Compression & 0 Hallucinations"
        )

        return {
            "file_name": file_name,
            "detected_theme": theme,
            "extracted_symbols": symbols[:10],
            "video_spec": {
                "engine": video_spec.tool,
                "prompt": video_spec.prompt,
                "negative_prompt": video_spec.negative_prompt,
                "camera_movement": video_spec.camera_movement,
                "audio_cue": video_spec.audio_sfx_cue
            },
            "photo_spec": {
                "engine": photo_spec.engine,
                "prompt": photo_spec.prompt,
                "negative_prompt": photo_spec.negative_prompt,
                "camera_lens": photo_spec.camera_lens,
                "parameters": photo_spec.parameters
            },
            "storyboard_scenes": [
                {
                    "scene": s.scene_number,
                    "timecode": s.timecode,
                    "title": s.scene_title,
                    "visual": s.visual_description,
                    "voiceover": s.voiceover_script,
                    "text": s.on_screen_text,
                    "prompt": s.video_prompt
                }
                for s in storyboard
            ]
        }
