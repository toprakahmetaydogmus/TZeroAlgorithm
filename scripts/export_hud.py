# -*- coding: utf-8 -*-
"""
Helper script to export the T-Zero Cyberpunk Graph HUD to HTML.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

from tzero_jarvis.graph_visualizer import CyberpunkGraphVisualizer
from tzero_jarvis.causal_graph import CausalTemporalGraph
from tzero_jarvis.semantic_compressor import get_global_compressor

def export_hud(output_path="tzero_graph_hud.html"):
    c = get_global_compressor()
    g = CausalTemporalGraph(c.codebook)
    for cid, entry in c.codebook.codes.items():
        g.add_node(
            f"node_{cid}",
            f"Code #{cid}: {entry.get('graph', '')}",
            entry.get("primary_domain", "GENERIC"),
            cid
        )

    viz = CyberpunkGraphVisualizer(g)
    saved = viz.export_to_file(output_path)
    print(f"Cizge HTML uretildi: {saved}")
    return saved

if __name__ == "__main__":
    export_hud()
