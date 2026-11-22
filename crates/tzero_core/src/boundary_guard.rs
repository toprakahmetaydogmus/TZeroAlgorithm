// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! T-Zero Architectural Boundary Guard & Rules Enforcer.
//! Enforces strict inward-only layered architecture, detects circular dependencies,
//! and guards against banned imports and architectural erosion.

use std::collections::{HashMap, HashSet};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ArchLayer {
    Presentation = 1,
    Business = 2,
    Persistence = 3,
    Utils = 4,
    Unknown = 5,
}

impl ArchLayer {
    #[allow(clippy::should_implement_trait)]
    pub fn from_str(s: &str) -> Self {
        let lower = s.to_lowercase();
        if lower.contains("cli") || lower.contains("api") || lower.contains("ui") || lower.contains("mcp") || lower.contains("present") {
            ArchLayer::Presentation
        } else if lower.contains("service") || lower.contains("orchestr") || lower.contains("business") || lower.contains("core") {
            ArchLayer::Business
        } else if lower.contains("model") || lower.contains("persist") || lower.contains("ast") || lower.contains("db") {
            ArchLayer::Persistence
        } else if lower.contains("util") || lower.contains("shared") || lower.contains("help") || lower.contains("codebook") {
            ArchLayer::Utils
        } else {
            ArchLayer::Unknown
        }
    }

    /// Allowed inward dependencies: Presentation -> Business -> Persistence / Utils.
    pub fn can_depend_on(&self, target: ArchLayer) -> bool {
        match self {
            ArchLayer::Presentation => true, // Can depend on anything
            ArchLayer::Business => target != ArchLayer::Presentation,
            ArchLayer::Persistence => target == ArchLayer::Persistence || target == ArchLayer::Utils,
            ArchLayer::Utils => target == ArchLayer::Utils,
            ArchLayer::Unknown => true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoundaryViolation {
    pub source_module: String,
    pub source_layer: String,
    pub target_module: String,
    pub target_layer: String,
    pub violation_type: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CircularDependency {
    pub cycle: Vec<String>,
    pub length: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoundaryReport {
    pub total_modules_checked: usize,
    pub total_edges_checked: usize,
    pub is_compliant: bool,
    pub violations: Vec<BoundaryViolation>,
    pub circular_dependencies: Vec<CircularDependency>,
    pub banned_import_findings: Vec<String>,
}

/// Enforces architectural boundary rules across an edge list (source -> target).
pub fn enforce_boundaries(
    edges: &[(&str, &str)],
    banned_imports: Option<&[&str]>,
) -> BoundaryReport {
    let mut violations = Vec::new();
    let mut circular_deps = Vec::new();
    let mut banned_findings = Vec::new();

    let banned: HashSet<&str> = banned_imports.unwrap_or(&["eval", "exec", "pickle"]).iter().copied().collect();

    let mut graph: HashMap<String, Vec<String>> = HashMap::new();
    let mut all_modules: HashSet<String> = HashSet::new();

    for &(src, dst) in edges {
        all_modules.insert(src.to_string());
        all_modules.insert(dst.to_string());
        graph.entry(src.to_string()).or_default().push(dst.to_string());

        // Check banned
        for &b in &banned {
            if dst.contains(b) {
                banned_findings.push(format!("Module '{}' imports banned symbol '{}'", src, dst));
            }
        }

        // Layer checking
        let src_layer = ArchLayer::from_str(src);
        let dst_layer = ArchLayer::from_str(dst);

        if src_layer != ArchLayer::Unknown && dst_layer != ArchLayer::Unknown && !src_layer.can_depend_on(dst_layer) {
            violations.push(BoundaryViolation {
                source_module: src.to_string(),
                source_layer: format!("{:?}", src_layer),
                target_module: dst.to_string(),
                target_layer: format!("{:?}", dst_layer),
                violation_type: "LayerBreach".to_string(),
                description: format!(
                    "Inward-only violation: {:?} module '{}' cannot depend on outer {:?} module '{}'",
                    src_layer, src, dst_layer, dst
                ),
            });
        }
    }

    // Circular dependency detection using DFS
    let mut visited: HashSet<String> = HashSet::new();
    let mut rec_stack: HashSet<String> = HashSet::new();
    let mut current_path: Vec<String> = Vec::new();

    fn dfs_cycle(
        node: &str,
        graph: &HashMap<String, Vec<String>>,
        visited: &mut HashSet<String>,
        rec_stack: &mut HashSet<String>,
        path: &mut Vec<String>,
        cycles: &mut Vec<CircularDependency>,
    ) {
        visited.insert(node.to_string());
        rec_stack.insert(node.to_string());
        path.push(node.to_string());

        if let Some(neighbors) = graph.get(node) {
            for neighbor in neighbors {
                if !visited.contains(neighbor) {
                    dfs_cycle(neighbor, graph, visited, rec_stack, path, cycles);
                } else if rec_stack.contains(neighbor) {
                    // Cycle detected
                    let idx = path.iter().position(|x| x == neighbor).unwrap_or(0);
                    let mut cycle_slice = path[idx..].to_vec();
                    cycle_slice.push(neighbor.to_string());
                    cycles.push(CircularDependency {
                        length: cycle_slice.len() - 1,
                        cycle: cycle_slice,
                    });
                }
            }
        }

        path.pop();
        rec_stack.remove(node);
    }

    for module in &all_modules {
        if !visited.contains(module) {
            dfs_cycle(module, &graph, &mut visited, &mut rec_stack, &mut current_path, &mut circular_deps);
        }
    }

    let is_compliant = violations.is_empty() && circular_deps.is_empty() && banned_findings.is_empty();

    BoundaryReport {
        total_modules_checked: all_modules.len(),
        total_edges_checked: edges.len(),
        is_compliant,
        violations,
        circular_dependencies: circular_deps,
        banned_import_findings: banned_findings,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_inward_dependencies() {
        let edges = [
            ("tzero_cli", "tzero_service"),
            ("tzero_service", "tzero_model"),
            ("tzero_model", "tzero_utils"),
        ];
        let rep = enforce_boundaries(&edges, None);
        assert!(rep.is_compliant);
        assert_eq!(rep.violations.len(), 0);
    }

    #[test]
    fn test_layer_breach_detection() {
        let edges = [
            ("tzero_model", "tzero_cli"), // Persistence depending on Presentation!
        ];
        let rep = enforce_boundaries(&edges, None);
        assert!(!rep.is_compliant);
        assert_eq!(rep.violations.len(), 1);
        assert_eq!(rep.violations[0].violation_type, "LayerBreach");
    }

    #[test]
    fn test_circular_dependency_detection() {
        let edges = [
            ("mod_a", "mod_b"),
            ("mod_b", "mod_c"),
            ("mod_c", "mod_a"),
        ];
        let rep = enforce_boundaries(&edges, None);
        assert!(!rep.is_compliant);
        assert_eq!(rep.circular_dependencies.len(), 1);
        assert_eq!(rep.circular_dependencies[0].length, 3);
    }
}
