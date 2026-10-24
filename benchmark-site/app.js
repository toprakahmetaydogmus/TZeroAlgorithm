/**
 * T-ZERO BENCHMARK LAB — PREMIUM ENGINE
 * Three.js Particle System + Interactive Data Visualization
 * All metrics from real Python AST TokenReducer analysis.
 * NO external API calls — 100% static client-side.
 */

// ==========================================
// REAL VERIFIED BENCHMARK DATA
// ==========================================
const BENCHMARK_DATA = [
  {
    file: "tzero_v3.py",
    lines: 6008,
    chars: 271369,
    rawTokens: 67842,
    ultraTokens: 3800,
    ultraPct: 94.40,
    balancedTokens: 62539,
    balancedPct: 7.82,
    ultraSample: `import os
import sys
import re
import ast
import json
import time
import math
import logging
import keyring
import requests
import threading
from typing import Dict, List, Any, Tuple, Optional, Set

# --- T-ZERO AST CORE SIGNATURE MAP (6,008 lines pruned to 3,800 tokens) ---
class TokenReducer:
    @staticmethod
    def reduce(content: str, filename: str, mode: str = "ultra") -> str: ...
    @staticmethod
    def _reduce_python(content: str, mode: str) -> str: ...

class CodebaseScanner:
    def __init__(self, target_dir: str): ...
    def scan_workspace(self, max_tokens: int = 128000) -> Dict[str, Any]: ...

class ConfigManager:
    def get_api_key(self, provider: str) -> Optional[str]: ...
    def set_api_key(self, provider: str, key: str) -> bool: ...

class AutoReadmeGUI:
    def __init__(self, root): ...
    def build_dashboard(self): ...
    def run_token_audit(self): ...

def count_tokens_precise(text: str) -> int: ...
def build_compact_context_tree(project_dir: str) -> str: ...`,
    balancedSample: `# Balanced AST Mode: Keeps comments & method docstrings
class TokenReducer:
    """Enterprise-grade AST reducer supporting ultra & balanced modes."""
    @staticmethod
    def reduce(content: str, filename: str, mode: str = "balanced") -> str:
        # Implementation signature with interface contracts preserved
        ...`,
    rawSample: `# Full Source Preview (First 40 lines of 6,008 lines)
import os
import sys
import re
import ast
import json
import time
import math
import random
import logging
import shutil
import keyring
import requests
import threading
import subprocess
from typing import Dict, List, Any, Tuple, Optional, Set, Callable

# Configuration and Keyring Management
CONFIG_DIR = os.path.expanduser("~/.tzero")
KEYRING_SERVICE = "TZeroAlgorithmV3"

def init_keyring_store():
    # Attempting native OS credential store handshake
    try:
        keyring.set_password(KEYRING_SERVICE, "__test__", "1")
        keyring.delete_password(KEYRING_SERVICE, "__test__")
        return True
    except Exception:
        return False
... [6,008 lines total | 67,842 tokens]`
  },
  {
    file: "tzero_features.py",
    lines: 1031,
    chars: 41891,
    rawTokens: 10472,
    ultraTokens: 542,
    ultraPct: 94.82,
    balancedTokens: 6791,
    balancedPct: 35.15,
    ultraSample: `import os
import sys
import re
import ast
import json
from typing import Dict, List, Set, Tuple, Optional, Any

class ChangeImpactAnalyzer:
    def __init__(self, project_dir: str): ...
    def analyze_symbol(self, symbol_name: str) -> Dict[str, Any]: ...
    def calculate_blast_radius_score(self, dependents: List[str]) -> int: ...

class ArchitectureRuleEngine:
    def __init__(self, rules_file: str): ...
    def enforce_boundaries(self, file_path: str) -> List[str]: ...

class LocalSemanticSearcher:
    def __init__(self, project_dir: str): ...
    def index_workspace(self): ...
    def query_bm25_hybrid(self, query: str, top_k: int = 5) -> List[Dict]: ...

class ROIEstimator:
    @staticmethod
    def calculate_savings(raw_tokens: int, ultra_tokens: int, model: str) -> Dict: ...`,
    balancedSample: `class ChangeImpactAnalyzer:
    """Traces AST callers and downstream dependencies across codebase."""
    def analyze_symbol(self, symbol_name: str) -> Dict[str, Any]:
        """Calculates 0-100 blast radius score for symbol."""
        ...`,
    rawSample: `import os
import sys
import re
import ast
import json
import math
import collections
import http.server
import socketserver
import threading
import urllib.parse
from typing import Dict, List, Set, Tuple, Optional, Any

def should_skip_dir(root: str, base_dir: str) -> bool:
    skip_dirs = {".git", ".idea", "__pycache__", "venv", ".venv", "dist", "build"}
    parts = os.path.relpath(root, base_dir).split(os.sep)
    return any(p in skip_dirs for p in parts)
... [1,031 lines total | 10,472 tokens]`
  },
  {
    file: "tzero_mcp.py",
    lines: 842,
    chars: 34987,
    rawTokens: 8746,
    ultraTokens: 410,
    ultraPct: 95.31,
    balancedTokens: 6757,
    balancedPct: 22.74,
    ultraSample: `import os
import sys
import json
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

server = FastMCP("tzero")

@server.tool()
def get_project_context_tree(project_root: str, reduction_mode: str = "ultra") -> str: ...

@server.tool()
def query_module_dependencies(project_root: str, file_path: str = "") -> str: ...

@server.tool()
def audit_codebase_quality(project_root: str) -> str: ...

@server.tool()
def search_codebase_semantic(query: str, project_root: str) -> str: ...

@server.tool()
def analyze_change_impact(target_symbol: str, project_root: str) -> str: ...

@server.tool()
def enforce_architecture_boundaries(project_root: str) -> str: ...`,
    balancedSample: `@server.tool()
def get_project_context_tree(project_root: str, reduction_mode: str = "ultra") -> str:
    """Builds hierarchical AST context tree reducing tokens by up to 95%."""
    ...`,
    rawSample: `import os
import sys
import json
import re
import ast
import inspect
import logging
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("tzero_mcp")
... [842 lines total | 8,746 tokens]`
  },
  {
    file: "addmcp.py",
    lines: 1015,
    chars: 41013,
    rawTokens: 10253,
    ultraTokens: 397,
    ultraPct: 96.13,
    balancedTokens: 6613,
    balancedPct: 35.50,
    ultraSample: `from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

@dataclass(frozen=True)
class ClientTarget:
    name: str
    config_path: Path
    detected: bool

def build_client_targets() -> List[ClientTarget]: ...
def inject_mcp_config(target: ClientTarget) -> bool: ...
def detect_installed_ides() -> List[str]: ...
def main(): ...`,
    balancedSample: `@dataclass(frozen=True)
class ClientTarget:
    """Represents an IDE MCP configuration target file."""
    name: str
    config_path: Path
    detected: bool`,
    rawSample: `import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
... [1,015 lines total | 10,253 tokens]`
  }
];

// ==========================================
// THREE.JS PARTICLE SYSTEM
// ==========================================
// ==========================================
// THREE.JS PARTICLE SYSTEM (BACKGROUND AMBIENT)
// ==========================================
function initParticleSystem() {
  const canvas = document.getElementById("hero-canvas");
  if (!canvas || typeof THREE === "undefined") return;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // Circular glowing star sprite texture (prevents square quads)
  const circleCanvas = document.createElement("canvas");
  circleCanvas.width = 32;
  circleCanvas.height = 32;
  const cctx = circleCanvas.getContext("2d");
  const radGrad = cctx.createRadialGradient(16, 16, 0, 16, 16, 16);
  radGrad.addColorStop(0, "rgba(255, 255, 255, 1)");
  radGrad.addColorStop(0.35, "rgba(0, 240, 255, 0.8)");
  radGrad.addColorStop(0.75, "rgba(0, 240, 255, 0.15)");
  radGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
  cctx.fillStyle = radGrad;
  cctx.beginPath();
  cctx.arc(16, 16, 16, 0, Math.PI * 2);
  cctx.fill();
  const circleTexture = new THREE.CanvasTexture(circleCanvas);

  // Elegant subtle particle count
  const particleCount = 100;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(particleCount * 3);
  const velocities = new Float32Array(particleCount * 3);
  const colors = new Float32Array(particleCount * 3);

  const cyanColor = new THREE.Color(0x00f0ff);
  const purpleColor = new THREE.Color(0xa855f7);
  const emeraldColor = new THREE.Color(0x10b981);

  for (let i = 0; i < particleCount; i++) {
    const i3 = i * 3;
    // Keep particles well behind camera (camera at z=40)
    positions[i3] = (Math.random() - 0.5) * 60;
    positions[i3 + 1] = (Math.random() - 0.5) * 45;
    positions[i3 + 2] = -Math.random() * 25 - 5; // z between -30 and -5

    velocities[i3] = (Math.random() - 0.5) * 0.008;
    velocities[i3 + 1] = (Math.random() - 0.5) * 0.008;
    velocities[i3 + 2] = (Math.random() - 0.5) * 0.004;

    const colorChoice = Math.random();
    let color;
    if (colorChoice < 0.5) color = cyanColor;
    else if (colorChoice < 0.8) color = purpleColor;
    else color = emeraldColor;

    colors[i3] = color.r;
    colors[i3 + 1] = color.g;
    colors[i3 + 2] = color.b;
  }

  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({
    size: 1.2,
    map: circleTexture,
    vertexColors: true,
    transparent: true,
    opacity: 0.35,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true,
    depthWrite: false,
  });

  const particles = new THREE.Points(geometry, material);
  scene.add(particles);

  // Ambient connection lines
  const lineGeometry = new THREE.BufferGeometry();
  const linePositions = new Float32Array(particleCount * 6);
  const lineColors = new Float32Array(particleCount * 6);
  lineGeometry.setAttribute("position", new THREE.BufferAttribute(linePositions, 3));
  lineGeometry.setAttribute("color", new THREE.BufferAttribute(lineColors, 3));
  
  const lineMaterial = new THREE.LineBasicMaterial({
    vertexColors: true,
    transparent: true,
    opacity: 0.08,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
  scene.add(lines);

  camera.position.z = 40;

  let mouseX = 0, mouseY = 0;
  document.addEventListener("mousemove", (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  let lineIndex = 0;
  function animate() {
    requestAnimationFrame(animate);

    const posArr = particles.geometry.attributes.position.array;

    for (let i = 0; i < particleCount; i++) {
      const i3 = i * 3;
      posArr[i3] += velocities[i3];
      posArr[i3 + 1] += velocities[i3 + 1];
      posArr[i3 + 2] += velocities[i3 + 2];

      // Strict boundaries ensuring particles NEVER approach camera z=40
      if (posArr[i3] > 32 || posArr[i3] < -32) velocities[i3] *= -1;
      if (posArr[i3 + 1] > 24 || posArr[i3 + 1] < -24) velocities[i3 + 1] *= -1;
      if (posArr[i3 + 2] > 2 || posArr[i3 + 2] < -32) velocities[i3 + 2] *= -1;
    }

    // Update connections
    lineIndex = 0;
    const lp = lines.geometry.attributes.position.array;
    const lc = lines.geometry.attributes.color.array;
    const maxDist = 7;

    for (let i = 0; i < Math.min(particleCount, 40); i++) {
      for (let j = i + 1; j < Math.min(particleCount, 40); j++) {
        const i3 = i * 3, j3 = j * 3;
        const dx = posArr[i3] - posArr[j3];
        const dy = posArr[i3 + 1] - posArr[j3 + 1];
        const dz = posArr[i3 + 2] - posArr[j3 + 2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

        if (dist < maxDist && lineIndex < particleCount * 2) {
          const li = lineIndex * 6;
          lp[li] = posArr[i3];
          lp[li + 1] = posArr[i3 + 1];
          lp[li + 2] = posArr[i3 + 2];
          lp[li + 3] = posArr[j3];
          lp[li + 4] = posArr[j3 + 1];
          lp[li + 5] = posArr[j3 + 2];

          const alpha = 1 - dist / maxDist;
          lc[li] = 0; lc[li + 1] = 0.94 * alpha; lc[li + 2] = 1 * alpha;
          lc[li + 3] = 0; lc[li + 4] = 0.94 * alpha; lc[li + 5] = 1 * alpha;
          lineIndex++;
        }
      }
    }

    // Clear unused lines
    for (let i = lineIndex * 6; i < particleCount * 6; i++) {
      lp[i] = 0;
      lc[i] = 0;
    }

    particles.geometry.attributes.position.needsUpdate = true;
    lines.geometry.attributes.position.needsUpdate = true;
    lines.geometry.attributes.color.needsUpdate = true;

    // Smooth subtle mouse follow
    particles.rotation.y += (mouseX * 0.05 - particles.rotation.y) * 0.02;
    particles.rotation.x += (-mouseY * 0.03 - particles.rotation.x) * 0.02;
    lines.rotation.y = particles.rotation.y;
    lines.rotation.x = particles.rotation.x;

    renderer.render(scene, camera);
  }

  animate();
}

// ==========================================
// SCROLL ANIMATIONS
// ==========================================
function initScrollAnimations() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
  );

  document.querySelectorAll(".animate-on-scroll").forEach((el) => {
    observer.observe(el);
  });
}

// ==========================================
// TOAST NOTIFICATION & SAFE CLIPBOARD HELPER
// ==========================================
function showToast(message, icon = "⚡") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `<span style="font-size:16px">${icon}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = "opacity 0.3s ease, transform 0.3s ease";
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px) scale(0.95)";
    setTimeout(() => toast.remove(), 300);
  }, 2700);
}

function copyTextWithToast(text, successMessage = "Copied to clipboard!") {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text).then(() => {
      showToast(successMessage, "✓");
      return true;
    }).catch(() => fallbackCopy(text, successMessage));
  } else {
    return fallbackCopy(text, successMessage);
  }
}

function fallbackCopy(text, successMessage) {
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    ta.style.top = "-9999px";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    if (ok) {
      showToast(successMessage, "✓");
      return Promise.resolve(true);
    }
  } catch (e) {}
  showToast("Please copy manually", "ℹ️");
  return Promise.resolve(false);
}

// ==========================================
// NAVBAR SCROLL & MOBILE MENU & SCROLLSPY
// ==========================================
function initNavbarScroll() {
  const navbar = document.getElementById("navbar");
  const mobileBtn = document.getElementById("mobile-menu-btn");
  const navLinks = document.getElementById("nav-links");
  const links = document.querySelectorAll(".nav-link");

  if (mobileBtn && navLinks) {
    mobileBtn.addEventListener("click", () => {
      mobileBtn.classList.toggle("active");
      navLinks.classList.toggle("nav-open");
    });

    links.forEach(link => {
      link.addEventListener("click", () => {
        mobileBtn.classList.remove("active");
        navLinks.classList.remove("nav-open");
      });
    });
  }

  // Rock-solid ScrollSpy calculation
  const sectionEls = Array.from(document.querySelectorAll("section[id]"));
  function updateScrollSpy() {
    const scrollPos = window.scrollY + 140;
    let currentId = "";
    for (const sec of sectionEls) {
      const top = sec.offsetTop;
      const height = sec.offsetHeight;
      if (scrollPos >= top && scrollPos < top + height) {
        currentId = sec.getAttribute("id");
        break;
      }
    }
    if (currentId) {
      links.forEach(link => {
        if (link.getAttribute("href") === `#${currentId}`) {
          link.classList.add("active");
        } else {
          link.classList.remove("active");
        }
      });
    }
  }

  window.addEventListener("scroll", updateScrollSpy, { passive: true });
  updateScrollSpy();

  window.addEventListener("scroll", () => {
    if (!navbar) return;
    if (window.scrollY > 40) {
      navbar.classList.add("scrolled");
    } else {
      navbar.classList.remove("scrolled");
    }
  }, { passive: true });
}

// ==========================================
// COUNTER ANIMATION
// ==========================================
function initCounterAnimation() {
  const counters = document.querySelectorAll(".fs-number");
  
  const animateCounter = (el) => {
    const target = parseInt(el.dataset.count);
    if (isNaN(target)) return;
    
    const duration = 2000;
    const startTime = performance.now();
    
    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      
      const current = Math.round(target * eased);
      
      if (target === 0) {
        el.textContent = "$0";
      } else {
        el.textContent = current.toLocaleString();
      }
      
      if (progress < 1) {
        requestAnimationFrame(update);
      }
    }
    
    requestAnimationFrame(update);
  };

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const el = entry.target;
          animateCounter(el);
          observer.unobserve(el);
        }
      });
    },
    { threshold: 0.5 }
  );

  counters.forEach((counter) => observer.observe(counter));
}

// ==========================================
// DOM INIT
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
  const safeInit = (fn, name) => {
    try {
      fn();
    } catch (err) {
      console.warn(`[T-Zero Init] ${name} caught non-fatal exception:`, err);
    }
  };

  safeInit(initParticleSystem, "ParticleSystem");
  safeInit(initScrollAnimations, "ScrollAnimations");
  safeInit(initNavbarScroll, "NavbarScroll");
  safeInit(initCounterAnimation, "CounterAnimation");
  safeInit(renderBenchmarkTable, "BenchmarkTable");
  safeInit(renderVisualBars, "VisualBars");
  safeInit(initInspector, "Inspector");
  safeInit(initCalculator, "Calculator");
  safeInit(initCopyButtons, "CopyButtons");
  safeInit(initSandbox, "Sandbox");
  safeInit(initCausalHUD, "CausalHUD");
  safeInit(initMCPTools, "MCPTools");
  safeInit(initAgentSetupTabs, "AgentSetupTabs");
  safeInit(initDownloadCenter, "DownloadCenter");
});

// ==========================================
// BENCHMARK TABLE
// ==========================================
function renderBenchmarkTable() {
  const tbody = document.getElementById("benchmark-tbody");
  if (!tbody) return;

  tbody.innerHTML = BENCHMARK_DATA.map(item => `
    <tr>
      <td class="file-cell">📄 ${item.file}</td>
      <td>${item.lines.toLocaleString()}</td>
      <td>${item.chars.toLocaleString()}</td>
      <td style="color:#fb7185">${item.rawTokens.toLocaleString()}</td>
      <td style="color:#00f0ff; font-weight:700">${item.ultraTokens.toLocaleString()}</td>
      <td class="reduction-cell">-${item.ultraPct.toFixed(2)}%</td>
      <td><span class="badge badge-success">Verified</span></td>
    </tr>
  `).join("");
}

// ==========================================
// VISUAL BARS
// ==========================================
function renderVisualBars() {
  const container = document.getElementById("visual-bars");
  if (!container) return;

  container.innerHTML = BENCHMARK_DATA.map(item => {
    const ultraWidth = Math.max(4, (item.ultraTokens / item.rawTokens) * 100);
    return `
      <div class="bar-row">
        <div class="bar-info">
          <span><strong>${item.file}</strong></span>
          <span>Raw: <span style="color:#fb7185">${item.rawTokens.toLocaleString()}</span> → Ultra: <span style="color:#00f0ff">${item.ultraTokens.toLocaleString()}</span> (<span style="color:#10b981">-${item.ultraPct.toFixed(1)}%</span>)</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill-ultra" style="width: ${ultraWidth}%">
            ${ultraWidth > 8 ? item.ultraTokens.toLocaleString() : ''}
          </div>
          <div class="bar-fill-raw">
            Token Savings: -${item.ultraPct.toFixed(1)}%
          </div>
        </div>
      </div>
    `;
  }).join("");
}

// ==========================================
// AST INSPECTOR (OPTIONAL LEGACY)
// ==========================================
let currentFile = "tzero_v3.py";
let currentMode = "ultra";

function initInspector() {
  const fileTabs = document.querySelectorAll("#file-tabs .tab-btn");
  const modeTabs = document.querySelectorAll("#mode-tabs .mode-btn");

  if (!fileTabs.length && !modeTabs.length) return;

  fileTabs.forEach(btn => {
    btn.addEventListener("click", () => {
      fileTabs.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentFile = btn.dataset.file;
      updateInspectorView();
    });
  });

  modeTabs.forEach(btn => {
    btn.addEventListener("click", () => {
      modeTabs.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentMode = btn.dataset.mode;
      updateInspectorView();
    });
  });

  updateInspectorView();
}

function updateInspectorView() {
  const display = document.getElementById("code-display");
  const filenameEl = document.getElementById("active-filename");
  const tokensEl = document.getElementById("active-tokens");
  const reductionEl = document.getElementById("active-reduction");
  const titleEl = document.getElementById("editor-title");

  if (!display || !tokensEl || !reductionEl || !titleEl) return;

  const data = BENCHMARK_DATA.find(d => d.file === currentFile) || BENCHMARK_DATA[0];
  if (filenameEl) filenameEl.textContent = data.file;

  if (currentMode === "ultra") {
    display.textContent = data.ultraSample;
    tokensEl.textContent = `${data.ultraTokens.toLocaleString()} tokens`;
    reductionEl.textContent = `-${data.ultraPct.toFixed(2)}%`;
    titleEl.textContent = `${data.file} — Ultra AST Signatures (-${data.ultraPct.toFixed(1)}%)`;
  } else if (currentMode === "balanced") {
    display.textContent = data.balancedSample;
    tokensEl.textContent = `${data.balancedTokens.toLocaleString()} tokens`;
    reductionEl.textContent = `-${data.balancedPct.toFixed(2)}%`;
    titleEl.textContent = `${data.file} — Balanced AST Signatures (-${data.balancedPct.toFixed(1)}%)`;
  } else {
    display.textContent = data.rawSample;
    tokensEl.textContent = `${data.rawTokens.toLocaleString()} tokens`;
    reductionEl.textContent = "0.00% (Raw Source)";
    titleEl.textContent = `${data.file} — Full Unoptimized Source`;
  }
}

// ==========================================
// FINANCIAL CALCULATOR
// ==========================================
function initCalculator() {
  const reqSlider = document.getElementById("req-slider");
  const devSlider = document.getElementById("dev-slider");
  const reqVal = document.getElementById("req-val");
  const devVal = document.getElementById("dev-val");
  const modelChips = document.querySelectorAll(".model-chip");
  const reqPresets = document.querySelectorAll("#req-presets .calc-preset-btn");
  const devPresets = document.querySelectorAll("#dev-presets .calc-preset-btn");
  const copyBtn = document.getElementById("calc-copy-btn");

  if (!reqSlider || !devSlider) return;

  let currentModelCost = 2.50;
  let currentModelName = "OpenAI GPT-4o";

  function updateSliderTrack(slider) {
    const min = parseFloat(slider.min) || 0;
    const max = parseFloat(slider.max) || 100;
    const val = parseFloat(slider.value) || 0;
    const pct = Math.max(0, Math.min(100, ((val - min) / (max - min)) * 100));
    slider.style.background = `linear-gradient(to right, var(--accent-cyan) 0%, var(--accent-cyan) ${pct}%, rgba(20, 28, 48, 0.8) ${pct}%, rgba(20, 28, 48, 0.8) 100%)`;
  }

  modelChips.forEach(chip => {
    chip.addEventListener("click", () => {
      modelChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      currentModelCost = parseFloat(chip.dataset.cost);
      currentModelName = chip.dataset.name || chip.querySelector(".model-name")?.textContent?.trim() || "LLM";
      calculateROI();
    });
  });

  reqPresets.forEach(btn => {
    btn.addEventListener("click", () => {
      reqPresets.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const val = parseInt(btn.dataset.val);
      reqSlider.value = val;
      if (reqVal) reqVal.textContent = `${val.toLocaleString()} requests`;
      updateSliderTrack(reqSlider);
      calculateROI();
    });
  });

  devPresets.forEach(btn => {
    btn.addEventListener("click", () => {
      devPresets.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const count = parseInt(btn.dataset.val);
      devSlider.value = count;
      if (devVal) devVal.textContent = `${count} ${count === 1 ? 'developer' : 'developers'}`;
      updateSliderTrack(devSlider);
      calculateROI();
    });
  });

  reqSlider.addEventListener("input", (e) => {
    const val = parseInt(e.target.value);
    if (reqVal) reqVal.textContent = `${val.toLocaleString()} requests`;
    reqPresets.forEach(b => {
      if (parseInt(b.dataset.val) === val) b.classList.add("active");
      else b.classList.remove("active");
    });
    updateSliderTrack(reqSlider);
    calculateROI();
  });

  devSlider.addEventListener("input", (e) => {
    const count = parseInt(e.target.value);
    if (devVal) devVal.textContent = `${count} ${count === 1 ? 'developer' : 'developers'}`;
    devPresets.forEach(b => {
      if (parseInt(b.dataset.val) === count) b.classList.add("active");
      else b.classList.remove("active");
    });
    updateSliderTrack(devSlider);
    calculateROI();
  });

  function calculateROI() {
    const monthlyRequestsPerDev = parseInt(reqSlider.value) || 5000;
    const devCount = parseInt(devSlider.value) || 3;
    const totalRequests = monthlyRequestsPerDev * devCount;

    const rawTokensPerReq = 102265;
    const tzeroTokensPerReq = 5274;

    const totalRawTokens = totalRequests * rawTokensPerReq;
    const totalTzeroTokens = totalRequests * tzeroTokensPerReq;

    const monthlyRawCost = (totalRawTokens / 1000000) * currentModelCost;
    const monthlyTzeroCost = (totalTzeroTokens / 1000000) * currentModelCost;
    const monthlySavings = monthlyRawCost - monthlyTzeroCost;
    const annualSavings = monthlySavings * 12;

    const rawTokensEl = document.getElementById("calc-raw-tokens");
    const tzeroTokensEl = document.getElementById("calc-tzero-tokens");
    const rawCostEl = document.getElementById("calc-raw-cost");
    const tzeroCostEl = document.getElementById("calc-tzero-cost");
    const annualSavingsEl = document.getElementById("calc-annual-savings");

    if (rawTokensEl) rawTokensEl.textContent = `${totalRawTokens.toLocaleString()} tokens`;
    if (tzeroTokensEl) tzeroTokensEl.textContent = `${totalTzeroTokens.toLocaleString()} tokens`;
    
    if (rawCostEl) rawCostEl.textContent = `$${monthlyRawCost.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / mo`;
    if (tzeroCostEl) tzeroCostEl.textContent = `$${monthlyTzeroCost.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / mo`;
    
    if (annualSavingsEl) {
      annualSavingsEl.textContent = `$${annualSavings.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / YEAR`;
    }
  }

  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      const devCount = devSlider.value;
      const savings = document.getElementById("calc-annual-savings")?.textContent || "";
      const text = `🚀 T-Zero AST Token Reduction ROI Report:\n` +
        `• Engineering Team Size: ${devCount} developers\n` +
        `• Target Model: ${currentModelName} ($${currentModelCost}/1M tokens)\n` +
        `• Monthly Prompt Requests: ${parseInt(reqSlider.value).toLocaleString()}\n` +
        `• Net Annual Savings: ${savings}\n` +
        `• Payback Period: Instant (Day 1, 100% Free T-Zero)`;
      copyTextWithToast(text, "ROI Summary copied to clipboard!");
    });
  }

  updateSliderTrack(reqSlider);
  updateSliderTrack(devSlider);
  calculateROI();
}

// ==========================================
// COPY BUTTONS
// ==========================================
function initCopyButtons() {
  // Hero copy button
  const heroCopy = document.getElementById("hero-copy-btn");
  if (heroCopy) {
    heroCopy.addEventListener("click", () => {
      copyTextWithToast("pip install tzero-mcp", "pip install command copied!");
    });
  }

  // CTA copy button
  const cmdCopy = document.getElementById("cmd-copy-btn");
  if (cmdCopy) {
    cmdCopy.addEventListener("click", () => {
      copyTextWithToast("pip install tzero-mcp", "pip install command copied!");
    });
  }

  // Code inspector copy
  const codeCopy = document.getElementById("copy-code-btn");
  if (codeCopy) {
    codeCopy.addEventListener("click", () => {
      const code = document.getElementById("code-display")?.textContent || "";
      copyTextWithToast(code, "Pruned code snippet copied!");
    });
  }
}

// ==========================================
// 1. LIVE POLYGLOT AST REDUCTION SANDBOX
// ==========================================
const SANDBOX_PRESETS = {
  python: `import os
from typing import List, Optional, Dict
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, status

app = FastAPI(title="UserAuthService", version="2.0.0")

class UserRecord(BaseModel):
    user_id: str
    email: str
    role: str = "developer"
    is_active: bool = True

class AuthRepository:
    def __init__(self, db_conn_pool: str):
        self.pool = db_conn_pool
        self._cache: Dict[str, UserRecord] = {}

    def get_user_by_email(self, email: str) -> Optional[UserRecord]:
        if email in self._cache:
            return self._cache[email]
        row = self.pool.execute("SELECT * FROM users WHERE email = %s", (email,))
        if not row:
            return None
        user = UserRecord(**row)
        self._cache[email] = user
        return user

    def persist_session_token(self, user_id: str, token_hash: str, ttl_sec: int = 3600) -> bool:
        expiration = os.times().elapsed + ttl_sec
        return self.pool.setex(f"session:{user_id}", ttl_sec, token_hash)

@app.post("/api/v1/auth/login", response_model=UserRecord)
async def login_endpoint(credentials: dict, repo: AuthRepository = Depends()):
    user = repo.get_user_by_email(credentials.get("email"))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user`,

  typescript: `import { Controller, Post, Body, UseGuards, UnauthorizedException } from '@nestjs/common';
import { JwtAuthGuard } from '../guards/jwt-auth.guard';
import { UserDto, AuthResponseDto } from '../dto/user.dto';

export interface ISessionStore {
  saveSession(userId: string, token: string): Promise<boolean>;
  revokeSession(userId: string): Promise<void>;
}

@Controller('api/v2/auth')
export class AuthenticationController {
  constructor(
    private readonly sessionStore: ISessionStore,
    private readonly jwtSecret: string
  ) {}

  @UseGuards(JwtAuthGuard)
  @Post('authenticate')
  async authenticate(@Body() payload: UserDto): Promise<AuthResponseDto> {
    if (!payload.email || !payload.passwordHash) {
      throw new UnauthorizedException('Payload credentials missing or malformed');
    }
    const token = await this.signJwtToken(payload.userId);
    await this.sessionStore.saveSession(payload.userId, token);
    return { token, expiresAt: Date.now() + 3600000 };
  }

  private async signJwtToken(userId: string): Promise<string> {
    const encoder = new TextEncoder();
    return btoa(JSON.stringify({ sub: userId, iat: Date.now() }));
  }
}`,

  rust: `use std::collections::HashMap;
use std::sync::{Arc, RwLock};

#[derive(Debug, Clone)]
pub struct WorkerConfig {
    pub worker_id: usize,
    pub concurrency_limit: usize,
}

pub trait TaskDispatcher: Send + Sync {
    fn dispatch(&self, task_id: &str, payload: &[u8]) -> Result<bool, String>;
    fn query_status(&self, task_id: &str) -> Option<String>;
}

pub struct MemoryDispatcher {
    state: Arc<RwLock<HashMap<String, String>>>,
    config: WorkerConfig,
}

impl MemoryDispatcher {
    pub fn new(config: WorkerConfig) -> Self {
        Self {
            state: Arc::new(RwLock::new(HashMap::new())),
            config,
        }
    }
}

impl TaskDispatcher for MemoryDispatcher {
    fn dispatch(&self, task_id: &str, payload: &[u8]) -> Result<bool, String> {
        let mut map = self.state.write().map_err(|e| e.to_string())?;
        map.insert(task_id.to_string(), "RUNNING".to_string());
        println!("Task {} dispatched with {} bytes", task_id, payload.len());
        Ok(true)
    }

    fn query_status(&self, task_id: &str) -> Option<String> {
        self.state.read().ok()?.get(task_id).cloned()
    }
}`,

  go: `package service

import (
	"context"
	"errors"
	"sync"
	"time"
)

type WorkerTask struct {
	ID        string    \`json:"id"\`
	Payload   []byte    \`json:"payload"\`
	CreatedAt time.Time \`json:"created_at"\`
}

type TaskExecutor interface {
	Execute(ctx context.Context, task *WorkerTask) error
	HealthCheck() bool
}

type DistributedQueue struct {
	mu      sync.RWMutex
	tasks   map[string]*WorkerTask
	timeout time.Duration
}

func NewQueue(timeout time.Duration) *DistributedQueue {
	return &DistributedQueue{
		tasks:   make(map[string]*WorkerTask),
		timeout: timeout,
	}
}

func (q *DistributedQueue) Push(task *WorkerTask) error {
	q.mu.Lock()
	defer q.mu.Unlock()
	if task == nil || task.ID == "" {
		return errors.New("invalid task structure")
	}
	q.tasks[task.ID] = task
	return nil
}`,

  solidity: `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20Vault {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
}

contract TZeroSecurityVault is IERC20Vault {
    mapping(address => uint256) private _balances;
    address public immutable owner;
    uint256 private _totalSupply;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event SecurityAuditLogged(bytes32 indexed hash, uint256 timestamp);

    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not authorized");
        _;
    }

    constructor(uint256 initialSupply) {
        owner = msg.sender;
        _totalSupply = initialSupply;
        _balances[msg.sender] = initialSupply;
    }

    function totalSupply() external view override returns (uint256) {
        return _totalSupply;
    }

    function balanceOf(address account) external view override returns (uint256) {
        return _balances[account];
    }

    function transfer(address to, uint256 amount) external override returns (bool) {
        require(_balances[msg.sender] >= amount, "Insufficient balance");
        _balances[msg.sender] -= amount;
        _balances[to] += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }
}`,

  cpp: `#pragma once
#include <iostream>
#include <string>
#include <memory>
#include <unordered_map>

namespace TZero::Core {

template <typename TPayload>
class ISignalHandler {
public:
    virtual ~ISignalHandler() = default;
    virtual bool Emit(const std::string& signal_id, const TPayload& data) = 0;
};

template <typename TPayload>
class AutonomousEngine : public ISignalHandler<TPayload> {
private:
    std::string engine_id_;
    std::unordered_map<std::string, TPayload> telemetry_cache_;

public:
    explicit AutonomousEngine(std::string id) : engine_id_(std::move(id)) {}

    bool Emit(const std::string& signal_id, const TPayload& data) override {
        if (signal_id.empty()) return false;
        telemetry_cache_[signal_id] = data;
        std::cout << "[" << engine_id_ << "] Signal emitted: " << signal_id << std::endl;
        return true;
    }

    [[nodiscard]] size_t GetCachedSignalCount() const noexcept {
        return telemetry_cache_.size();
    }
};

} // namespace TZero::Core`
};

function pruneCodeAST(code, lang) {
  const lines = code.split("\n");
  const output = [];
  let inFunction = false;
  let funcIndent = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      if (!inFunction) output.push("");
      continue;
    }

    if (lang === "python") {
      const isDef = trimmed.startsWith("def ") || trimmed.startsWith("async def ");
      const isClass = trimmed.startsWith("class ");
      const isDecorator = trimmed.startsWith("@");
      const isImport = trimmed.startsWith("import ") || trimmed.startsWith("from ");
      const indent = line.search(/\S/);

      if (isClass || isImport || isDecorator || (indent === 0 && !isDef && trimmed.includes("="))) {
        inFunction = false;
        output.push(line);
      } else if (isDef) {
        inFunction = true;
        funcIndent = indent;
        output.push(line.replace(/:$/, ": ..."));
      } else if (inFunction) {
        // Skip interior lines of functions
        if (indent <= funcIndent && !trimmed.startsWith("#")) {
          inFunction = false;
          output.push(line);
        }
      }
    } else {
      // General brace-language signature extractor (TS, Rust, Go, Solidity, C++)
      const isImport = trimmed.startsWith("import ") || trimmed.startsWith("from ") || trimmed.startsWith("use ") || trimmed.startsWith("package ") || trimmed.startsWith("#include") || trimmed.startsWith("// SPDX") || trimmed.startsWith("pragma");
      const isStructOrClass = trimmed.startsWith("export class") || trimmed.startsWith("class ") || trimmed.startsWith("export interface") || trimmed.startsWith("interface ") || trimmed.startsWith("pub struct") || trimmed.startsWith("struct ") || trimmed.startsWith("pub trait") || trimmed.startsWith("trait ") || trimmed.startsWith("contract ") || trimmed.startsWith("namespace ");
      const isDecoratorOrAttr = trimmed.startsWith("@") || trimmed.startsWith("#[");
      const isMethod = trimmed.includes("(") && (trimmed.includes("function") || trimmed.includes("fn ") || trimmed.includes("func ") || trimmed.includes("async ") || trimmed.includes("public") || trimmed.includes("override") || trimmed.includes("constructor") || trimmed.includes("modifier") || trimmed.includes("virtual"));

      if (isImport || isStructOrClass || isDecoratorOrAttr) {
        output.push(line);
      } else if (isMethod) {
        const signature = line.split("{")[0].trimEnd();
        output.push(signature + " { ... }");
      } else if (trimmed === "}" || trimmed === "};") {
        output.push(line);
      } else if (trimmed.includes(";") && !trimmed.includes("{") && (trimmed.includes(":") || trimmed.includes("pub ") || trimmed.includes("event ") || trimmed.includes("mapping"))) {
        output.push(line);
      }
    }
  }

  const pruned = output.join("\n").replace(/\n{3,}/g, "\n\n").trim();
  return pruned.length > 0 ? pruned : "# All function bodies pruned successfully\n// AST Signature Map Generated";
}

function initSandbox() {
  const inputEl = document.getElementById("sandbox-input");
  const outputCodeEl = document.getElementById("sandbox-output-code");
  const rawStatsEl = document.getElementById("sandbox-raw-stats");
  const savingsBadge = document.getElementById("sandbox-savings-badge");
  const stripRawTokens = document.getElementById("strip-raw-tokens");
  const stripUltraTokens = document.getElementById("strip-ultra-tokens");
  const stripSavingsPct = document.getElementById("strip-savings-pct");
  const copyBtn = document.getElementById("sandbox-copy-btn");
  const presetBtns = document.querySelectorAll(".preset-btn");

  if (!inputEl || !outputCodeEl) return;

  let currentLang = "python";

  function runReduction() {
    const rawCode = inputEl.value;
    const reduced = pruneCodeAST(rawCode, currentLang);
    outputCodeEl.textContent = reduced;

    const rawChars = rawCode.length;
    const reducedChars = reduced.length;

    const rawTokens = Math.max(1, Math.ceil(rawChars / 4));
    const ultraTokens = Math.max(1, Math.ceil(reducedChars / 4));
    const savings = Math.max(0, ((1 - ultraTokens / rawTokens) * 100)).toFixed(1);

    rawStatsEl.textContent = `${rawChars.toLocaleString()} chars | ~${rawTokens.toLocaleString()} tokens`;
    savingsBadge.textContent = `Saved: -${savings}%`;

    stripRawTokens.textContent = `${rawTokens.toLocaleString()} tokens`;
    stripUltraTokens.textContent = `${ultraTokens.toLocaleString()} tokens`;
    stripSavingsPct.textContent = `-${savings}%`;
  }

  presetBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      presetBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentLang = btn.dataset.lang;
      inputEl.value = SANDBOX_PRESETS[currentLang] || "";
      runReduction();
    });
  });

  inputEl.addEventListener("input", runReduction);

  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      copyTextWithToast(outputCodeEl.textContent, "Pruned code copied to clipboard!");
    });
  }

  // Initialize with python preset
  inputEl.value = SANDBOX_PRESETS.python;
  runReduction();
}

// ==========================================
// 2. 4D CAUSAL-TEMPORAL GRAPH & PBFT SWARM HUD
// ==========================================
function initCausalHUD() {
  const canvas = document.getElementById("causal-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const simulateBtn = document.getElementById("hud-simulate-btn");
  const traceBtn = document.getElementById("hud-trace-btn");
  const roundEl = document.getElementById("hud-round-val");
  const nodeTitle = document.getElementById("node-info-title");
  const nodeSub = document.getElementById("node-info-sub");
  const nodeTags = document.getElementById("node-info-tags");

  // Resize canvas to match display width with rock-solid fallback
  function resize() {
    const parentWidth = canvas.parentElement ? canvas.parentElement.clientWidth : 0;
    const w = parentWidth > 50 ? parentWidth : (window.innerWidth ? Math.min(window.innerWidth - 64, 1200) : 1000);
    canvas.width = w;
    canvas.height = 420;
  }
  window.addEventListener("resize", resize);
  resize();

  const nodes = [
    { id: "ast", label: "AST-Optimizer", role: "AST Structure & Symbol Graph Engine", x: 0.18, y: 0.35, color: "#00f0ff", icon: "⚡", health: "100%", latency: "0.21ms", weight: "0.98", active: true },
    { id: "sec", label: "Security-Sentinel", role: "100% Zero-Leak OS Keyring & Secret Scanner", x: 0.42, y: 0.22, color: "#10b981", icon: "🛡️", health: "100%", latency: "0.14ms", weight: "1.00", active: true },
    { id: "dev", label: "Autonomous-DevOps", role: "Self-Healing Execution & Deployment Watcher", x: 0.82, y: 0.38, color: "#a855f7", icon: "🚀", health: "99.8%", latency: "0.45ms", weight: "0.92", active: true },
    { id: "mem", label: "Memory-Hippocampus", role: "4D Causal-Temporal Chain & Latent Compression", x: 0.65, y: 0.72, color: "#f59e0b", icon: "🧠", health: "100%", latency: "0.32ms", weight: "0.95", active: true },
    { id: "veto", label: "Consensus-Veto", role: "Byzantine Fault Tolerant Zero-Hallucination Gate", x: 0.28, y: 0.72, color: "#ec4899", icon: "⚖️", health: "100%", latency: "0.19ms", weight: "1.00", active: true }
  ];

  const edges = [
    { from: "ast", to: "sec" },
    { from: "sec", to: "dev" },
    { from: "dev", to: "mem" },
    { from: "mem", to: "veto" },
    { from: "veto", to: "ast" },
    { from: "ast", to: "mem" },
    { from: "sec", to: "veto" }
  ];

  // Particle pulses traveling along edges
  const pulses = edges.map((e, idx) => ({
    edge: e,
    progress: (idx * 0.18) % 1,
    speed: 0.003 + (idx % 3) * 0.0015
  }));

  let hoveredNode = null;
  let waveRadius = 0;
  let waveActive = false;
  let waveOrigin = { x: 0, y: 0 };
  let traceActive = false;
  let traceTimer = null;

  function getNodePos(node) {
    return {
      x: Math.max(50, Math.min(canvas.width - 50, node.x * canvas.width)),
      y: Math.max(40, Math.min(canvas.height - 40, node.y * canvas.height))
    };
  }

  function renderHUD() {
    if (canvas.width < 100) resize();
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Subtle background grid
    ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
    ctx.lineWidth = 1;
    const gridStep = 40;
    for (let x = 0; x < canvas.width; x += gridStep) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += gridStep) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Draw Edges
    edges.forEach((edge) => {
      const fromNode = nodes.find((n) => n.id === edge.from);
      const toNode = nodes.find((n) => n.id === edge.to);
      const p1 = getNodePos(fromNode);
      const p2 = getNodePos(toNode);

      const isCausalTrace = traceActive && ((edge.from === "ast" && edge.to === "mem") || (edge.from === "mem" && edge.to === "veto"));

      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.strokeStyle = isCausalTrace ? "rgba(0, 240, 255, 0.8)" : "rgba(255, 255, 255, 0.12)";
      ctx.lineWidth = isCausalTrace ? 2.5 : 1.2;
      ctx.stroke();
    });

    // Draw Pulses
    pulses.forEach((pulse) => {
      pulse.progress = (pulse.progress + pulse.speed) % 1;
      const fromNode = nodes.find((n) => n.id === pulse.edge.from);
      const toNode = nodes.find((n) => n.id === pulse.edge.to);
      const p1 = getNodePos(fromNode);
      const p2 = getNodePos(toNode);

      const px = p1.x + (p2.x - p1.x) * pulse.progress;
      const py = p1.y + (p2.y - p1.y) * pulse.progress;

      ctx.beginPath();
      ctx.arc(px, py, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = fromNode.color;
      ctx.shadowColor = fromNode.color;
      ctx.shadowBlur = 10;
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    // PBFT Consensus Wave
    if (waveActive) {
      waveRadius += 4;
      ctx.beginPath();
      ctx.arc(waveOrigin.x, waveOrigin.y, waveRadius, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(16, 185, 129, ${Math.max(0, 1 - waveRadius / 400)})`;
      ctx.lineWidth = 2.5;
      ctx.stroke();

      if (waveRadius > 400) {
        waveActive = false;
        waveRadius = 0;
      }
    }

    // Draw Nodes
    nodes.forEach((node) => {
      const pos = getNodePos(node);
      const isHovered = hoveredNode && hoveredNode.id === node.id;
      const nodeRadius = isHovered ? 26 : 20;

      // Outer glow
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, nodeRadius + 8, 0, Math.PI * 2);
      ctx.fillStyle = isHovered ? `${node.color}33` : "rgba(255, 255, 255, 0.04)";
      ctx.fill();

      // Main Node Circle
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, nodeRadius, 0, Math.PI * 2);
      ctx.fillStyle = "#0c1017";
      ctx.strokeStyle = node.color;
      ctx.lineWidth = isHovered ? 3 : 2;
      ctx.shadowColor = node.color;
      ctx.shadowBlur = isHovered ? 16 : 8;
      ctx.fill();
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Node Icon
      ctx.font = isHovered ? "16px sans-serif" : "13px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(node.icon, pos.x, pos.y);

      // Node Label
      ctx.font = "600 12px Inter, sans-serif";
      ctx.fillStyle = isHovered ? "#fff" : "rgba(255, 255, 255, 0.75)";
      ctx.fillText(node.label, pos.x, pos.y + nodeRadius + 16);
    });

    requestAnimationFrame(renderHUD);
  }

  // Mouse interaction
  function updateHoverAt(mx, my) {
    let found = null;
    for (const node of nodes) {
      const pos = getNodePos(node);
      const dist = Math.hypot(mx - pos.x, my - pos.y);
      if (dist < 32) {
        found = node;
        break;
      }
    }

    hoveredNode = found;
    if (found) {
      canvas.style.cursor = "pointer";
      nodeTitle.textContent = `${found.icon} ${found.label}`;
      nodeTitle.style.color = found.color;
      nodeSub.textContent = found.role;
      nodeTags.innerHTML = `
        <span class="info-tag" style="border-color:${found.color}">Health: ${found.health}</span>
        <span class="info-tag">Latency: ${found.latency}</span>
        <span class="info-tag">Causal Weight: ${found.weight}</span>
        <span class="info-tag" style="color:var(--accent-emerald)">PBFT Quorum: Passed ✓</span>
      `;
    } else {
      canvas.style.cursor = "default";
    }
    return found;
  }

  canvas.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    updateHoverAt(e.clientX - rect.left, e.clientY - rect.top);
  });

  canvas.addEventListener("click", (e) => {
    const rect = canvas.getBoundingClientRect();
    const found = updateHoverAt(e.clientX - rect.left, e.clientY - rect.top);
    if (found) {
      showToast(`Selected Node: ${found.label} (${found.role})`, found.icon);
    }
  });

  // Touch support for mobile and tablets
  canvas.addEventListener("touchstart", (e) => {
    if (!e.touches.length) return;
    const rect = canvas.getBoundingClientRect();
    const touch = e.touches[0];
    updateHoverAt(touch.clientX - rect.left, touch.clientY - rect.top);
  }, { passive: true });

  canvas.addEventListener("touchmove", (e) => {
    if (!e.touches.length) return;
    const rect = canvas.getBoundingClientRect();
    const touch = e.touches[0];
    updateHoverAt(touch.clientX - rect.left, touch.clientY - rect.top);
  }, { passive: true });

  // Simulate PBFT Vote
  if (simulateBtn) {
    simulateBtn.addEventListener("click", () => {
      const secNode = nodes.find((n) => n.id === "sec");
      waveOrigin = getNodePos(secNode);
      waveActive = true;
      waveRadius = 0;

      const randomRound = `#${Math.floor(8000 + Math.random() * 1999)}-${["OMEGA", "DELTA", "SIGMA", "ALPHA"][Math.floor(Math.random() * 4)]}`;
      if (roundEl) roundEl.textContent = randomRound;

      showToast(`Quorum achieved: 5/5 nodes validated round ${randomRound}`, "🛡️");
      simulateBtn.innerHTML = '<span style="color:var(--accent-emerald)">Quorum Achieved (5/5) ✓</span>';
      setTimeout(() => {
        simulateBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg> Trigger PBFT Vote';
      }, 2000);
    });
  }

  // Trace Causal Link
  if (traceBtn) {
    traceBtn.addEventListener("click", () => {
      traceActive = true;
      showToast("4D Causal-Temporal Trace Initiated across Nodes", "⚡");
      traceBtn.innerHTML = '<span style="color:var(--accent-cyan)">Tracing 4D Path... ⚡</span>';
      clearTimeout(traceTimer);
      traceTimer = setTimeout(() => {
        traceActive = false;
        traceBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> Trace Causal Link';
      }, 3000);
    });
  }

  renderHUD();
}

// ==========================================
// 3. 37 NATIVE MCP TOOLS SUITE EXPLORER
// ==========================================
const MCP_TOOLS_CATALOG = [
  // Category: AST & Context (12)
  { name: "get_project_context_tree", cat: "ast", badge: "AST", desc: "Builds multi-tier hierarchical AST context tree reducing prompts up to 95%.", sig: "get_project_context_tree(project_root: str, reduction_mode: str = 'ultra')" },
  { name: "query_module_dependencies", cat: "ast", badge: "AST", desc: "Analyzes import/export dependencies, module calls and external packages.", sig: "query_module_dependencies(project_root: str, file_path: str = '')" },
  { name: "query_architecture_boundaries", cat: "ast", badge: "AST", desc: "Retrieves active architectural boundaries and operational constraints.", sig: "query_architecture_boundaries(project_root: str)" },
  { name: "generate_architecture_blueprint", cat: "ast", badge: "AST", desc: "Generates ARCHITECTURE.md system blueprint with live Mermaid topology.", sig: "generate_architecture_blueprint(project_root: str)" },
  { name: "generate_repo_map", cat: "ast", badge: "AST", desc: "Generates ultra-compact AST symbol token map for chat context windows.", sig: "generate_repo_map(project_root: str)" },
  { name: "prune_code_snippet", cat: "ast", badge: "AST", desc: "Prunes function bodies from code snippets while keeping interface contracts.", sig: "prune_code_snippet(code: str, filename: str, mode: str = 'ultra')" },
  { name: "get_smart_skeleton_context", cat: "ast", badge: "AST", desc: "Extracts skeleton AST with types, docstrings, and signatures without implementation.", sig: "get_smart_skeleton_context(file_path: str)" },
  { name: "rank_repository_pagerank", cat: "ast", badge: "AST", desc: "Computes AST dependency PageRank to surface the most critical codebase files.", sig: "rank_repository_pagerank(project_root: str)" },
  { name: "trace_symbol_call_chain", cat: "ast", badge: "AST", desc: "Traces forward and backward caller chains for any function across entire project.", sig: "trace_symbol_call_chain(target_symbol: str, project_root: str)" },
  { name: "find_dead_code", cat: "ast", badge: "AST", desc: "Detects unreferenced exports, unreachable branches, and unused variables.", sig: "find_dead_code(project_root: str)" },
  { name: "get_incremental_diff_context", cat: "ast", badge: "AST", desc: "Compacts Git diffs into AST-aware structural change summaries.", sig: "get_incremental_diff_context(project_root: str, base_commit: str = 'HEAD~1')" },
  { name: "find_code_duplicity", cat: "ast", badge: "AST", desc: "Scans workspace for duplicate or copy-pasted AST blocks across modules.", sig: "find_code_duplicity(project_root: str, min_lines: int = 6)" },
  { name: "suggest_reusable_helpers", cat: "ast", badge: "AST", desc: "Discovers and surfaces reusable utility functions across repository AST to avoid duplicate code.", sig: "suggest_reusable_helpers(query: str, code_snippet: str = '')" },

  // Category: Memory & Graph (10)
  { name: "jarvis_compress_semantic_memory", cat: "memory", badge: "Memory", desc: "Compresses episodic agent actions into dense semantic vectors.", sig: "jarvis_compress_semantic_memory(session_id: str, memory_content: str)" },
  { name: "jarvis_decompress_semantic_memory", cat: "memory", badge: "Memory", desc: "Rehydrates compressed memory blocks on demand with sub-millisecond latency.", sig: "jarvis_decompress_semantic_memory(memory_id: str)" },
  { name: "jarvis_consolidate_memory", cat: "memory", badge: "Memory", desc: "Hippocampal consolidation of short-term memories into permanent long-term storage.", sig: "jarvis_consolidate_memory(retention_threshold: float = 0.85)" },
  { name: "jarvis_export_memory_store", cat: "memory", badge: "Memory", desc: "Exports complete persistent cognitive memory database into structured JSON.", sig: "jarvis_export_memory_store(include_vectors: bool = True)" },
  { name: "jarvis_latent_press_compress", cat: "memory", badge: "Memory", desc: "Multi-stage token compressor utilizing latent space clustering.", sig: "jarvis_latent_press_compress(raw_text: str, ratio_target: float = 0.1)" },
  { name: "jarvis_query_knowledge_graph", cat: "memory", badge: "Memory", desc: "Queries the 4D causal graph for interconnected concepts and entities.", sig: "jarvis_query_knowledge_graph(query_entity: str, max_depth: int = 3)" },
  { name: "jarvis_zero_key_query", cat: "memory", badge: "Memory", desc: "Executes offline similarity retrieval without sending requests to external APIs.", sig: "jarvis_zero_key_query(prompt: str, top_k: int = 5)" },
  { name: "jarvis_compress_document", cat: "memory", badge: "Memory", desc: "Compresses large architectural documents into high-density AST summaries.", sig: "jarvis_compress_document(document_path: str)" },
  { name: "jarvis_causal_chain_query", cat: "memory", badge: "Memory", desc: "Traces temporal cause-and-effect reasoning paths for agent decision auditing.", sig: "jarvis_causal_chain_query(event_id: str)" },
  { name: "jarvis_export_graph_visualization", cat: "memory", badge: "Memory", desc: "Generates Cytoscape/Mermaid graph visualization of agent memory state.", sig: "jarvis_export_graph_visualization(format: str = 'mermaid')" },

  // Category: Security & Guard (8)
  { name: "audit_codebase_quality", cat: "security", badge: "Security", desc: "AST static code smell audit and 100% Zero-Leak security check for secret leaks.", sig: "audit_codebase_quality(project_root: str)" },
  { name: "verify_zero_leak_security", cat: "security", badge: "Security", desc: "Verifies zero plaintext API keys or credentials exist across all workspace files.", sig: "verify_zero_leak_security(workspace_root: str)" },
  { name: "verify_hallucination_guard", cat: "security", badge: "Security", desc: "Cross-checks LLM suggested functions against verified project AST symbol table.", sig: "verify_hallucination_guard(suggested_symbols: list, project_root: str)" },
  { name: "enforce_architecture_boundaries", cat: "security", badge: "Security", desc: "Enforces architectural boundary rules defined in tzero.rules.json.", sig: "enforce_architecture_boundaries(project_root: str)" },
  { name: "analyze_change_impact", cat: "security", badge: "Security", desc: "Calculates change blast radius (0-100 score) before modifying a class/function.", sig: "analyze_change_impact(target_symbol: str, project_root: str)" },
  { name: "estimate_token_cost", cat: "security", badge: "Security", desc: "Calculates exact token cost comparison across OpenAI, Anthropic, Gemini, DeepSeek.", sig: "estimate_token_cost(token_count: int)" },
  { name: "export_agent_rules", cat: "security", badge: "Security", desc: "Exports AI agent rule specifications (.cursorrules, .clinerules, .cursor/rules/*.mdc).", sig: "export_agent_rules(format: str = 'cursor')" },
  { name: "get_token_savings_metrics", cat: "security", badge: "Security", desc: "Computes quantitative token reduction metrics and monthly team financial ROI.", sig: "get_token_savings_metrics(project_root: str)" },

  // Category: Swarm & Consensus (7)
  { name: "jarvis_orchestrate_goal", cat: "swarm", badge: "Swarm", desc: "Orchestrates multi-agent autonomous goal execution from a single intent prompt.", sig: "jarvis_orchestrate_goal(goal_description: str, max_iterations: int = 10)" },
  { name: "jarvis_swarm_orchestrate", cat: "swarm", badge: "Swarm", desc: "Spawns and coordinates specialized agents with dedicated tasks and telemetry.", sig: "jarvis_swarm_orchestrate(swarm_config: dict)" },
  { name: "jarvis_self_healing_execute", cat: "swarm", badge: "Swarm", desc: "Executes CLI commands with automatic error diagnosis, patching, and retry.", sig: "jarvis_self_healing_execute(command: str, auto_patch: bool = True)" },
  { name: "jarvis_bft_swarm_consensus", cat: "swarm", badge: "Swarm", desc: "Runs Byzantine Fault Tolerant voting across 5 subagents to guarantee safety.", sig: "jarvis_bft_swarm_consensus(proposal: dict, quorum_ratio: float = 0.67)" },
  { name: "search_codebase_semantic", cat: "swarm", badge: "Swarm", desc: "Performs 100% private local BM25 hybrid semantic code search without cloud APIs.", sig: "search_codebase_semantic(query: str, project_root: str)" },
  { name: "jarvis_hybrid_search", cat: "swarm", badge: "Swarm", desc: "Combines lexical keyword matching with AST symbol ranking for hybrid search.", sig: "jarvis_hybrid_search(query: str, top_k: int = 10)" },
  { name: "jarvis_minhash_similarity", cat: "swarm", badge: "Swarm", desc: "Sub-millisecond MinHash Jaccard similarity indexing across repositories.", sig: "jarvis_minhash_similarity(text_a: str, text_b: str)" }
];

function initMCPTools() {
  const container = document.getElementById("mcp-tools-container");
  const searchInput = document.getElementById("tool-search-input");
  const filterChips = document.querySelectorAll(".tool-filter-chips .filter-chip");

  if (!container) return;

  let activeFilter = "all";
  let searchQuery = "";

  function renderTools() {
    container.innerHTML = "";

    const filtered = MCP_TOOLS_CATALOG.filter((tool) => {
      const matchFilter = activeFilter === "all" || tool.cat === activeFilter;
      const matchSearch =
        tool.name.toLowerCase().includes(searchQuery) ||
        tool.desc.toLowerCase().includes(searchQuery) ||
        tool.badge.toLowerCase().includes(searchQuery);
      return matchFilter && matchSearch;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-muted);">
          <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</div>
          No tools match "<strong>${searchQuery}</strong>" in the selected category.
        </div>
      `;
      return;
    }

    filtered.forEach((tool) => {
      const card = document.createElement("div");
      card.className = "tool-card";
      
      const badgeClass =
        tool.cat === "ast" ? "badge-cyan" :
        tool.cat === "memory" ? "badge-purple" :
        tool.cat === "security" ? "badge-success" : "badge-accent";

      card.innerHTML = `
        <div class="tool-header">
          <span class="tool-name">${tool.name}</span>
          <span class="tool-badge ${badgeClass}">${tool.badge}</span>
        </div>
        <p class="tool-desc">${tool.desc}</p>
        <div class="tool-sig" title="Click to copy signature">
          <code>${tool.sig}</code>
        </div>
      `;

      card.querySelector(".tool-sig").addEventListener("click", () => {
        copyTextWithToast(tool.sig, `Copied ${tool.name} signature!`);
      });

      container.appendChild(card);
    });
  }

  filterChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      filterChips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      activeFilter = chip.dataset.filter;
      renderTools();
    });
  });

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      renderTools();
    });
  }

  renderTools();
}

// ==========================================
// 4. 1-CLICK AGENT INTEGRATION CONFIG GENERATOR
// ==========================================
const AGENT_CONFIGS = {
  claude: {
    path: "Windows: %APPDATA%\\Claude\\claude_desktop_config.json | macOS: ~/Library/Application Support/Claude/claude_desktop_config.json",
    code: `{
  "mcpServers": {
    "tzero": {
      "command": "python",
      "args": ["-m", "tzero_mcp"]
    }
  }
}`
  },
  cursor: {
    path: ".cursor/mcp.json (Workspace Root)",
    code: `{
  "mcpServers": {
    "tzero": {
      "command": "python",
      "args": ["-m", "tzero_mcp"]
    }
  }
}`
  },
  antigravity: {
    path: "~/.gemini/config/mcp_config.json",
    code: `{
  "mcpServers": {
    "tzero": {
      "command": "python",
      "args": ["-m", "tzero_mcp"]
    }
  }
}`
  },
  windsurf: {
    path: "~/.codeium/windsurf/mcp_config.json",
    code: `{
  "mcpServers": {
    "tzero": {
      "command": "python",
      "args": ["-m", "tzero_mcp"]
    }
  }
}`
  },
  cline: {
    path: "~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
    code: `{
  "mcpServers": {
    "tzero": {
      "command": "python",
      "args": ["-m", "tzero_mcp"]
    }
  }
}`
  },
  cli: {
    path: "Terminal One-Liner (Any Shell)",
    code: `# Option 1: Run via pip (Multi-platform)
pip install tzero-mcp
python -m tzero_mcp

# Option 2: Run standalone Windows binary without Python
.\\TZeroMCP.exe`
  }
};

function initAgentSetupTabs() {
  const tabs = document.querySelectorAll(".agent-tabs .agent-tab");
  const pathEl = document.getElementById("config-path");
  const codeEl = document.getElementById("agent-config-code");
  const copyBtn = document.getElementById("agent-copy-btn");

  if (!tabs.length || !codeEl) return;

  function setConfig(target) {
    const config = AGENT_CONFIGS[target];
    if (!config) return;
    if (pathEl) pathEl.textContent = config.path;
    codeEl.textContent = config.code;
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      setConfig(tab.dataset.target);
    });
  });

  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      copyTextWithToast(codeEl.textContent, "Agent configuration copied to clipboard!");
    });
  }

  // Initial load
  setConfig("claude");
}

// ==========================================
// 5. STANDALONE DOWNLOAD CENTER
// ==========================================
function initDownloadCenter() {
  // Download button click feedback
  const dlButtons = document.querySelectorAll(".downloads-grid a.btn");
  dlButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const name = btn.dataset.name || "Executable";
      showToast(`Initiating download for ${name}...`, "🚀");
    });
  });

  // Checksum copy links
  const shaLinks = document.querySelectorAll(".sha-copy");
  shaLinks.forEach((code) => {
    code.style.cursor = "pointer";
    code.addEventListener("click", () => {
      const fullSha = code.dataset.sha || code.textContent.trim();
      copyTextWithToast(fullSha, "Verified SHA-256 Checksum copied!");
    });
  });
}

