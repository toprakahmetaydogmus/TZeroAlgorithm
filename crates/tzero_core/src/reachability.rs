// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! Multi-Module AST Call-Graph Reachability & Dead Code Pruner in Rust.
//! Traverses symbol call-trees from root entrypoints using BFS/DFS, discovering reachable
//! call paths and pruning unused, orphan functions to produce zero-waste LLM contexts.

use std::collections::{HashMap, HashSet, VecDeque};
use serde::{Deserialize, Serialize};
use crate::symbol_graph::SymbolRecord;

/// Reachability analysis summary report.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReachabilityReport {
    pub total_symbols: usize,
    pub reachable_count: usize,
    pub dead_symbol_count: usize,
    pub dead_code_ratio: f64,
    pub reachable_symbols: Vec<String>,
    pub dead_symbols: Vec<String>,
}

/// Identifies reachable and dead symbols starting from specified entrypoints.
pub fn analyze_reachability(
    symbols: &[SymbolRecord],
    invocations: &[(String, String)], // (caller_symbol_name, callee_symbol_name)
    entrypoints: &[String],
) -> ReachabilityReport {
    let mut call_graph: HashMap<String, Vec<String>> = HashMap::new();
    let mut all_symbol_names: HashSet<String> = HashSet::new();

    for sym in symbols {
        all_symbol_names.insert(sym.name.clone());
    }

    for (caller, callee) in invocations {
        call_graph
            .entry(caller.clone())
            .or_default()
            .push(callee.clone());
    }

    // Determine seed roots: provided entrypoints or symbols matching main/run/cli
    let mut queue = VecDeque::new();
    let mut visited: HashSet<String> = HashSet::new();

    for ep in entrypoints {
        if all_symbol_names.contains(ep) && visited.insert(ep.clone()) {
            queue.push_back(ep.clone());
        }
    }

    // Fallback: if no entrypoints passed, use common entrypoint names
    if queue.is_empty() {
        for name in &all_symbol_names {
            let lower = name.to_lowercase();
            if lower == "main" || lower.starts_with("run") || lower.starts_with("cli") || lower.starts_with("test") {
                if visited.insert(name.clone()) {
                    queue.push_back(name.clone());
                }
            }
        }
    }

    // BFS Traversal
    while let Some(current) = queue.pop_front() {
        if let Some(callees) = call_graph.get(&current) {
            for callee in callees {
                if all_symbol_names.contains(callee) && visited.insert(callee.clone()) {
                    queue.push_back(callee.clone());
                }
            }
        }
    }

    let mut reachable: Vec<String> = visited.into_iter().collect();
    reachable.sort();

    let mut dead: Vec<String> = all_symbol_names
        .difference(&reachable.iter().cloned().collect())
        .cloned()
        .collect();
    dead.sort();

    let total = symbols.len();
    let dead_count = dead.len();
    let ratio = if total > 0 {
        ((dead_count as f64 / total as f64) * 1000.0).round() / 10.0
    } else {
        0.0
    };

    ReachabilityReport {
        total_symbols: total,
        reachable_count: reachable.len(),
        dead_symbol_count: dead_count,
        dead_code_ratio: ratio,
        reachable_symbols: reachable,
        dead_symbols: dead,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_reachability_pruning() {
        let symbols = vec![
            SymbolRecord {
                name: "main".to_string(),
                kind: "function".to_string(),
                line: 1,
                path: "app.py".to_string(),
                signature: "def main():".to_string(),
            },
            SymbolRecord {
                name: "helper".to_string(),
                kind: "function".to_string(),
                line: 5,
                path: "app.py".to_string(),
                signature: "def helper():".to_string(),
            },
            SymbolRecord {
                name: "orphan_feature".to_string(),
                kind: "function".to_string(),
                line: 10,
                path: "app.py".to_string(),
                signature: "def orphan_feature():".to_string(),
            },
        ];

        let invocations = vec![("main".to_string(), "helper".to_string())];
        let entrypoints = vec!["main".to_string()];

        let rep = analyze_reachability(&symbols, &invocations, &entrypoints);
        assert_eq!(rep.reachable_count, 2);
        assert_eq!(rep.dead_symbol_count, 1);
        assert!(rep.dead_symbols.contains(&"orphan_feature".to_string()));
    }
}
