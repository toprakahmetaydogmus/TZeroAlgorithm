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
function initParticleSystem() {
  const canvas = document.getElementById("hero-canvas");
  if (!canvas || typeof THREE === "undefined") return;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // Particle system
  const particleCount = 800;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(particleCount * 3);
  const velocities = new Float32Array(particleCount * 3);
  const colors = new Float32Array(particleCount * 3);
  const sizes = new Float32Array(particleCount);

  const cyanColor = new THREE.Color(0x00f0ff);
  const purpleColor = new THREE.Color(0xa855f7);
  const emeraldColor = new THREE.Color(0x10b981);

  for (let i = 0; i < particleCount; i++) {
    const i3 = i * 3;
    positions[i3] = (Math.random() - 0.5) * 40;
    positions[i3 + 1] = (Math.random() - 0.5) * 30;
    positions[i3 + 2] = (Math.random() - 0.5) * 20 - 5;

    velocities[i3] = (Math.random() - 0.5) * 0.005;
    velocities[i3 + 1] = (Math.random() - 0.5) * 0.005;
    velocities[i3 + 2] = (Math.random() - 0.5) * 0.003;

    const colorChoice = Math.random();
    let color;
    if (colorChoice < 0.5) color = cyanColor;
    else if (colorChoice < 0.8) color = purpleColor;
    else color = emeraldColor;

    colors[i3] = color.r;
    colors[i3 + 1] = color.g;
    colors[i3 + 2] = color.b;

    sizes[i] = Math.random() * 3 + 0.5;
  }

  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute("size", new THREE.BufferAttribute(sizes, 1));

  const material = new THREE.PointsMaterial({
    size: 2,
    vertexColors: true,
    transparent: true,
    opacity: 0.6,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true,
    depthWrite: false,
  });

  const particles = new THREE.Points(geometry, material);
  scene.add(particles);

  // Connection lines
  const lineGeometry = new THREE.BufferGeometry();
  const linePositions = new Float32Array(particleCount * 6);
  const lineColors = new Float32Array(particleCount * 6);
  lineGeometry.setAttribute("position", new THREE.BufferAttribute(linePositions, 3));
  lineGeometry.setAttribute("color", new THREE.BufferAttribute(lineColors, 3));
  
  const lineMaterial = new THREE.LineBasicMaterial({
    vertexColors: true,
    transparent: true,
    opacity: 0.15,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
  scene.add(lines);

  camera.position.z = 15;

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

      // Boundaries
      if (Math.abs(posArr[i3]) > 20) velocities[i3] *= -1;
      if (Math.abs(posArr[i3 + 1]) > 15) velocities[i3 + 1] *= -1;
      if (Math.abs(posArr[i3 + 2] + 5) > 10) velocities[i3 + 2] *= -1;
    }

    // Update connections
    lineIndex = 0;
    const lp = lines.geometry.attributes.position.array;
    const lc = lines.geometry.attributes.color.array;
    const maxDist = 4;

    for (let i = 0; i < Math.min(particleCount, 100); i++) {
      for (let j = i + 1; j < Math.min(particleCount, 100); j++) {
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

    // Smooth mouse follow
    particles.rotation.y += (mouseX * 0.1 - particles.rotation.y) * 0.02;
    particles.rotation.x += (-mouseY * 0.05 - particles.rotation.x) * 0.02;
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
// NAVBAR SCROLL EFFECT
// ==========================================
function initNavbarScroll() {
  const navbar = document.getElementById("navbar");
  if (!navbar) return;

  let lastScroll = 0;
  window.addEventListener("scroll", () => {
    const currentScroll = window.scrollY;
    if (currentScroll > 50) {
      navbar.classList.add("scrolled");
    } else {
      navbar.classList.remove("scrolled");
    }
    lastScroll = currentScroll;
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
  initParticleSystem();
  initScrollAnimations();
  initNavbarScroll();
  initCounterAnimation();
  renderBenchmarkTable();
  renderVisualBars();
  initInspector();
  initCalculator();
  initCopyButtons();
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
// AST INSPECTOR
// ==========================================
let currentFile = "tzero_v3.py";
let currentMode = "ultra";

function initInspector() {
  const fileTabs = document.querySelectorAll("#file-tabs .tab-btn");
  const modeTabs = document.querySelectorAll("#mode-tabs .mode-btn");

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
  const data = BENCHMARK_DATA.find(d => d.file === currentFile) || BENCHMARK_DATA[0];
  const display = document.getElementById("code-display");
  const filenameEl = document.getElementById("active-filename");
  const tokensEl = document.getElementById("active-tokens");
  const reductionEl = document.getElementById("active-reduction");
  const titleEl = document.getElementById("editor-title");

  filenameEl.textContent = data.file;

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

  let currentModelCost = 2.50;

  modelChips.forEach(chip => {
    chip.addEventListener("click", () => {
      modelChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      currentModelCost = parseFloat(chip.dataset.cost);
      calculateROI();
    });
  });

  reqSlider.addEventListener("input", (e) => {
    reqVal.textContent = `${parseInt(e.target.value).toLocaleString()} requests`;
    calculateROI();
  });

  devSlider.addEventListener("input", (e) => {
    devVal.textContent = `${e.target.value} people`;
    calculateROI();
  });

  function calculateROI() {
    const monthlyRequestsPerDev = parseInt(reqSlider.value);
    const devCount = parseInt(devSlider.value);
    const totalRequests = monthlyRequestsPerDev * devCount;

    const rawTokensPerReq = 102265;
    const tzeroTokensPerReq = 5274;

    const totalRawTokens = totalRequests * rawTokensPerReq;
    const totalTzeroTokens = totalRequests * tzeroTokensPerReq;

    const monthlyRawCost = (totalRawTokens / 1000000) * currentModelCost;
    const monthlyTzeroCost = (totalTzeroTokens / 1000000) * currentModelCost;
    const monthlySavings = monthlyRawCost - monthlyTzeroCost;
    const annualSavings = monthlySavings * 12;

    document.getElementById("calc-raw-tokens").textContent = `${totalRawTokens.toLocaleString()} tokens`;
    document.getElementById("calc-tzero-tokens").textContent = `${totalTzeroTokens.toLocaleString()} tokens`;
    
    document.getElementById("calc-raw-cost").textContent = `$${monthlyRawCost.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / mo`;
    document.getElementById("calc-tzero-cost").textContent = `$${monthlyTzeroCost.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / mo`;
    
    document.getElementById("calc-annual-savings").textContent = `$${annualSavings.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / YEAR`;
  }

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
      navigator.clipboard.writeText("pip install tzero-mcp").then(() => {
        heroCopy.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-emerald)" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>';
        setTimeout(() => {
          heroCopy.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>';
        }, 2000);
      });
    });
  }

  // CTA copy button
  const cmdCopy = document.getElementById("cmd-copy-btn");
  if (cmdCopy) {
    cmdCopy.addEventListener("click", () => {
      navigator.clipboard.writeText("pip install tzero-mcp").then(() => {
        cmdCopy.textContent = "Copied! ✓";
        setTimeout(() => cmdCopy.textContent = "Copy", 2000);
      });
    });
  }

  // Code inspector copy
  const codeCopy = document.getElementById("copy-code-btn");
  if (codeCopy) {
    codeCopy.addEventListener("click", () => {
      const code = document.getElementById("code-display").textContent;
      navigator.clipboard.writeText(code).then(() => {
        codeCopy.textContent = "Copied! ✓";
        setTimeout(() => codeCopy.textContent = "Copy", 2000);
      });
    });
  }
}
