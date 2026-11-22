// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! High-Performance Graph PageRank & Architectural Backbone Analyzer in Rust.
//! Implements power-iteration PageRank ($d=0.85, \epsilon=10^{-6}$) over extracted
//! dependency and call edges to discover module centrality and architectural cores.

use std::collections::{HashMap, HashSet};
use serde::{Deserialize, Serialize};
use crate::symbol_graph::DependencyEdge;

/// Ranked centrality score for an architectural node.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PageRankResult {
    pub node: String,
    pub score: f64,
    pub rank: usize,
    pub in_degree: usize,
    pub out_degree: usize,
}

/// Power-iteration PageRank algorithm:
/// PR(u) = (1 - d) / N + d * sum_{v in In(u)} (PR(v) / Out(v))
/// Handles dangling nodes (teleportation) and guarantees convergence.
pub fn compute_pagerank(
    edges: &[DependencyEdge],
    damping: Option<f64>,
    max_iter: Option<usize>,
    tolerance: Option<f64>,
) -> Vec<PageRankResult> {
    let d = damping.unwrap_or(0.85);
    let max_iterations = max_iter.unwrap_or(100);
    let tol = tolerance.unwrap_or(1e-6);

    let mut all_nodes: HashSet<String> = HashSet::new();
    let mut in_neighbors: HashMap<String, Vec<String>> = HashMap::new();
    let mut out_degrees: HashMap<String, usize> = HashMap::new();
    let mut in_degrees: HashMap<String, usize> = HashMap::new();

    for edge in edges {
        all_nodes.insert(edge.source.clone());
        all_nodes.insert(edge.target.clone());

        in_neighbors
            .entry(edge.target.clone())
            .or_default()
            .push(edge.source.clone());

        *out_degrees.entry(edge.source.clone()).or_insert(0) += 1;
        *in_degrees.entry(edge.target.clone()).or_insert(0) += 1;
    }

    let n = all_nodes.len();
    if n == 0 {
        return Vec::new();
    }

    let n_f64 = n as f64;
    let initial_score = 1.0 / n_f64;
    let mut current_pr: HashMap<String, f64> = all_nodes.iter().map(|node| (node.clone(), initial_score)).collect();
    let mut next_pr: HashMap<String, f64> = HashMap::with_capacity(n);

    for _ in 0..max_iterations {
        let mut dangling_sum = 0.0f64;
        for (node, &pr) in &current_pr {
            if out_degrees.get(node).copied().unwrap_or(0) == 0 {
                dangling_sum += pr;
            }
        }

        let base_teleport = (1.0 - d) / n_f64 + d * (dangling_sum / n_f64);
        let mut diff = 0.0f64;

        for node in &all_nodes {
            let mut sum_in = 0.0f64;
            if let Some(incoming) = in_neighbors.get(node) {
                for in_node in incoming {
                    let out_deg = out_degrees.get(in_node).copied().unwrap_or(1).max(1) as f64;
                    let in_pr = current_pr.get(in_node).copied().unwrap_or(0.0);
                    sum_in += in_pr / out_deg;
                }
            }

            let new_val = base_teleport + d * sum_in;
            let old_val = current_pr.get(node).copied().unwrap_or(0.0);
            diff += (new_val - old_val).abs();
            next_pr.insert(node.clone(), new_val);
        }

        std::mem::swap(&mut current_pr, &mut next_pr);

        if diff < tol {
            break;
        }
    }

    let mut results: Vec<PageRankResult> = current_pr
        .into_iter()
        .map(|(node, score)| {
            let in_deg = in_degrees.get(&node).copied().unwrap_or(0);
            let out_deg = out_degrees.get(&node).copied().unwrap_or(0);
            PageRankResult {
                node,
                score: (score * 10000.0).round() / 10000.0,
                rank: 0,
                in_degree: in_deg,
                out_degree: out_deg,
            }
        })
        .collect();

    results.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));

    for (idx, item) in results.iter_mut().enumerate() {
        item.rank = idx + 1;
    }

    results
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pagerank_basic() {
        let edges = vec![
            DependencyEdge {
                source: "app".to_string(),
                target: "core".to_string(),
                kind: "import".to_string(),
            },
            DependencyEdge {
                source: "cli".to_string(),
                target: "core".to_string(),
                kind: "import".to_string(),
            },
            DependencyEdge {
                source: "core".to_string(),
                target: "utils".to_string(),
                kind: "import".to_string(),
            },
        ];

        let results = compute_pagerank(&edges, None, None, None);
        assert!(!results.is_empty());
        // Core should rank higher than app/cli due to multiple inbound dependencies
        let core_res = results.iter().find(|r| r.node == "core").unwrap();
        let app_res = results.iter().find(|r| r.node == "app").unwrap();
        assert!(core_res.score > app_res.score);
    }
}
