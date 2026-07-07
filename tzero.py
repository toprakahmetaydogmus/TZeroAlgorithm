# -*- coding: utf-8 -*-
import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
import time

# Ultra-Premium Space Dark & Glassmorphic Color Palette
BG_MAIN = "#0a0d14"          # Deep cosmic space background
BG_CARD = "#111625"          # Semi-translucent dark glass card
BG_CARD_LIGHT = "#1a2238"    # Highlighted glass panel
FG_TEXT = "#e2e8f0"          # Crisp starlight white text
FG_MUTED = "#64748b"         # Nebular grey muted text
FG_ACCENT = "#00ffd8"        # Glowing neon cyan accent
FG_ACCENT_PURPLE = "#bd93f9" # Cyberpunk electric purple accent
BG_BUTTON = "#6272a4"        # Modern button bg
BG_BUTTON_HOVER = "#00ffd8"  # Neon cyan hover state
BG_SUCCESS = "#50fa7b"       # Neon green success indicator
FG_SUCCESS = BG_SUCCESS       # Alias so both names work

# Provider presets: base URL + representative model list
PROVIDER_CONFIGS = {
    "NVIDIA NIM": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "models": [
            "meta/llama-3.3-70b-instruct",
            "meta/llama-4-scout-17b-16e-instruct",
            "meta/llama-4-maverick-17b-128e-instruct",
            "deepseek-ai/deepseek-r1",
            "mistralai/mistral-large-3-675b-instruct-2512",
            "mistralai/mistral-small-4-119b-2603",
            "mistralai/mistral-medium-3.5-128b",
            "google/gemma-4-31b-it",
            "nvidia/cosmos3-nano-reasoner",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
            "nvidia/llama-3.1-nemotron-51b-instruct",
            "qwen/qwen3.6-27b",
            "qwen/qwen3.5-122b-a10b",
            "moonshotai/kimi-k2.6",
            "moonshotai/kimi-k2.5",
            "stepfun-ai/step-3.7-flash",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "minimaxai/minimax-m3",
            "microsoft/phi-4-mini-instruct",
        ],
    },
    "OpenAI": {
        "base_url": "https://api.openai.com/v1",
        "models": [
            "o3",
            "o4-mini",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ],
    },
    "Google Gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ],
    },
    "OpenRouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "anthropic/claude-sonnet-4-5",
            "anthropic/claude-3.7-sonnet",
            "anthropic/claude-3.5-haiku",
            "google/gemini-2.5-pro",
            "google/gemini-2.5-flash",
            "openai/gpt-4o",
            "openai/o3",
            "meta-llama/llama-3.3-70b-instruct",
            "deepseek/deepseek-r1",
            "mistralai/mistral-large",
            "qwen/qwen3-235b-a22b",
            "moonshotai/kimi-k2",
        ],
    },
}

class AutoReadmeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NVIDIA NIM - Enterprise Project Context & README Architect")
        self.root.geometry("1100x850")
        self.root.configure(bg=BG_MAIN)
        self.root.minsize(900, 700)
        
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # General Styles
        self.style.configure(".", background=BG_MAIN, foreground=FG_TEXT, font=("Segoe UI", 10))
        self.style.configure("TLabel", background=BG_MAIN, foreground=FG_TEXT)
        self.style.configure("TFrame", background=BG_MAIN)
        
        # Typography & Sections
        self.style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), foreground=FG_ACCENT)
        self.style.configure("Section.TLabel", font=("Segoe UI", 10, "bold"), foreground=FG_ACCENT_PURPLE)
        self.style.configure("Sub.TLabel", font=("Segoe UI", 9), foreground=FG_MUTED)
        
        # Translucent Combobox Styles
        self.style.configure("TCombobox", fieldbackground=BG_CARD, background=BG_MAIN, foreground=FG_TEXT)
        self.style.map("TCombobox", 
                       fieldbackground=[("readonly", BG_CARD)], 
                       foreground=[("readonly", FG_TEXT)],
                       selectbackground=[("readonly", BG_CARD_LIGHT)])
        
        # Modern Neon Radio Buttons
        self.style.configure("TRadiobutton", background=BG_MAIN, foreground=FG_TEXT, font=("Segoe UI", 10))
        self.style.map("TRadiobutton", background=[("active", BG_MAIN)], foreground=[("active", FG_ACCENT)])

        # Premium Glowing Progressbar
        self.style.configure("Premium.Horizontal.TProgressbar", 
                             troughcolor=BG_CARD, 
                             background=FG_ACCENT, 
                             bordercolor=BG_MAIN, 
                             lightcolor=FG_ACCENT, 
                             darkcolor=FG_ACCENT, 
                             thickness=8)

    def create_widgets(self):
        # Header Canvas Logo & Banner
        header_frame = ttk.Frame(self.root, padding="15")
        header_frame.pack(fill=tk.X)
        
        # Neural Network Canvas Icon (Glassmorphic or Loaded Image)
        self.logo_canvas = tk.Canvas(header_frame, width=80, height=60, bg=BG_MAIN, highlightthickness=0)
        self.logo_canvas.pack(side=tk.LEFT, padx=(0, 15))
        
        # Download and cache the custom user logo
        self.logo_tk = None
        self.load_and_cache_logo()
        self.draw_neon_logo()
        
        title_container = ttk.Frame(header_frame)
        title_container.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(title_container, text="NVIDIA NIM - T-MASTER README ARCHITECT", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(title_container, text="Generate English T-1/T-2/T-3 context trees to decrease AI token cost by ~90%", style="Sub.TLabel").pack(anchor=tk.W)
        
        # Main Paned Workspace (Split layout: Control Panel & Markdown Editor)
        paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Left Panel (Inputs)
        left_frame = ttk.Frame(paned_window, padding="15")
        paned_window.add(left_frame, weight=1)
        
        # Right Panel (Preview)
        right_frame = ttk.Frame(paned_window, padding="15")
        paned_window.add(right_frame, weight=1)
        
        # --- LEFT PANEL CONTENTS ---
        
        # Load Config Values
        self._config = self.load_config()
        loaded_provider = self._config.get("provider", "NVIDIA NIM")
        loaded_base = self._config.get("api_base", PROVIDER_CONFIGS["NVIDIA NIM"]["base_url"])
        # Per-provider keys dict — falls back to legacy single api_key field
        self._api_keys = self._config.get("api_keys", {})
        if not self._api_keys and self._config.get("api_key"):
            self._api_keys["NVIDIA NIM"] = self._config["api_key"]
        loaded_key = self._api_keys.get(loaded_provider, os.environ.get("NVIDIA_API_KEY", ""))

        # Provider Selector
        provider_frame = ttk.Frame(left_frame)
        provider_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(provider_frame, text="AI Provider:", style="Section.TLabel").pack(anchor=tk.W, pady=2)
        self.provider_var = tk.StringVar(value=loaded_provider)
        self.provider_combo = ttk.Combobox(provider_frame, textvariable=self.provider_var,
                                           values=list(PROVIDER_CONFIGS.keys()), state="readonly")
        self.provider_combo.pack(fill=tk.X, ipady=4, pady=2)
        self.provider_combo.bind("<<ComboboxSelected>>", self.on_provider_change)

        # Endpoint Config Area
        endpoint_frame = ttk.Frame(left_frame)
        endpoint_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(endpoint_frame, text="API Base URL:", style="Section.TLabel").pack(anchor=tk.W, pady=2)
        self.api_base_entry = tk.Entry(endpoint_frame, bg=BG_CARD, fg="#ffffff", insertbackground="#ffffff",
                                       relief=tk.FLAT, font=("Consolas", 10))
        self.api_base_entry.pack(fill=tk.X, ipady=6, pady=2)
        self.api_base_entry.insert(0, loaded_base)

        # API Key Section
        api_frame = ttk.Frame(left_frame)
        api_frame.pack(fill=tk.X, pady=(0, 8))
        self.api_key_label = ttk.Label(api_frame, text="API Key:", style="Section.TLabel")
        self.api_key_label.pack(anchor=tk.W, pady=2)
        self.api_entry = tk.Entry(api_frame, bg=BG_CARD, fg="#ffffff", insertbackground="#ffffff",
                                  relief=tk.FLAT, font=("Consolas", 10), show="*")
        self.api_entry.pack(fill=tk.X, ipady=6, pady=2)
        if loaded_key:
            self.api_entry.insert(0, loaded_key)
        # Set startup state so on_provider_change knows what was previously selected
        self._current_provider = loaded_provider
        _startup_hints = {
            "NVIDIA NIM": "NVIDIA NIM API Key (nvapi-...)",
            "OpenAI": "OpenAI API Key (sk-...)",
            "Google Gemini": "Google Gemini API Key (AIza...)",
            "OpenRouter": "OpenRouter API Key (sk-or-...)",
        }
        self.api_key_label.config(text=_startup_hints.get(loaded_provider, "API Key:"))

        # Target Project Directory Selector
        dir_frame = ttk.Frame(left_frame)
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(dir_frame, text="Target Project Directory:", style="Section.TLabel").pack(anchor=tk.W, pady=2)
        
        dir_selector_frame = ttk.Frame(dir_frame)
        dir_selector_frame.pack(fill=tk.X)
        self.dir_entry = tk.Entry(dir_selector_frame, bg=BG_CARD, fg=FG_TEXT, insertbackground="#ffffff", 
                                  relief=tk.FLAT, font=("Segoe UI", 10))
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 5))
        self.dir_entry.insert(0, os.getcwd())
        
        self.browse_btn = tk.Button(dir_selector_frame, text="Browse...", bg=BG_CARD_LIGHT, fg=FG_TEXT, 
                               activebackground=BG_MAIN, activeforeground=FG_ACCENT, relief=tk.FLAT,
                               command=self.browse_directory, width=10, font=("Segoe UI", 9, "bold"))
        self.browse_btn.pack(side=tk.RIGHT, ipady=3)
        self.bind_hover_effect(self.browse_btn)
        
        # Model Configuration Dropdown
        model_frame = ttk.Frame(left_frame)
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        model_label_frame = ttk.Frame(model_frame)
        model_label_frame.pack(fill=tk.X)
        self.model_selection_label = ttk.Label(model_label_frame, text="NVIDIA NIM LLM Model Selection:", style="Section.TLabel")
        self.model_selection_label.pack(side=tk.LEFT, pady=2)
        
        self.refresh_models_btn = tk.Button(model_label_frame, text="Sync Active NIMs \u21bb", bg=BG_CARD_LIGHT, fg=FG_ACCENT,
                                       activebackground=BG_MAIN, activeforeground=FG_ACCENT, relief=tk.FLAT,
                                       command=self.start_refresh_models_thread, font=("Segoe UI", 8, "bold"))
        self.refresh_models_btn.pack(side=tk.RIGHT, padx=2)
        self.bind_hover_effect(self.refresh_models_btn)
        
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, state="readonly")
        
        self.default_models = (
            # --- Meta / Llama ---
            "meta/llama-3.3-70b-instruct",
            "meta/llama-3.1-70b-instruct",
            "meta/llama-3.1-8b-instruct",
            "meta/llama-3.2-3b-instruct",
            "meta/llama-3.2-1b-instruct",
            "meta/llama-4-scout-17b-16e-instruct",
            "meta/llama-4-maverick-17b-128e-instruct",
            "meta/llama-3.2-11b-vision-instruct",
            "meta/llama-3.2-90b-vision-instruct",
            # --- DeepSeek ---
            "deepseek-ai/deepseek-r1",
            "deepseek-ai/deepseek-r1-distill-llama-8b",
            "deepseek-ai/deepseek-r1-distill-qwen-7b",
            # --- Mistral ---
            "mistralai/mistral-large-3-675b-instruct-2512",
            "mistralai/mistral-small-3.2-24b-instruct-2506",
            "mistralai/mistral-small-4-119b-2603",
            "mistralai/mistral-medium-3.5-128b",
            "mistralai/ministral-3-14b-instruct-2512",
            # --- Google ---
            "google/gemma-4-31b-it",
            "google/diffusiongemma-26b-a4b-it",
            # --- NVIDIA ---
            "nvidia/cosmos3-nano-reasoner",
            "nvidia/cosmos-reason2-8b",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
            "nvidia/llama-3.1-nemotron-51b-instruct",
            "nvidia/nemotron-parse-v1.2",
            # --- Qwen ---
            "qwen/qwen3.6-27b",
            "qwen/qwen3.6-35b-a3b",
            "qwen/qwen3.5-122b-a10b",
            # --- Moonshot / Kimi ---
            "moonshotai/kimi-k2.6",
            "moonshotai/kimi-k2.5",
            # --- StepFun ---
            "stepfun-ai/step-3.7-flash",
            # --- OpenAI OSS ---
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            # --- Microsoft ---
            "microsoft/phi-4-mini-instruct",
            # --- MiniMax ---
            "minimaxai/minimax-m3",
            "minimaxai/minimax-m2.7",
        )
        self.model_combo['values'] = self.default_models
        self.model_combo.set("meta/llama-3.3-70b-instruct")
        self.model_combo.pack(fill=tk.X, ipady=4, pady=2)
        
        # IDE / Agent System Selection
        ide_frame = ttk.Frame(left_frame)
        ide_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(ide_frame, text="Target AI IDE / Copilot Agent:", style="Section.TLabel").pack(anchor=tk.W, pady=2)
        
        self.ide_var = tk.StringVar(value="cursor")
        id_options = [
            ("Cursor (AI Native Agent / rules system)", "cursor"),
            ("VS Code (Copilot / Cline / Roo-Code Workspace)", "vscode"),
            ("Antigravity IDE (Integrated AI Agent Workflow)", "antigravity"),
            ("Standalone Markdown (General Web LLM Ingest)", "other")
        ]
        
        for text, value in id_options:
            rb = ttk.Radiobutton(ide_frame, text=text, value=value, variable=self.ide_var, style="TRadiobutton")
            rb.pack(anchor=tk.W, pady=2)
            
        # Additional Project Notes (Manual Input)
        notes_frame = ttk.Frame(left_frame)
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        ttk.Label(notes_frame, text="Project Objectives & Custom Notes (Optional):", style="Section.TLabel").pack(anchor=tk.W, pady=2)
        
        self.notes_text = tk.Text(notes_frame, bg=BG_CARD, fg=FG_TEXT, insertbackground="#ffffff", 
                                  relief=tk.FLAT, font=("Segoe UI", 10), height=4)
        self.notes_text.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # Progress Bar & Percentage Status Indicators
        status_frame = ttk.Frame(left_frame)
        status_frame.pack(fill=tk.X, pady=(5, 2))
        
        self.status_label = ttk.Label(status_frame, text="Ready", style="Sub.TLabel")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.percent_label = ttk.Label(status_frame, text="0%", style="Section.TLabel")
        self.percent_label.pack(side=tk.RIGHT)
        
        self.progress_bar = ttk.Progressbar(left_frame, style="Premium.Horizontal.TProgressbar", mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(2, 10))
        self.progress_bar['value'] = 0
        
        # Primary Action Button
        self.generate_btn = tk.Button(left_frame, text="ARCHITECT COMPREHENSIVE README.MD", 
                                      bg="#4c1d95", fg="#ffffff", activebackground="#6d28d9", 
                                      activeforeground="#ffffff", relief=tk.FLAT, font=("Segoe UI", 11, "bold"),
                                      command=self.start_generation_thread)
        self.generate_btn.pack(fill=tk.X, ipady=12)
        self.bind_hover_effect(self.generate_btn, highlight_color=FG_ACCENT)
        
        # --- RIGHT PANEL CONTENTS (EXHAUSTIVE PREVIEW & SAVE) ---
        ttk.Label(right_frame, text="Generated Markdown Architecture (Editable Preview)", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        preview_container = ttk.Frame(right_frame)
        preview_container.pack(fill=tk.BOTH, expand=True)
        
        self.preview_text = tk.Text(preview_container, bg=BG_CARD, fg=FG_TEXT, insertbackground="#ffffff",
                                    relief=tk.FLAT, font=("Consolas", 10), wrap=tk.WORD)
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(preview_container, command=self.preview_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_text.config(yscrollcommand=scrollbar.set)
        
        # Export Button
        self.save_btn = tk.Button(right_frame, text="SAVE WORKSPACE README.MD", 
                                  bg="#065f46", fg="#ffffff", activebackground="#047857", 
                                  activeforeground="#ffffff", relief=tk.FLAT, font=("Segoe UI", 11, "bold"),
                                  command=self.save_readme_file, state=tk.DISABLED)
        self.save_btn.pack(fill=tk.X, ipady=10, pady=(10, 0))
        self.bind_hover_effect(self.save_btn, highlight_color="#50fa7b")

        # Sync all provider-specific labels to the loaded provider on startup
        self.on_provider_change()

    def draw_neon_logo(self):
        """Draws a beautiful cyberpunk neon network logo on the canvas"""
        self.logo_canvas.delete("all")
        if self.logo_tk:
            # Draw the loaded custom logo image directly on the canvas
            self.logo_canvas.create_image(40, 30, image=self.logo_tk)
            return
            
        # Draw glowing lines fallback
        
        # Draw glowing nodes
        self.logo_canvas.create_oval(10, 25, 20, 35, fill="#8a2be2", outline="#ffffff", width=1)
        self.logo_canvas.create_oval(35, 10, 45, 20, fill="#00ffd8", outline="#ffffff", width=1)
        self.logo_canvas.create_oval(35, 40, 45, 50, fill="#00ffd8", outline="#ffffff", width=1)
        self.logo_canvas.create_oval(60, 25, 70, 35, fill="#bd93f9", outline="#ffffff", width=1)

    def load_and_cache_logo(self):
        """Loads logo from user's URL, caches it on disk, generates an ICO, and sets the window icon"""
        logo_url = "https://lh3.googleusercontent.com/gps-cs-s/APNQkAHal_Cx8IXuplrkQCiDHSsct0uF3lGkvmycSCeEsK0LG9MECuQZixsbScdPSOPBr2pS62KA5nswXQti5SrgbXUtO8JxixutPL-p2k7sVgvrxCVAF1toxOuta5DyP5N3lxXXNA9WE8x5NQaQ=s680-w680-h510-rw"
        cache_dir = os.path.expanduser("~\\.nvidia_nim_cache")
        cache_path = os.path.join(cache_dir, "logo_custom.png")
        ico_path = os.path.join(cache_dir, "logo.ico")
        
        try:
            os.makedirs(cache_dir, exist_ok=True)
            if not os.path.exists(cache_path):
                # Download bytes in a short blocking request since it's startup
                r = requests.get(logo_url, timeout=4)
                if r.status_code == 200:
                    with open(cache_path, 'wb') as f:
                        f.write(r.content)
            
            if os.path.exists(cache_path):
                from PIL import Image, ImageTk
                img = Image.open(cache_path)
                
                # Generate native Windows .ico file if it doesn't exist
                if not os.path.exists(ico_path):
                    img.save(ico_path, format="ICO", sizes=[(64, 48), (32, 24), (16, 12)])
                
                # Set Tkinter window icon to replace the default feather
                if os.path.exists(ico_path):
                    try:
                        self.root.iconbitmap(ico_path)
                    except Exception as icon_err:
                        print("Failed to set window icon:", icon_err)
                
                img_resized = img.resize((80, 60), Image.Resampling.LANCZOS)
                self.logo_tk = ImageTk.PhotoImage(img_resized)
        except Exception as e:
            print("Online logo cache and icon loading failed:", e)

    def on_provider_change(self, event=None):
        """Save current key, then fill base URL/model list/key for the new provider."""
        # Save whatever key is currently in the field for the *previous* provider
        prev = getattr(self, "_current_provider", None)
        if prev:
            self._api_keys[prev] = self.api_entry.get().strip()

        provider = self.provider_var.get()
        self._current_provider = provider
        cfg = PROVIDER_CONFIGS.get(provider, {})

        # Update base URL
        self.api_base_entry.delete(0, tk.END)
        self.api_base_entry.insert(0, cfg.get("base_url", ""))

        # Update model list
        models = cfg.get("models", [])
        self.model_combo["values"] = models
        if models:
            self.model_combo.set(models[0])

        # Load this provider's saved API key (or clear the field)
        self.api_entry.delete(0, tk.END)
        saved_key = self._api_keys.get(provider, "")
        if saved_key:
            self.api_entry.insert(0, saved_key)

        # Update label hint
        hints = {
            "NVIDIA NIM": "NVIDIA NIM API Key (nvapi-...)",
            "OpenAI": "OpenAI API Key (sk-...)",
            "Google Gemini": "Google Gemini API Key (AIza...)",
            "OpenRouter": "OpenRouter API Key (sk-or-...)",
        }
        self.api_key_label.config(text=hints.get(provider, "API Key:"))

        # Update model section label and sync button text
        model_labels = {
            "NVIDIA NIM": "NVIDIA NIM LLM Model Selection:",
            "OpenAI": "OpenAI Model Selection:",
            "Google Gemini": "Google Gemini Model Selection:",
            "OpenRouter": "OpenRouter Model Selection:",
        }
        sync_labels = {
            "NVIDIA NIM": "Sync Active NIMs \u21bb",
            "OpenAI": "Sync Models \u21bb",
            "Google Gemini": "Sync Models \u21bb",
            "OpenRouter": "Sync Models \u21bb",
        }
        self.model_selection_label.config(text=model_labels.get(provider, "Model Selection:"))
        self.refresh_models_btn.config(text=sync_labels.get(provider, "Sync Models \u21bb"))

    def bind_hover_effect(self, widget, highlight_color=FG_ACCENT):
        """Creates smooth cyberpunk hover animations for buttons"""
        original_bg = widget.cget("bg")
        def on_enter(event):
            widget.config(bg=highlight_color, fg="#0a0d14")
        def on_leave(event):
            widget.config(bg=original_bg, fg="#ffffff")
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def browse_directory(self):
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, selected_dir)

    def scan_project_structure(self, base_dir):
        """Intelligent codebase crawler. Collects structure and file headers for up to 40 core scripts."""
        structure = []
        code_snippets = {}
        # Ignore heavy folders to avoid scanning overhead
        ignored_dirs = {
            '.git', 'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build',
            '.next', '.nuxt', 'out', 'coverage', '.idea', '.vscode', 'bower_components',
            'logs', 'vendor', '.yarn', 'public', 'assets', 'images', 'media', 'temp', 'tmp'
        }
        allowed_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.html', '.css', '.json', '.sh', '.bat', '.cjs', '.mjs'}
        
        file_count = 0
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            
            rel_path = os.path.relpath(root, base_dir)
            if rel_path == ".":
                rel_path = ""
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                full_rel_file = os.path.join(rel_path, file) if rel_path else file
                structure.append(full_rel_file)
                
                # Analyze up to 40 primary codebase scripts (compact context size)
                if ext in allowed_extensions and file_count < 40:
                    try:
                        file_path = os.path.join(root, file)
                        
                        # Skip files larger than 500 KB to avoid timeouts on database files/bundles
                        if os.path.getsize(file_path) > 500 * 1024:
                            continue
                            
                        file_count += 1
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            # Read only first 200 lines to fit context window smoothly
                            lines = []
                            for _ in range(200):
                                line = f.readline()
                                if not line:
                                    break
                                lines.append(line)
                            
                            # Signature Extraction (imports, classes, functions, exports)
                            summary_lines = []
                            for line in lines:
                                stripped = line.strip()
                                if (stripped.startswith(('import ', 'from ', 'def ', 'class ', 'function ', 'const ', 'let ', 'var ', 'export ', 'module.exports')) 
                                    or 'require(' in stripped 
                                    or stripped.startswith(('@', '#!'))):
                                    summary_lines.append(line)
                            
                            if not summary_lines:
                                summary_lines = lines[:30]
                                
                            content = "".join(summary_lines).strip()
                            if content:
                                code_snippets[full_rel_file] = content
                    except Exception:
                        pass
                        
        return structure, code_snippets

    def update_progress(self, val, status_text, color=None):
        self.root.after(0, lambda: self._update_progress_ui(val, status_text, color))

    def _update_progress_ui(self, val, status_text, color):
        self.progress_bar['value'] = val
        self.percent_label.config(text=f"{int(val)}%")
        if status_text:
            self.status_label.config(text=status_text)
        if color:
            self.status_label.config(foreground=color)
        else:
            self.status_label.config(foreground=FG_MUTED)

    def start_generation_thread(self):
        api_base = self.api_base_entry.get().strip()
        api_key = self.api_entry.get().strip()
        project_dir = self.dir_entry.get().strip()
        
        if not api_base:
            messagebox.showerror("Error", "Please enter a valid NVIDIA NIM API Base URL!")
            return
            
        if not api_key:
            messagebox.showerror("Error", "Please enter a valid NVIDIA NIM API Key!")
            return
            
        if not os.path.exists(project_dir):
            messagebox.showerror("Error", "Selected project directory does not exist!")
            return

        # Auto-Save configuration parameters on click
        self.save_config(api_key, api_base)

        self.generate_btn.config(text="Processing...", state=tk.DISABLED)
        self.update_progress(15, "Scanning project workspace...", FG_ACCENT)
        self.root.update_idletasks()
        
        threading.Thread(target=self.async_generate_readme, args=(api_base, api_key, project_dir), daemon=True).start()

    def async_generate_readme(self, api_base, api_key, project_dir):
        selected_ide = self.ide_var.get()
        selected_model = self.model_var.get()
        user_notes = self.notes_text.get("1.0", tk.END).strip()
        
        try:
            # 1. Full directory structure crawl (Excludes node_modules and heavy folders)
            files_list, snippets = self.scan_project_structure(project_dir)
            
            project_context = {
                "klasor_yapisi": files_list[:250], # Include up to 250 files in the directory list
                "secilen_ide": selected_ide,
                "kullanici_notlari": user_notes,
                "kod_ornekleri": {k: v[:600] for k, v in snippets.items()}
            }
            
            self.update_progress(35, "Extracting code signatures & imports...")
            time.sleep(0.5)
            provider = self.provider_var.get()
            self.update_progress(50, f"Invoking {provider} Engine...")

            # API Setup — headers differ per provider
            url = f"{api_base.rstrip('/')}/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            if provider == "NVIDIA NIM":
                headers["X-Nvidia-Api-Key"] = api_key
            elif provider == "OpenRouter":
                headers["HTTP-Referer"] = "https://github.com/uts-pro"
                headers["X-Title"] = "UTS PRO README Architect"
            
            # Two-message prompt: system enforces raw-only output, user delivers full instructions
            system_msg = (
                "You are an elite Principal Software Architect and AI Context Engineer. "
                "Your ONLY job is to output a raw, complete README.md file in GitHub-Flavored Markdown. "
                "CRITICAL RULES you must never break:\n"
                "1. Output MUST start immediately with the first '#' character of the README — zero preamble.\n"
                "2. NEVER write sentences like 'Here is your README', 'Certainly!', 'Below you will find', or any acknowledgment.\n"
                "3. NEVER truncate, summarize, or omit any file. Every file in the input list gets its own T-[FileName] section.\n"
                "4. Output ONLY raw Markdown — no code fences around the entire document, no XML tags, no JSON wrappers.\n"
                "5. The document must be production-ready: a developer or AI agent must be able to use it with zero additional context."
            )

            user_msg = f"""Generate the complete, exhaustive README.md for this software project. Follow every rule below without exception.

═══════════════════════════════════════════════════════
PROJECT INPUT DATA
═══════════════════════════════════════════════════════
Target AI IDE / Workspace:   {project_context['secilen_ide']}
Developer Notes / Objective: {project_context['kullanici_notlari'] or 'None provided'}
Complete File List:
{json.dumps(project_context['klasor_yapisi'], indent=2)}

Extracted Code Signatures & Imports:
{json.dumps(project_context['kod_ornekleri'], indent=2)}

═══════════════════════════════════════════════════════
MANDATORY README STRUCTURE (output in this exact order)
═══════════════════════════════════════════════════════

# [Project Name] — T-Master AI Context Tree

> ### 🚀 AI Cost Optimization Notice
> This README.md is the **T-Master context tree** for this codebase. AI assistants (Cursor, Copilot, Cline, Antigravity) **MUST** read this file first instead of recursively indexing the directory. This reduces context tokens and AI API costs by approximately **90%**.

---

## T-1 · Master Architecture

Write a detailed prose description of:
- The overall system design and execution flow
- How modules interact with each other (data flow, event flow, API calls)
- Entry points and boot sequence
- Key design patterns used (event-driven, MVC, microservice, etc.)
- External services and APIs the project depends on

---

## T-1.5 · Operational Pipeline & State Transitions

Provide an exhaustive step-by-step trace of the operational pipeline (using sequential tags like `T-100`, `T-101`, `T-142`, `T-143`, etc.):
- **Initialization (T-100 to T-110):** How the system boots, verifies environment configs, and establishes basic connections.
- **Integration & Validation (T-111 to T-130):** How files are integrated, licenses or plans are checked, and syntax is validated.
- **Active Operational Handshakes (T-131 to T-150):** The detailed transitions (e.g. how the system shifts from `T-142` standby state into `T-143` active background execution, worker orchestration, or event listeners). Explain the precise events, data payloads, and logging outputs that occur during these transition checkpoints.
- **Teardown & Exception Management (T-151+):** Logging, error catching, retries, and graceful termination.

---

## T-2 · Exhaustive Module Reference

**MANDATORY:** Create one sub-section for EVERY SINGLE file listed in the Complete File List above.
Use this exact format for each file:

### T-`<filename>`
| Field | Value |
|---|---|
| **Purpose** | One clear sentence describing what this file does |
| **Type** | Script / Config / Template / Data / Log / Other |
| **Execution** | How it is run (node, python, bat, sh, require'd, imported, etc.) |

**Imports / Dependencies:**
List every import/require found in the code signatures. Use inline code formatting.

**Exports / Public API:**
List every exported function, class, or value. For each function write:
- `functionName(param1: type, param2: type) → returnType` — one-line description

**Key Variables / Configuration:**
List any important module-level constants, config objects, or environment variables.

**Interactions:**
Which other files does this module call or get called by?

---

## T-3 · Execution & Runtime Reference

For each runtime platform present in the project, list:
- Exact command to run each script
- Required environment variables
- CLI arguments and flags
- Expected output / side effects

---

## T-4 · IDE & AI Agent Configuration

Write tailored instructions specifically for **{project_context['secilen_ide']}**:
- Where to place .cursorrules / .clinerules / workspace config
- System prompt template the agent should use when working on this project
- Which files the agent must read first
- Which files the agent must NEVER edit directly

---

## T-5 · Setup & Deployment

### Prerequisites
List every required runtime, tool, and global package.

### Installation
Step-by-step installation commands for Windows, macOS/Linux.

### Running in Development
Exact commands to start each service or script.

### Running in Production
Deployment steps, environment variable configuration, process manager setup.

═══════════════════════════════════════════════════════
FINAL REMINDER
═══════════════════════════════════════════════════════
- Start your output with `# ` immediately — no preamble.
- Every file in the file list MUST have its own T-`filename` section in T-2.
- All content in English.
- Be exhaustive. Longer is better. Never truncate.
"""

            payload = {
                "model": selected_model,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user",   "content": user_msg},
                ],
                "temperature": 0.15,
                "top_p": 0.85,
                "max_tokens": 8192,
            }

            
            max_retries = 3
            backoff = 3
            response = None
            error_details = "NIM API connection failed."
            
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        self.update_progress(50 + attempt * 12, f"Timeout. Retrying (Attempt {attempt+1}/{max_retries})...", "#ffb74d")
                        time.sleep(backoff * attempt)
                    
                    response = requests.post(url, headers=headers, json=payload, timeout=300)
                    
                    # Retry on server errors
                    if response.status_code in (429, 502, 503, 504) and attempt < max_retries - 1:
                        error_details = f"Server busy: HTTP {response.status_code} - {response.text}"
                        continue
                    break
                except Exception as req_err:
                    response = None
                    error_details = f"Connection Timeout / Error: {str(req_err)}"
                    if attempt < max_retries - 1:
                        continue
                    break
            
            if response and response.status_code == 200:
                self.update_progress(90, "Assembling markdown preview...")
                result_data = response.json()
                readme_content = result_data['choices'][0]['message']['content']
                self.root.after(0, lambda: self.show_preview(readme_content))
            else:
                error_msg = response.text if response else error_details
                try:
                    if response:
                        error_msg = response.json().get('detail', response.text)
                except:
                    pass
                status_code = response.status_code if response else "Timeout"
                self.root.after(0, lambda em=error_msg, sc=status_code: self.show_error(f"API Error (HTTP {sc}):\n{em}"))
                
        except Exception as e:
            self.root.after(0, lambda ex=str(e): self.show_error(f"Processing Error:\n{ex}"))
            
        finally:
            self.root.after(0, self.reset_generate_btn)

    def show_preview(self, content):
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, content)
        self.save_btn.config(state=tk.NORMAL)
        self.update_progress(100, "README.md generated successfully! Review and save.", BG_SUCCESS)

    def show_error(self, message):
        messagebox.showerror("Error", message)
        self.update_progress(0, "Error occurred.", "red")

    def reset_generate_btn(self):
        self.generate_btn.config(text="ARCHITECT COMPREHENSIVE README.MD", state=tk.NORMAL)

    def save_readme_file(self):
        project_dir = self.dir_entry.get().strip()
        readme_content = self.preview_text.get("1.0", tk.END).strip()
        
        if not readme_content:
            messagebox.showwarning("Warning", "No content found to save!")
            return
            
        output_path = os.path.join(project_dir, "README.md")
        try:
            with open(output_path, "w", encoding="utf-8") as out_file:
                out_file.write(readme_content)
            messagebox.showinfo("Success", f"README.md saved to workspace root successfully!\nPath: {output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

    def start_refresh_models_thread(self):
        api_base = self.api_base_entry.get().strip()
        api_key = self.api_entry.get().strip()
        if not api_base or not api_key:
            messagebox.showerror("Error", "Please supply both API Base URL and API Key to sync models!")
            return
        
        self.save_config(api_key, api_base)
        
        self.status_label.config(text="Syncing active models from NIM Catalog...", foreground=FG_ACCENT)
        threading.Thread(target=self.async_refresh_models, args=(api_base, api_key), daemon=True).start()

    def async_refresh_models(self, api_base, api_key):
        try:
            url = f"{api_base.rstrip('/')}/models"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "X-Nvidia-Api-Key": api_key,
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                models_data = response.json().get("data", [])
                
                chat_models = []
                ignored_keywords = ('embed', 'rerank', 'clip', 'diffusion', 'whisper', 'tts', 'stt', 'deit', 'neva', 'kosmos', 'fuyu')
                for item in models_data:
                    model_id = item.get("id", "")
                    if any(kw in model_id.lower() for kw in ('llama', 'gemma', 'mixtral', 'mistral', 'qwen', 'phi', 'deepseek', 'instruct', 'chat')):
                        if not any(ikw in model_id.lower() for ikw in ignored_keywords):
                            chat_models.append(model_id)
                
                chat_models = sorted(list(set(chat_models)))
                
                if chat_models:
                    self.root.after(0, lambda: self.update_model_dropdown(chat_models))
                else:
                    self.root.after(0, lambda: self.show_error("No compatible chat models found. Fallback list loaded."))
            else:
                self.root.after(0, lambda: self.show_error(f"Sync failed. HTTP Error {response.status_code}"))
        except Exception as e:
            self.root.after(0, lambda ex=str(e): self.show_error(f"Failed to query model list:\n{ex}"))

    def update_model_dropdown(self, models):
        self.model_combo['values'] = models
        current = self.model_var.get()
        if current in models:
            self.model_combo.set(current)
        else:
            priority = [m for m in models if "llama-3.3-70b" in m or "deepseek-r1" in m]
            if priority:
                self.model_combo.set(priority[0])
            else:
                self.model_combo.set(models[0])
        self.status_label.config(text=f"Sync successful! {len(models)} models loaded.", foreground=FG_ACCENT)

    def load_config(self):
        CONFIG_PATH_SYSTEM = "C:\\Program Files\\NvidiaNimArchitect\\config.json"
        CONFIG_PATH_USER = os.path.expanduser("~\\.nvidia_nim_config.json")
        for path in (CONFIG_PATH_SYSTEM, CONFIG_PATH_USER):
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
        return {}

    def save_config(self, api_key, api_base):
        CONFIG_PATH_SYSTEM = "C:\\Program Files\\NvidiaNimArchitect\\config.json"
        CONFIG_PATH_USER = os.path.expanduser("~\\.nvidia_nim_config.json")
        # Update the per-provider key dict in-place
        provider = self.provider_var.get()
        self._api_keys[provider] = api_key
        data = {
            "provider": provider,
            "api_base": api_base,
            "api_keys": self._api_keys,
        }
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH_SYSTEM), exist_ok=True)
            with open(CONFIG_PATH_SYSTEM, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
                return
        except PermissionError:
            try:
                with open(CONFIG_PATH_USER, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
            except:
                pass
        except:
            try:
                with open(CONFIG_PATH_USER, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
            except:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoReadmeApp(root)
    root.mainloop()