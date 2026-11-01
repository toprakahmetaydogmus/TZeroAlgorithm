// ==========================================
// 6. T-ZERO NEURAL CORTEX & 105 MATRIX LAB
// ==========================================

const CORTEX_FLEET_AGENTS = [
  { id: "agent_sec", name: "SecuritySentinelAgent", icon: "🛡️", color: "#10b981", role: "Zero-Leak OS Vaults & Keyring Defense", scope: "100% Zero-Leak Guard, entropy secret analysis, token shielding", tags: ["security", "zero-leak", "keyring"] },
  { id: "agent_ast", name: "ASTArchitectAgent", icon: "⚡", color: "#00f0ff", role: "AST Skeletonization & 95% Token Pruning", scope: "Universal Tree-sitter + LSP CST parsing, interface contract extraction", tags: ["ast", "tree-sitter", "pruning"] },
  { id: "agent_purger", name: "DeadCodePurgerAgent", icon: "🧹", color: "#fb7185", role: "Orphan Symbol & Unreachable Branch Purging", scope: "Dead code elimination, unreferenced symbol pruning, DAG sweep", tags: ["dead-code", "dag", "optimization"] },
  { id: "agent_test", name: "TestSynthesizerAgent", icon: "🧪", color: "#38bdf8", role: "Property-Based Mutation Unit Tests", scope: "Autonomous test generation, mutation verification, boundary fuzzing", tags: ["testing", "mutation", "fuzzing"] },
  { id: "agent_poly", name: "PolyglotTranspilerAgent", icon: "🌐", color: "#f59e0b", role: "Cross-Language Boundary & FFI Resolution", scope: "Python/C++/Rust WASM/REST/gRPC boundary tracking, polyglot call graph", tags: ["ffi", "polyglot", "wasm"] },
  { id: "agent_bug", name: "BugHunterAgent", icon: "🔍", color: "#ec4899", role: "AST Causal Trace & Stack Dump Autopsy", scope: "Crash dump autopsy, non-breaking logpoint injection, root-cause tree", tags: ["debugging", "autopsy", "causal"] },
  { id: "agent_perf", name: "PerformanceProfilerAgent", icon: "⏱️", color: "#a855f7", role: "Live CPU Flamegraphs & Micro-benchmarks", scope: "Live CPU flamegraphing, performance regression barriers, bottleneck alert", tags: ["profiler", "flamegraph", "performance"] },
  { id: "agent_doc", name: "DocstringGeneratorAgent", icon: "📝", color: "#34d399", role: "AST Type Inlining & Docstring Alignment", scope: "Inferred type inlining, doc-code synchronization, automatic ADR logging", tags: ["documentation", "types", "adr"] },
  { id: "agent_dep", name: "DependencyAuditorAgent", icon: "📦", color: "#f43f5e", role: "Lockfile Drift & Conflict Simulator", scope: "Dependency collision simulator, environment drift detection, CVE audit", tags: ["dependencies", "drift", "audit"] },
  { id: "agent_refactor", name: "RefactorModernizerAgent", icon: "🛠️", color: "#60a5fa", role: "Surgical AST Patching & Clone Deduplication", scope: "AST node replacement, Type-3/4 clone detection, atomic batch refactoring", tags: ["refactor", "clones", "ast-patch"] },
  { id: "agent_guard", name: "HallucinationValidatorAgent", icon: "⚖️", color: "#e11d48", role: "Pre-Flight Reality-Lock AST Validation", scope: "Zero-hallucination verification, Levenshtein method fuzzy match, reality-lock", tags: ["hallucination", "guard", "reality-lock"] },
  { id: "agent_devops", name: "DevOpsReleaseAgent", icon: "🚀", color: "#8b5cf6", role: "Zero-Roundtrip DAG Execution & CI/CD Guard", scope: "DAG execution engine, semantic changelog generation, standalone binary release", tags: ["devops", "dag", "orchestration"] }
];

const CORTEX_PILLAR_HUBS = [
  { id: "pillar_1", num: 1, name: "I. Compiler & AST", icon: "⚙️", color: "#8b5cf6", desc: "Universal Tree-sitter + LSP CST parsing, DAG calls, surgical patching." },
  { id: "pillar_2", num: 2, name: "II. Matryoshka Token", icon: "💎", color: "#00f0ff", desc: "L0-L3 resolution zoomer, PageRank context, BM25 hybrid search." },
  { id: "pillar_3", num: 3, name: "III. Shadow Workspace", icon: "🌌", color: "#10b981", desc: "Memory CoW OverlayFS, ACID rollback, mutation testing, fuzzing." },
  { id: "pillar_4", num: 4, name: "IV. Runtime Telemetry", icon: "📡", color: "#f59e0b", desc: "Autonomous DAP debugger, CPU flamegraph, crash autopsy, loop watchdog." },
  { id: "pillar_5", num: 5, name: "V. Orchestration DAG", icon: "⚡", color: "#ec4899", desc: "Zero-roundtrip DAG runner, dynamic self-writing meta-tools, Unix pipe." },
  { id: "pillar_6", num: 6, name: "VI. Cognitive Memory", icon: "🧠", color: "#a855f7", desc: "Persistent knowledge graph, episodic bug memory, developer DNA cloner." },
  { id: "pillar_7", num: 7, name: "VII. Hardware & Security", icon: "🛡️", color: "#f43f5e", desc: "Hardware-in-the-loop, zero-leak scrubber, prompt injection shield, single-binary." }
];

function initNeuralCortex() {
  initCortexTabs();
  initCortexMatrix();
  initCortexCanvas();
  initAgentForge();
  initHallucinationGuard();
  initMatryoshkaZoomer();
  initShadowCoW();
}

// 1. TABS SWITCHER
function initCortexTabs() {
  const tabs = document.querySelectorAll(".cortex-tabs-wrapper .cortex-tab-btn");
  const panes = document.querySelectorAll(".cortex-pane");
  if (!tabs.length || !panes.length) return;

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const target = tab.dataset.tab; // e.g. "matrix-tab"

      panes.forEach((pane) => {
        pane.classList.remove("active");
        if (pane.id === `pane-${target}`) {
          pane.classList.add("active");
        }
      });

      if (target === "canvas-tab" && window._cortexResize) {
        setTimeout(window._cortexResize, 50);
      }
    });
  });
}

// 2. 105 MATRIX RENDERER & FILTER
function initCortexMatrix() {
  const container = document.getElementById("matrix-cards-container");
  const searchInput = document.getElementById("matrix-search-input");
  const filterPills = document.querySelectorAll("#pillar-filters .filter-pill");

  if (!container) return;

  let activePillar = "all";
  let searchQuery = "";

  function renderCards() {
    container.innerHTML = "";
    const list = typeof CORTEX_CAPABILITIES !== "undefined" ? CORTEX_CAPABILITIES : [];
    const filtered = list.filter((cap) => {
      const matchPillar = activePillar === "all" || String(cap.pillarNum) === String(activePillar);
      const q = searchQuery.toLowerCase();
      const matchSearch =
        !q ||
        cap.id.toLowerCase().includes(q) ||
        cap.name.toLowerCase().includes(q) ||
        cap.description.toLowerCase().includes(q) ||
        (cap.tags && cap.tags.some((t) => t.toLowerCase().includes(q)));
      return matchPillar && matchSearch;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 4rem 1rem; color: var(--text-muted);">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔍</div>
          <div style="font-size: 1.1rem; color: #fff; font-weight: 600;">No capabilities match "${searchQuery}"</div>
          <div style="font-size: 0.88rem; margin-top: 0.25rem;">Try selecting "All (105)" or search by tags like "ast", "security", "tokens", or "dag".</div>
        </div>
      `;
      return;
    }

    filtered.forEach((cap) => {
      const card = document.createElement("div");
      card.className = "matrix-card";
      card.dataset.pillar = cap.pillarNum;

      const tierClass =
        cap.tier === "T-1" ? "badge-cyan" :
        cap.tier === "T-2" ? "badge-purple" :
        cap.tier === "T-3" ? "badge-emerald" : "badge-coral";

      const pillarColor =
        cap.pillarNum === 1 ? "#8b5cf6" :
        cap.pillarNum === 2 ? "#00f0ff" :
        cap.pillarNum === 3 ? "#10b981" :
        cap.pillarNum === 4 ? "#f59e0b" :
        cap.pillarNum === 5 ? "#ec4899" :
        cap.pillarNum === 6 ? "#a855f7" : "#f43f5e";

      card.innerHTML = `
        <div class="matrix-card-header">
          <span class="matrix-id" style="color: ${pillarColor}; font-weight: 700;">${cap.id}</span>
          <span class="matrix-tier ${tierClass}">${cap.tier}</span>
        </div>
        <h4 class="matrix-name">${cap.name}</h4>
        <p class="matrix-desc">${cap.description}</p>
        <div class="matrix-footer">
          <span class="matrix-pillar-tag" style="border-left: 2px solid ${pillarColor}; padding-left: 6px;">${cap.pillarShort}</span>
          <span class="matrix-tag">#${cap.tags ? cap.tags[0] : "cortex"}</span>
        </div>
      `;

      card.addEventListener("click", () => {
        copyTextWithToast(
          `${cap.id} [${cap.name}]: ${cap.description}`,
          `Copied capability ${cap.id} metadata!`
        );
      });

      container.appendChild(card);
    });
  }

  filterPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      filterPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      activePillar = pill.dataset.pillar;
      renderCards();
    });
  });

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value.trim();
      renderCards();
    });
  }

  renderCards();
}

// 3. 3D SYNAPTIC NEURAL CANVAS (60 FPS HTML5 Canvas)
function initCortexCanvas() {
  const canvas = document.getElementById("neural-cortex-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const inspBadge = document.getElementById("insp-badge");
  const inspTitle = document.getElementById("insp-title");
  const inspDesc = document.getElementById("insp-desc");
  const inspTags = document.getElementById("insp-tags");
  const pulseBtn = document.getElementById("btn-pulse-synapse");
  const resetBtn = document.getElementById("btn-reset-cortex-view");

  function resize() {
    const parent = canvas.parentElement;
    const w = parent ? parent.clientWidth : 1000;
    canvas.width = Math.max(w, 400);
    canvas.height = 480;
  }
  window._cortexResize = resize;
  window.addEventListener("resize", resize);
  resize();

  // Nodes graph model
  let selectedNode = null;
  let hoveredNode = null;
  let shockwave = { active: false, radius: 0, maxRadius: 600, originX: 0, originY: 0 };

  // Calculate layout coordinates
  function getNodes() {
    const w = canvas.width;
    const h = canvas.height;
    const cx = w * 0.44;
    const cy = h * 0.50;

    const list = [];

    // Central Core Substrate
    list.push({
      id: "tzero_substrate",
      type: "substrate",
      label: "T-Zero Cortex",
      icon: "🧠",
      color: "#00f0ff",
      x: cx,
      y: cy,
      radius: 30,
      badge: "NEURAL SUBSTRATE",
      title: "T-Zero AgentOS Neural Substrate",
      desc: "Central context orchestrator binding all 105 capabilities with zero-leak cryptographic security and offline AST graph indexing.",
      tags: ["kernel", "ast-engine", "zero-leak", "dag"]
    });

    // 7 Pillars outer ring
    const pCount = CORTEX_PILLAR_HUBS.length;
    const pRx = Math.min(w * 0.38, 360);
    const pRy = Math.min(h * 0.38, 175);
    CORTEX_PILLAR_HUBS.forEach((p, idx) => {
      const angle = (idx / pCount) * Math.PI * 2 - Math.PI / 2;
      list.push({
        id: p.id,
        type: "pillar",
        label: p.name,
        icon: p.icon,
        color: p.color,
        x: cx + Math.cos(angle) * pRx,
        y: cy + Math.sin(angle) * pRy,
        radius: 20,
        badge: `PILLAR ${p.num} OF 7`,
        title: `Pillar ${p.num}: ${p.name}`,
        desc: p.desc,
        tags: [`pillar-${p.num}`, "15-capabilities", "architecture"]
      });
    });

    // 12 Fleet Agents inner ring
    const aCount = CORTEX_FLEET_AGENTS.length;
    const aRx = Math.min(w * 0.22, 210);
    const aRy = Math.min(h * 0.22, 105);
    CORTEX_FLEET_AGENTS.forEach((a, idx) => {
      const angle = (idx / aCount) * Math.PI * 2 - Math.PI / 2;
      list.push({
        id: a.id,
        type: "agent",
        label: a.name.replace("Agent", ""),
        icon: a.icon,
        color: a.color,
        x: cx + Math.cos(angle) * aRx,
        y: cy + Math.sin(angle) * aRy,
        radius: 16,
        badge: `FLEET AGENT #${idx + 1}`,
        title: a.name,
        desc: `${a.role}. Scope: ${a.scope}.`,
        tags: a.tags
      });
    });

    return list;
  }

  // Synaptic packets traveling along edges
  const packets = [];
  for (let i = 0; i < 48; i++) {
    packets.push({
      edgeIndex: Math.floor(Math.random() * 26),
      progress: Math.random(),
      speed: 0.003 + Math.random() * 0.006,
      size: 2 + Math.random() * 2,
      color: ["#00f0ff", "#10b981", "#a855f7", "#ec4899", "#f59e0b"][Math.floor(Math.random() * 5)]
    });
  }

  function getEdges(nodeList) {
    const edges = [];
    const core = nodeList.find((n) => n.id === "tzero_substrate");
    const pillars = nodeList.filter((n) => n.type === "pillar");
    const agents = nodeList.filter((n) => n.type === "agent");

    if (!core) return edges;

    // Connect core to all pillars
    pillars.forEach((p) => {
      edges.push({ from: core, to: p, color: p.color, width: 1.4, alpha: 0.25 });
    });

    // Connect core to fleet agents
    agents.forEach((a) => {
      edges.push({ from: core, to: a, color: a.color, width: 1.2, alpha: 0.35 });
    });

    // Cross-connect neighboring fleet agents
    for (let i = 0; i < agents.length; i++) {
      const next = agents[(i + 1) % agents.length];
      edges.push({ from: agents[i], to: next, color: agents[i].color, width: 0.8, alpha: 0.15 });
    }

    return edges;
  }

  function renderInspector(node) {
    if (!node) return;
    if (inspBadge) inspBadge.textContent = node.badge;
    if (inspTitle) inspTitle.textContent = node.title;
    if (inspDesc) inspDesc.textContent = node.desc;
    if (inspTags) {
      inspTags.innerHTML = node.tags.map((t) => `<span class="inspector-tag">#${t}</span>`).join("");
    }
  }

  // Animation frame
  let animTime = 0;
  function animate() {
    requestAnimationFrame(animate);
    animTime += 0.016;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const nodes = getNodes();
    const edges = getEdges(nodes);

    // Draw background subtle hex grid dots
    ctx.fillStyle = "rgba(255, 255, 255, 0.02)";
    const dotSpacing = 36;
    for (let x = 18; x < canvas.width; x += dotSpacing) {
      for (let y = 18; y < canvas.height; y += dotSpacing) {
        ctx.fillRect(x, y, 1.5, 1.5);
      }
    }

    // Shockwave pulse
    if (shockwave.active) {
      shockwave.radius += 8;
      ctx.beginPath();
      ctx.arc(shockwave.originX, shockwave.originY, shockwave.radius, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(0, 240, 255, ${Math.max(0, 1 - shockwave.radius / shockwave.maxRadius)})`;
      ctx.lineWidth = 3;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(shockwave.originX, shockwave.originY, Math.max(0, shockwave.radius - 20), 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(168, 85, 247, ${Math.max(0, 0.7 - shockwave.radius / shockwave.maxRadius)})`;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      if (shockwave.radius >= shockwave.maxRadius) {
        shockwave.active = false;
        shockwave.radius = 0;
      }
    }

    // Draw Synaptic Edges
    edges.forEach((edge) => {
      ctx.beginPath();
      ctx.moveTo(edge.from.x, edge.from.y);
      ctx.lineTo(edge.to.x, edge.to.y);
      ctx.strokeStyle = edge.color;
      ctx.globalAlpha = edge.alpha;
      ctx.lineWidth = edge.width;
      ctx.stroke();
      ctx.globalAlpha = 1.0;
    });

    // Draw animated synaptic particle packets
    packets.forEach((pkt) => {
      const edge = edges[pkt.edgeIndex % edges.length];
      if (!edge) return;

      pkt.progress += pkt.speed;
      if (pkt.progress >= 1) {
        pkt.progress = 0;
        pkt.edgeIndex = Math.floor(Math.random() * edges.length);
      }

      const px = edge.from.x + (edge.to.x - edge.from.x) * pkt.progress;
      const py = edge.from.y + (edge.to.y - edge.from.y) * pkt.progress;

      ctx.beginPath();
      ctx.arc(px, py, pkt.size, 0, Math.PI * 2);
      ctx.fillStyle = pkt.color;
      ctx.shadowColor = pkt.color;
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    // Draw Nodes
    nodes.forEach((node) => {
      const isHover = hoveredNode && hoveredNode.id === node.id;
      const isSelected = selectedNode && selectedNode.id === node.id;
      const r = node.radius + (isHover || isSelected ? 4 : 0);

      // Outer glow ring
      ctx.beginPath();
      ctx.arc(node.x, node.y, r + 6, 0, Math.PI * 2);
      ctx.fillStyle = isHover || isSelected ? `${node.color}33` : "rgba(255, 255, 255, 0.03)";
      ctx.fill();

      // Node background & stroke
      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
      ctx.fillStyle = "#0a0e14";
      ctx.strokeStyle = node.color;
      ctx.lineWidth = isHover || isSelected ? 3 : 1.8;
      ctx.shadowColor = node.color;
      ctx.shadowBlur = isHover || isSelected ? 18 : 6;
      ctx.fill();
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Icon
      ctx.font = node.type === "substrate" ? "18px sans-serif" : isHover ? "14px sans-serif" : "12px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(node.icon, node.x, node.y);

      // Label below
      ctx.font = isHover || isSelected ? "bold 11px Inter, sans-serif" : "10px Inter, sans-serif";
      ctx.fillStyle = isHover || isSelected ? "#ffffff" : "rgba(255, 255, 255, 0.75)";
      ctx.fillText(node.label, node.x, node.y + r + 14);
    });
  }
  animate();

  // Mouse interaction
  function findNodeAt(mx, my) {
    const nodes = getNodes();
    for (const node of nodes) {
      const dx = mx - node.x;
      const dy = my - node.y;
      if (Math.sqrt(dx * dx + dy * dy) <= node.radius + 8) {
        return node;
      }
    }
    return null;
  }

  canvas.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    hoveredNode = findNodeAt(mx, my);
    canvas.style.cursor = hoveredNode ? "pointer" : "default";
    if (hoveredNode && !selectedNode) {
      renderInspector(hoveredNode);
    }
  });

  canvas.addEventListener("click", (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const hit = findNodeAt(mx, my);
    if (hit) {
      selectedNode = hit;
      renderInspector(hit);
      showToast(`Inspecting ${hit.title}`, hit.icon);
    } else {
      selectedNode = null;
    }
  });

  if (pulseBtn) {
    pulseBtn.addEventListener("click", () => {
      const core = getNodes().find((n) => n.id === "tzero_substrate");
      shockwave.originX = core ? core.x : canvas.width * 0.44;
      shockwave.originY = core ? core.y : canvas.height * 0.50;
      shockwave.active = true;
      shockwave.radius = 0;
      showToast("Synaptic impulse dispatched across all 105 capabilities!", "⚡");
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      selectedNode = null;
      hoveredNode = null;
      const core = getNodes().find((n) => n.id === "tzero_substrate");
      renderInspector(core);
      showToast("Cortex topology reset to default", "🔄");
    });
  }

  // Initial inspector state
  const defaultSubstrate = getNodes().find((n) => n.id === "tzero_substrate");
  renderInspector(defaultSubstrate);
}

// 4. AGENTFORGE SUBAGENT SYNTHESIZER
function initAgentForge() {
  const roleInput = document.getElementById("forge-role");
  const taskInput = document.getElementById("forge-task");
  const tierSelect = document.getElementById("forge-tier");
  const synthBtn = document.getElementById("btn-forge-synthesize");
  const copyBtn = document.getElementById("btn-copy-forge");
  const preview = document.getElementById("forge-code-preview");

  if (!synthBtn || !preview) return;

  function synthesize() {
    const role = (roleInput && roleInput.value.trim()) || "GraphQLMigrationExpert";
    const task = (taskInput && taskInput.value.trim()) || "Migrate REST endpoints to GraphQL with AST safety";
    const tier = (tierSelect && tierSelect.value) || "T-2";

    const cleanId = role.toLowerCase().replace(/[^a-z0-9]/g, "_");
    const manifest = {
      schema_version: "5.0.0",
      agent_id: `agent_${cleanId}`,
      role: role,
      isolation_tier: tier,
      token_budget: tier === "T-1" ? 4000 : tier === "T-2" ? 12000 : 32000,
      active_pillars: [1, 2, 7],
      capabilities: [
        "CAP-001 (Universal Tree-sitter + LSP CST Bridge)",
        "CAP-002 (AST Skeletonization -90% Tokens)",
        "CAP-005 (Forward Impact & Blast Radius)",
        "CAP-008 (Auto Import & Symbol Resolver)",
        "CAP-095 (Entropy Secret Scrubber Zero-Leak)"
      ],
      security: {
        zero_leak_verified: true,
        offline_ast_guarantee: true,
        egress_policy: "ZERO_TRUST_OFFLINE"
      },
      system_directive: `You are operating as ${role} under the Siber Akademi T-Zero Neural Cortex.\nYour mandate: ${task}. Maintain 100% zero-leak security and AST architectural boundaries.`
    };

    const formatted = JSON.stringify(manifest, null, 2);
    preview.textContent = formatted;
    showToast(`Synthesized subagent ${role} (${tier})!`, "⚡");
  }

  synthBtn.addEventListener("click", synthesize);

  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      copyTextWithToast(preview.textContent, "Subagent manifest copied to clipboard!");
    });
  }

  // Initial preview
  synthesize();
}

// 5. HALLUCINATION REALITY-LOCK PLAYGROUND
function initHallucinationGuard() {
  const codeInput = document.getElementById("guard-code-input");
  const runBtn = document.getElementById("btn-run-reality-lock");
  const validBtn = document.getElementById("btn-preset-valid");
  const hallBtn = document.getElementById("btn-preset-hallucinated");
  const statusBox = document.getElementById("guard-status-box");
  const statusTitle = document.getElementById("guard-status-title");
  const statusDesc = document.getElementById("guard-status-desc");

  if (!runBtn || !codeInput) return;

  const PRESET_VALID = `import math
import os

def compute_metrics(x: float) -> float:
    # Valid verified calls to Python standard library AST
    radius = math.sqrt(x)
    cwd_len = len(os.getcwd())
    return radius * math.pi + cwd_len
`;

  const PRESET_HALLUCINATED = `import math
import os

def compute_metrics(x: float):
    # DANGER: AI hallucinated fictional functions that do not exist!
    radius = math.quantum_fast_inverse_sqrt(x)
    os.teleport_process(pid=1337)
    return radius
`;

  if (validBtn) {
    validBtn.addEventListener("click", () => {
      validBtn.classList.add("active");
      if (hallBtn) hallBtn.classList.remove("active");
      codeInput.value = PRESET_VALID;
      verifyCode();
    });
  }

  if (hallBtn) {
    hallBtn.addEventListener("click", () => {
      hallBtn.classList.add("active");
      if (validBtn) validBtn.classList.remove("active");
      codeInput.value = PRESET_HALLUCINATED;
      verifyCode();
    });
  }

  function verifyCode() {
    const code = codeInput.value;
    const hallucinations = [];

    if (code.includes("quantum_fast_inverse_sqrt")) {
      hallucinations.push({
        symbol: "math.quantum_fast_inverse_sqrt",
        suggestion: "math.isqrt or math.sqrt",
        reason: "Unknown attribute in verified math module AST"
      });
    }
    if (code.includes("teleport_process")) {
      hallucinations.push({
        symbol: "os.teleport_process",
        suggestion: "os.getpid or os.kill",
        reason: "Symbol does not exist in POSIX/Windows OS AST contracts"
      });
    }

    if (hallucinations.length > 0) {
      if (statusBox) {
        statusBox.style.borderColor = "var(--accent-coral)";
        statusBox.style.background = "rgba(251, 113, 133, 0.08)";
      }
      const icon = statusBox ? statusBox.querySelector(".status-icon") : null;
      if (icon) {
        icon.textContent = "❌";
        icon.className = "status-icon coral-icon";
      }
      if (statusTitle) {
        statusTitle.textContent = `REALITY-LOCK ALERT: ${hallucinations.length} HALLUCINATIONS DETECTED`;
        statusTitle.style.color = "var(--accent-coral)";
      }
      if (statusDesc) {
        statusDesc.innerHTML = hallucinations.map((h) => 
          `• <strong>${h.symbol}</strong> rejected: ${h.reason}. <span style="color:var(--accent-cyan)">Did you mean: <code>${h.suggestion}</code>?</span>`
        ).join("<br>");
      }
      showToast("Reality-Lock caught AI hallucinated symbols!", "🛡️");
    } else {
      if (statusBox) {
        statusBox.style.borderColor = "var(--accent-emerald)";
        statusBox.style.background = "rgba(16, 185, 129, 0.08)";
      }
      const icon = statusBox ? statusBox.querySelector(".status-icon") : null;
      if (icon) {
        icon.textContent = "✅";
        icon.className = "status-icon green-icon";
      }
      if (statusTitle) {
        statusTitle.textContent = "REALITY-LOCK PASS (100% AST GROUNDED)";
        statusTitle.style.color = "var(--accent-emerald)";
      }
      if (statusDesc) {
        statusDesc.textContent = "All invoked methods and imported modules match verified AST symbol contracts with zero hallucinations.";
      }
      showToast("AST Reality-Lock verified 100% genuine symbols!", "✓");
    }
  }

  runBtn.addEventListener("click", verifyCode);
}

// 6. MATRYOSHKA CONTEXT ZOOMER (L0 - L3)
function initMatryoshkaZoomer() {
  const buttons = document.querySelectorAll(".matryoshka-card .layer-btn");
  const layerLabel = document.getElementById("mat-active-layer");
  const tokenCost = document.getElementById("mat-token-cost");
  const codeBox = document.getElementById("mat-code-display");

  if (!buttons.length || !codeBox) return;

  const MATRYOSHKA_LAYERS = {
    L0: {
      label: "L0 (File Purpose Summary)",
      tokens: "~12 tokens (-98.8% reduction)",
      color: "#00f0ff",
      code: `# [calc.py L0]: Core mathematical calculator and matrix factorization service.`
    },
    L1: {
      label: "L1 (Exported Public Symbols)",
      tokens: "~48 tokens (-95.2% reduction)",
      color: "#10b981",
      code: `# [calc.py L1]: Exported Symbols
export class MatrixFactorizer
export def fast_svd(matrix: List[List[float]]) -> Tuple[List, List, List]
export def compute_eigenvalues(m: Matrix) -> List[float]
export def solve_linear_system(a: Matrix, b: Vector) -> Vector`
    },
    L2: {
      label: "L2 (AST Typed Interface Signatures)",
      tokens: "~184 tokens (-81.6% reduction)",
      color: "#a855f7",
      code: `# [calc.py L2]: AST Typed Interface Signatures (Ultra-Pruned)
class MatrixFactorizer:
    \"\"\"High-performance matrix factorization with LAPACK bindings.\"\"\"
    def __init__(self, tolerance: float = 1e-6): ...
    def fast_svd(self, matrix: List[List[float]]) -> Tuple[List, List, List]: ...
    def compute_eigenvalues(self, m: Matrix) -> List[float]: ...
    def solve_linear_system(self, a: Matrix, b: Vector) -> Vector: ...`
    },
    L3: {
      label: "L3 (Full Raw Source Implementation)",
      tokens: "~1,024 tokens (Full Codebase Payload)",
      color: "#fb7185",
      code: `# [calc.py L3]: Full Raw Implementation
import numpy as np
from typing import List, Tuple

class MatrixFactorizer:
    \"\"\"High-performance matrix factorization with LAPACK bindings.\"\"\"
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance

    def fast_svd(self, matrix: List[List[float]]) -> Tuple[List, List, List]:
        # Implementation of Singular Value Decomposition algorithm
        arr = np.array(matrix, dtype=np.float64)
        u, s, vt = np.linalg.svd(arr, full_matrices=False)
        return (u.tolist(), s.tolist(), vt.tolist())

    def compute_eigenvalues(self, m: Matrix) -> List[float]:
        w, _ = np.linalg.eig(np.array(m))
        return w.tolist()

    def solve_linear_system(self, a: Matrix, b: Vector) -> Vector:
        return np.linalg.solve(np.array(a), np.array(b)).tolist()`
    }
  };

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const layer = btn.dataset.layer;
      const data = MATRYOSHKA_LAYERS[layer];
      if (!data) return;

      if (layerLabel) {
        layerLabel.textContent = data.label;
        layerLabel.style.color = data.color;
      }
      if (tokenCost) {
        tokenCost.textContent = data.tokens;
      }
      codeBox.textContent = data.code;
    });
  });
}

// 7. SHADOW WORKSPACE COW SIMULATOR
function initShadowCoW() {
  const rollbackBtn = document.getElementById("btn-cow-rollback");
  const commitBtn = document.getElementById("btn-cow-commit");
  const diffViewer = document.querySelector(".shadow-diff-viewer .diff-content code");

  if (!rollbackBtn || !diffViewer) return;

  rollbackBtn.addEventListener("click", () => {
    diffViewer.textContent = `// Virtual OverlayFS memory checkpoint restored.
// 0 bytes were touched on disk. All 3 in-memory shadow nodes discarded in 0.28ms.`;
    showToast("Virtual CoW OverlayFS rolled back cleanly!", "⏪");
  });

  if (commitBtn) {
    commitBtn.addEventListener("click", () => {
      diffViewer.textContent = `// ACID TRANSACTION COMMITTED TO DISK:
// [1/3] services/auth.py -> sha256: 4a2b... [VERIFIED]
// [2/3] models/user.py   -> sha256: 9e1f... [VERIFIED]
// [3/3] api/router.py    -> sha256: 7c3d... [VERIFIED]
// Pre-flight static verification: 105 tests green, 0 lint errors, 0 secret leaks.`;
      showToast("ACID Transaction committed to workspace with zero regressions!", "💾");
    });
  }
}
