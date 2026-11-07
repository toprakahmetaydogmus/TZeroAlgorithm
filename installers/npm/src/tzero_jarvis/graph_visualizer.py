# -*- coding: utf-8 -*-
"""
T-ZERO CYBERPUNK KNOWLEDGE & CAUSAL GRAPH VISUALIZER
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 4.4.0

Bu modül, T-Zero 4D Nedensellik ve Bilgi Çizgesini tamamen bağımsız (Offline),
neon siberpunk estetiğine sahip interaktif bir HTML5 / SVG Force-Directed Graph
olarak render eder ve dışa aktarır.
"""

from __future__ import annotations
import os
import json
from typing import Dict, List, Optional, Any
from tzero_jarvis.causal_graph import CausalTemporalGraph


DOMAIN_COLORS = {
    "HARDWARE": "#38bdf8",
    "PROTOCOL": "#818cf8",
    "SOFTWARE": "#60a5fa",
    "VULN": "#f43f5e",
    "BIO": "#34d399",
    "CRYPTO": "#fbbf24",
    "QUANTUM": "#a78bfa",
    "AEROSPACE": "#fb923c",
    "AUTOMOTIVE": "#38bdf8",
    "FINANCE": "#4ade80",
    "ROBOTICS": "#f87171",
    "GENERIC": "#94a3b8"
}


class CyberpunkGraphVisualizer:
    """
    Siberpunk Temalı Çizge Görselleştirici.
    Hiçbir CDN veya internet bağlantısına ihtiyaç duymadan saf HTML5/SVG/Canvas üretir.
    """

    def __init__(self, causal_graph: Optional[CausalTemporalGraph] = None):
        self.causal_graph = causal_graph or CausalTemporalGraph()

    def generate_html(self, title: str = "T-ZERO JARVIS KNOWLEDGE & CAUSAL GRAPH") -> str:
        graph_data = self.causal_graph.to_graph_data()
        json_payload = json.dumps(graph_data, ensure_ascii=False)
        colors_payload = json.dumps(DOMAIN_COLORS, ensure_ascii=False)

        html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #090d16;
            color: #f8fafc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            overflow: hidden;
            height: 100vh;
            width: 100vw;
        }}
        #header {{
            position: absolute;
            top: 15px;
            left: 20px;
            z-index: 100;
            background: rgba(15, 23, 42, 0.88);
            backdrop-filter: blur(8px);
            padding: 12px 20px;
            border: 1px solid #1e293b;
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
            pointer-events: auto;
        }}
        #header h1 {{ font-size: 15px; font-weight: 600; letter-spacing: 0.5px; color: #f8fafc; }}
        #header p {{ font-size: 12px; color: #94a3b8; margin-top: 4px; }}
        #controls {{
            position: absolute;
            top: 15px;
            right: 20px;
            z-index: 100;
            background: rgba(15, 23, 42, 0.88);
            backdrop-filter: blur(8px);
            padding: 10px 15px;
            border: 1px solid #1e293b;
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        }}
        input[type="text"] {{
            background: #0b1120;
            border: 1px solid #334155;
            color: #f8fafc;
            padding: 7px 12px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 12px;
            outline: none;
            transition: border-color 0.15s ease;
        }}
        input[type="text"]:focus {{
            border-color: #38bdf8;
        }}
        #stats-bar {{
            position: absolute;
            bottom: 15px;
            left: 20px;
            z-index: 100;
            background: rgba(15, 23, 42, 0.88);
            backdrop-filter: blur(8px);
            padding: 8px 16px;
            border: 1px solid #1e293b;
            font-size: 12px;
            color: #94a3b8;
            border-radius: 6px;
        }}
        #inspector {{
            position: absolute;
            bottom: 15px;
            right: 20px;
            z-index: 100;
            width: 320px;
            max-height: 250px;
            overflow-y: auto;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid #334155;
            padding: 14px;
            font-size: 12px;
            border-radius: 8px;
            display: none;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
        }}
        canvas {{ display: block; width: 100%; height: 100%; }}
    </style>
</head>
<body>
    <div id="header">
        <h1>⚡ T-ZERO 4D KNOWLEDGE & CAUSAL GRAPH</h1>
        <p>Developer: Toprak Ahmet Aydoğmuş | Zero-Cost Neural Engine</p>
    </div>

    <div id="controls">
        <input type="text" id="searchInput" placeholder="Düğüm / Kod ara (örn: ESP32, #8421)..." oninput="filterGraph()">
    </div>

    <div id="stats-bar">
        Düğümler: <span id="nodeCount" style="color:#38bdf8">0</span> | 
        Bağlar: <span id="edgeCount" style="color:#818cf8">0</span> | 
        FPS: <span id="fpsCount" style="color:#fbbf24">60</span>
    </div>

    <div id="inspector">
        <h3 id="insTitle" style="color:#38bdf8; margin-bottom:6px;">Detay</h3>
        <p id="insBody" style="color:#cbd5e1; line-height:1.5;"></p>
    </div>

    <canvas id="graphCanvas"></canvas>

    <script>
        const graphData = {json_payload};
        const domainColors = {colors_payload};

        const canvas = document.getElementById('graphCanvas');
        const ctx = canvas.getContext('2d');
        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight;

        window.addEventListener('resize', () => {{
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        }});

        document.getElementById('nodeCount').innerText = graphData.nodes.length;
        document.getElementById('edgeCount').innerText = graphData.links.length;

        // Düğümleri rastgele pozisyonlara yerleştir
        const nodes = graphData.nodes.map((n, i) => {{
            const angle = (i / Math.max(1, graphData.nodes.length)) * 2 * Math.PI;
            const radius = 150 + Math.random() * 200;
            return {{
                ...n,
                x: width / 2 + Math.cos(angle) * radius,
                y: height / 2 + Math.sin(angle) * radius,
                vx: 0,
                vy: 0,
                radius: n.code ? 18 : 12,
                color: domainColors[n.group] || '#00ffcc'
            }};
        }});

        const nodeMap = new Map();
        nodes.forEach(n => nodeMap.set(n.id, n));

        const links = graphData.links.map(l => ({{
            ...l,
            sourceNode: nodeMap.get(l.source),
            targetNode: nodeMap.get(l.target)
        }})).filter(l => l.sourceNode && l.targetNode);

        // Basit Force-Directed Fizik Simülasyonu
        let zoom = 1.0;
        let panX = 0, panY = 0;
        let selectedNode = null;
        let isDragging = false;
        let dragNode = null;

        function simulate() {{
            // İtme kuvveti
            for (let i = 0; i < nodes.length; i++) {{
                for (let j = i + 1; j < nodes.length; j++) {{
                    const dx = nodes[j].x - nodes[i].x;
                    const dy = nodes[j].y - nodes[i].y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                    if (dist < 300) {{
                        const force = (300 - dist) / (dist * 15);
                        nodes[i].vx -= dx * force;
                        nodes[i].vy -= dy * force;
                        nodes[j].vx += dx * force;
                        nodes[j].vy += dy * force;
                    }}
                }}
            }}

            // Bağ çekme kuvveti
            links.forEach(l => {{
                const dx = l.targetNode.x - l.sourceNode.x;
                const dy = l.targetNode.y - l.sourceNode.y;
                const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                const force = (dist - 120) * 0.02;
                l.sourceNode.vx += dx * force;
                l.sourceNode.vy += dy * force;
                l.targetNode.vx -= dx * force;
                l.targetNode.vy -= dy * force;
            }});

            // Merkeze çekim ve sürtünme
            nodes.forEach(n => {{
                if (n === dragNode) return;
                n.vx += (width / 2 - n.x) * 0.002;
                n.vy += (height / 2 - n.y) * 0.002;
                n.vx *= 0.85;
                n.vy *= 0.85;
                n.x += n.vx;
                n.y += n.vy;
            }});
        }}

        let lastFrameTime = performance.now();
        let frameCount = 0;

        function render() {{
            simulate();

            ctx.clearRect(0, 0, width, height);
            ctx.save();
            ctx.translate(panX, panY);
            ctx.scale(zoom, zoom);

            // Bağları çiz
            links.forEach(l => {{
                ctx.beginPath();
                ctx.moveTo(l.sourceNode.x, l.sourceNode.y);
                ctx.lineTo(l.targetNode.x, l.targetNode.y);
                ctx.strokeStyle = l.relation === 'causes' ? 'rgba(255, 0, 85, 0.6)' : 'rgba(0, 229, 255, 0.4)';
                ctx.lineWidth = l.relation === 'causes' ? 2 : 1;
                ctx.stroke();

                // İlişki etiketi
                const midX = (l.sourceNode.x + l.targetNode.x) / 2;
                const midY = (l.sourceNode.y + l.targetNode.y) / 2;
                ctx.font = '9px monospace';
                ctx.fillStyle = '#80d8ff';
                ctx.fillText(l.relation, midX, midY);
            }});

            // Düğümleri çiz
            nodes.forEach(n => {{
                ctx.save();
                ctx.shadowColor = n.color;
                ctx.shadowBlur = 12;

                ctx.beginPath();
                ctx.arc(n.x, n.y, n.radius, 0, 2 * Math.PI);
                ctx.fillStyle = n.color;
                ctx.fill();

                ctx.restore();

                // Düğüm halkası
                ctx.beginPath();
                ctx.arc(n.x, n.y, n.radius + 3, 0, 2 * Math.PI);
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 1;
                ctx.stroke();

                // Metin etiketi
                ctx.font = '10px Consolas, monospace';
                ctx.fillStyle = '#ffffff';
                ctx.textAlign = 'center';
                const labelText = n.code ? `[#${{n.code}}] ${{n.label}}` : n.label;
                ctx.fillText(labelText, n.x, n.y + n.radius + 14);
            }});

            ctx.restore();

            // FPS sayacı
            frameCount++;
            const now = performance.now();
            if (now - lastFrameTime >= 1000) {{
                document.getElementById('fpsCount').innerText = frameCount;
                frameCount = 0;
                lastFrameTime = now;
            }}

            requestAnimationFrame(render);
        }}

        // Mouse Etkileşimi
        canvas.addEventListener('mousedown', e => {{
            const mx = (e.clientX - panX) / zoom;
            const my = (e.clientY - panY) / zoom;
            for (let n of nodes) {{
                const dx = n.x - mx;
                const dy = n.y - my;
                if (Math.sqrt(dx * dx + dy * dy) < n.radius + 5) {{
                    dragNode = n;
                    selectedNode = n;
                    showInspector(n);
                    return;
                }}
            }}
            isDragging = true;
            dragStartX = e.clientX - panX;
            dragStartY = e.clientY - panY;
        }});

        canvas.addEventListener('mousemove', e => {{
            if (dragNode) {{
                dragNode.x = (e.clientX - panX) / zoom;
                dragNode.y = (e.clientY - panY) / zoom;
            }} else if (isDragging) {{
                panX = e.clientX - dragStartX;
                panY = e.clientY - dragStartY;
            }}
        }});

        canvas.addEventListener('mouseup', () => {{
            dragNode = null;
            isDragging = false;
        }});

        canvas.addEventListener('wheel', e => {{
            e.preventDefault();
            const factor = e.deltaY < 0 ? 1.1 : 0.9;
            zoom *= factor;
            zoom = Math.min(Math.max(0.2, zoom), 4.0);
        }});

        function showInspector(node) {{
            const ins = document.getElementById('inspector');
            ins.style.display = 'block';
            document.getElementById('insTitle').innerText = `${{node.group}}: ${{node.label}}`;
            document.getElementById('insBody').innerHTML = `
                <b>ID:</b> ${{node.id}}<br>
                <b>Latent Code:</b> ${{node.code ? '#' + node.code : 'None'}}<br>
                <b>Domain:</b> ${{node.group}}<br>
                <b>Timestamp:</b> ${{new Date(node.timestamp * 1000).toLocaleTimeString()}}
            `;
        }}

        function filterGraph() {{
            const query = document.getElementById('searchInput').value.toLowerCase();
            nodes.forEach(n => {{
                const match = n.label.toLowerCase().includes(query) || (n.code && n.code.toString().includes(query));
                n.color = match ? (domainColors[n.group] || '#00ffcc') : '#334155';
                n.radius = match ? (n.code ? 20 : 14) : 8;
            }});
        }}

        requestAnimationFrame(render);
    </script>
</body>
</html>
"""
        return html

    def export_to_file(self, target_path: str, title: str = "T-ZERO JARVIS KNOWLEDGE & CAUSAL GRAPH") -> str:
        html = self.generate_html(title)
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(html)
        return target_path
