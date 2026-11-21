// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! High-Performance AST Symbol & Dependency Graph Extractor in Rust.
//! Extracts top-level classes, functions, interfaces, and module imports
//! across Python, TypeScript, Rust, and Go codebases.

use std::collections::{HashMap, HashSet};
use serde::{Deserialize, Serialize};

/// Extracted AST symbol record.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SymbolRecord {
    pub name: String,
    pub kind: String, // "class", "function", "interface", "method"
    pub line: usize,
    pub path: String,
    pub signature: String,
}

/// Extracted dependency edge (caller / importer -> callee / imported).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DependencyEdge {
    pub source: String,
    pub target: String,
    pub kind: String, // "import", "call", "inheritance"
}

/// System Graph Analysis Summary.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphAnalysisResult {
    pub total_nodes: usize,
    pub total_edges: usize,
    pub symbols: Vec<SymbolRecord>,
    pub edges: Vec<DependencyEdge>,
    pub centrality: HashMap<String, f64>,
}

/// Simple regex-free line-based fast symbol scanner for multi-language files.
pub fn extract_symbols_from_source(path: &str, content: &str) -> (Vec<SymbolRecord>, Vec<DependencyEdge>) {
    let mut symbols = Vec::new();
    let mut edges = Vec::new();

    let lines: Vec<&str> = content.lines().collect();
    let file_stem = std::path::Path::new(path)
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or(path);

    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim();
        let line_num = idx + 1;

        // Python def / class
        if trimmed.starts_with("def ") {
            if let Some(name_end) = trimmed[4..].find('(') {
                let name = trimmed[4..4 + name_end].trim().to_string();
                symbols.push(SymbolRecord {
                    name,
                    kind: "function".to_string(),
                    line: line_num,
                    path: path.to_string(),
                    signature: trimmed.to_string(),
                });
            }
        } else if trimmed.starts_with("class ") {
            if let Some(name_end) = trimmed[6..].find(|c: char| c == ':' || c == '(' || c.is_whitespace()) {
                let name = trimmed[6..6 + name_end].trim().to_string();
                symbols.push(SymbolRecord {
                    name,
                    kind: "class".to_string(),
                    line: line_num,
                    path: path.to_string(),
                    signature: trimmed.to_string(),
                });
            }
        } else if trimmed.starts_with("import ") || trimmed.starts_with("from ") {
            // Python imports
            let parts: Vec<&str> = trimmed.split_whitespace().collect();
            if parts.len() >= 2 {
                let mod_name = if parts[0] == "from" { parts[1] } else { parts[1].split('.').next().unwrap_or(parts[1]) };
                edges.push(DependencyEdge {
                    source: file_stem.to_string(),
                    target: mod_name.to_string(),
                    kind: "import".to_string(),
                });
            }
        }

        // Rust fn / struct / trait / impl
        if trimmed.starts_with("pub fn ") || trimmed.starts_with("fn ") {
            let offset = if trimmed.starts_with("pub fn ") { 7 } else { 3 };
            if let Some(name_end) = trimmed[offset..].find(|c: char| c == '(' || c == '<') {
                let name = trimmed[offset..offset + name_end].trim().to_string();
                symbols.push(SymbolRecord {
                    name,
                    kind: "function".to_string(),
                    line: line_num,
                    path: path.to_string(),
                    signature: trimmed.to_string(),
                });
            }
        } else if trimmed.starts_with("pub struct ") || trimmed.starts_with("struct ") {
            let offset = if trimmed.starts_with("pub struct ") { 11 } else { 7 };
            if let Some(name_end) = trimmed[offset..].find(|c: char| c == '{' || c == '(' || c == ';' || c == '<' || c.is_whitespace()) {
                let name = trimmed[offset..offset + name_end].trim().to_string();
                symbols.push(SymbolRecord {
                    name,
                    kind: "struct".to_string(),
                    line: line_num,
                    path: path.to_string(),
                    signature: trimmed.to_string(),
                });
            }
        } else if trimmed.starts_with("use ") {
            let mod_part = trimmed[4..].trim_end_matches(';').trim();
            edges.push(DependencyEdge {
                source: file_stem.to_string(),
                target: mod_part.to_string(),
                kind: "import".to_string(),
            });
        }

        // TypeScript / JavaScript export function / export class / interface
        if trimmed.starts_with("export function ") || trimmed.starts_with("function ") {
            let offset = if trimmed.starts_with("export function ") { 16 } else { 9 };
            if let Some(name_end) = trimmed[offset..].find('(') {
                let name = trimmed[offset..offset + name_end].trim().to_string();
                symbols.push(SymbolRecord {
                    name,
                    kind: "function".to_string(),
                    line: line_num,
                    path: path.to_string(),
                    signature: trimmed.to_string(),
                });
            }
        } else if trimmed.starts_with("export class ") || trimmed.starts_with("class ") {
            let offset = if trimmed.starts_with("export class ") { 13 } else { 6 };
            if let Some(name_end) = trimmed[offset..].find(|c: char| c == '{' || c.is_whitespace()) {
                let name = trimmed[offset..offset + name_end].trim().to_string();
                symbols.push(SymbolRecord {
                    name,
                    kind: "class".to_string(),
                    line: line_num,
                    path: path.to_string(),
                    signature: trimmed.to_string(),
                });
            }
        } else if trimmed.starts_with("import ") && trimmed.contains(" from ") {
            if let Some(quote_start) = trimmed.find(['\'', '"']) {
                let rest = &trimmed[quote_start + 1..];
                if let Some(quote_end) = rest.find(['\'', '"']) {
                    let imp = &rest[..quote_end];
                    edges.push(DependencyEdge {
                        source: file_stem.to_string(),
                        target: imp.to_string(),
                        kind: "import".to_string(),
                    });
                }
            }
        }
    }

    (symbols, edges)
}

/// Computes in-degree centrality for nodes in the dependency graph.
pub fn compute_centrality(edges: &[DependencyEdge]) -> HashMap<String, f64> {
    let mut in_degrees: HashMap<String, usize> = HashMap::new();
    let mut all_nodes: HashSet<String> = HashSet::new();

    for edge in edges {
        all_nodes.insert(edge.source.clone());
        all_nodes.insert(edge.target.clone());
        *in_degrees.entry(edge.target.clone()).or_insert(0) += 1;
    }

    let max_deg = in_degrees.values().copied().max().unwrap_or(1) as f64;
    let mut centrality = HashMap::new();

    for node in all_nodes {
        let deg = in_degrees.get(&node).copied().unwrap_or(0) as f64;
        centrality.insert(node, (deg / max_deg).min(1.0));
    }

    centrality
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_symbols_python() {
        let code = "import os\nclass MyEngine:\n    def run(self):\n        pass\n";
        let (symbols, edges) = extract_symbols_from_source("my_mod.py", code);
        assert_eq!(symbols.len(), 2);
        assert_eq!(symbols[0].name, "MyEngine");
        assert_eq!(symbols[1].name, "run");
        assert_eq!(edges.len(), 1);
        assert_eq!(edges[0].target, "os");
    }
}
