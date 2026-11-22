// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! T-Zero Multi-Tier Hierarchical AST Context Tree Engine.
//! Scans codebases recursively and builds compact Tier 1-4 representations
//! delivering up to 95% token reduction for LLM context windows.

use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};
use serde::{Deserialize, Serialize};

use crate::ast_pruner::{detect_language, prune_code};
use crate::tokenizer::count_tokens;

/// Context hierarchy tier (T-1 to T-4).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ContextTier {
    /// Tier 1: High-level architectural directory topology & token census.
    Overview = 1,
    /// Tier 2: File symbols, classes, functions, and interface skeletons.
    InterfaceSkeleton = 2,
    /// Tier 3: Complete signatures, docstrings, and pruned AST stubs (...).
    SignatureStubs = 3,
    /// Tier 4: Full unpruned source code with AST grounding metadata.
    FullImplementation = 4,
}

impl ContextTier {
    pub fn from_u32(val: u32) -> Self {
        match val {
            1 => ContextTier::Overview,
            2 => ContextTier::InterfaceSkeleton,
            4 => ContextTier::FullImplementation,
            _ => ContextTier::SignatureStubs,
        }
    }
}

/// Statistics for a single scanned source file.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileContextNode {
    pub path: String,
    pub relative_path: String,
    pub extension: String,
    pub lines: usize,
    pub raw_tokens: usize,
    pub pruned_tokens: usize,
    pub symbols: Vec<String>,
    pub snippet: String,
}

/// Aggregated multi-tier context tree report.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextTreeResult {
    pub root_dir: String,
    pub tier: u32,
    pub total_files: usize,
    pub total_lines: usize,
    pub raw_tokens: usize,
    pub pruned_tokens: usize,
    pub token_reduction_percent: f64,
    pub files: Vec<FileContextNode>,
    pub formatted_tree: String,
}

const DEFAULT_IGNORED_DIRS: &[&str] = &[
    ".git", "node_modules", "venv", ".venv", "__pycache__", "dist",
    "build", "target", ".pytest_cache", ".gemini", ".idea", ".vscode",
    "egg-info", ".eggs", ".tox", ".mypy_cache"
];

const CODE_EXTENSIONS: &[&str] = &[
    "py", "rs", "ts", "js", "go", "json", "toml", "yaml", "yml", "md", "sql", "sh"
];

/// Recursively scans directory and builds multi-tier AST context tree.
pub fn build_context_tree(root_dir: &str, tier: u32, max_depth: Option<usize>) -> ContextTreeResult {
    let root_path = Path::new(root_dir);
    let mut files_collected = Vec::new();
    let depth_limit = max_depth.unwrap_or(20);

    let ignored_set: HashSet<&str> = DEFAULT_IGNORED_DIRS.iter().copied().collect();

    fn scan_dir(
        dir: &Path,
        root: &Path,
        current_depth: usize,
        max_depth: usize,
        ignored: &HashSet<&str>,
        collected: &mut Vec<PathBuf>,
    ) {
        if current_depth > max_depth {
            return;
        }
        let entries = match fs::read_dir(dir) {
            Ok(e) => e,
            Err(_) => return,
        };

        for entry in entries.flatten() {
            let path = entry.path();
            let file_name = match path.file_name().and_then(|n| n.to_str()) {
                Some(n) => n,
                None => continue,
            };

            if path.is_dir() {
                if !ignored.contains(file_name) && !file_name.starts_with('.') {
                    scan_dir(&path, root, current_depth + 1, max_depth, ignored, collected);
                }
            } else if path.is_file() {
                if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
                    if CODE_EXTENSIONS.contains(&ext) {
                        collected.push(path);
                    }
                }
            }
        }
    }

    if root_path.is_dir() {
        scan_dir(root_path, root_path, 0, depth_limit, &ignored_set, &mut files_collected);
    } else if root_path.is_file() {
        files_collected.push(root_path.to_path_buf());
    }

    files_collected.sort();

    let mut nodes = Vec::new();
    let mut total_lines = 0;
    let mut total_raw_tokens = 0;
    let mut total_pruned_tokens = 0;

    let tier_enum = ContextTier::from_u32(tier);

    for p in &files_collected {
        let content = fs::read_to_string(p).unwrap_or_default();
        let lines = content.lines().count();
        total_lines += lines;

        let raw_toks = count_tokens(&content, "gpt-4o");
        total_raw_tokens += raw_toks;

        let rel_path = match p.strip_prefix(root_path) {
            Ok(rel) => rel.to_string_lossy().replace('\\', "/"),
            Err(_) => p.to_string_lossy().replace('\\', "/"),
        };
        let ext = p.extension().and_then(|e| e.to_str()).unwrap_or("").to_string();

        let lang = detect_language(&rel_path);

        let (snippet, pruned_toks) = match tier_enum {
            ContextTier::Overview => {
                let s = format!("// [T-1] File: {} ({} lines, {} raw tokens)", rel_path, lines, raw_toks);
                let t = count_tokens(&s, "gpt-4o");
                (s, t)
            }
            ContextTier::InterfaceSkeleton => {
                let pruned = prune_code(&content, lang);
                // Keep only function/class headers
                let skeleton: Vec<&str> = pruned
                    .lines()
                    .filter(|l| {
                        let trimmed = l.trim_start();
                        trimmed.starts_with("def ")
                            || trimmed.starts_with("class ")
                            || trimmed.starts_with("async def ")
                            || trimmed.starts_with("pub fn ")
                            || trimmed.starts_with("fn ")
                            || trimmed.starts_with("pub struct ")
                            || trimmed.starts_with("pub enum ")
                            || trimmed.starts_with("export function ")
                            || trimmed.starts_with("export class ")
                            || trimmed.starts_with("export interface ")
                    })
                    .collect();
                let s = skeleton.join("\n");
                let t = count_tokens(&s, "gpt-4o");
                (s, t)
            }
            ContextTier::SignatureStubs => {
                let pruned = prune_code(&content, lang);
                let t = count_tokens(&pruned, "gpt-4o");
                (pruned, t)
            }
            ContextTier::FullImplementation => {
                (content.clone(), raw_toks)
            }
        };

        total_pruned_tokens += pruned_toks;

        // Quick extract symbols
        let mut symbols = Vec::new();
        for line in content.lines() {
            let tr = line.trim();
            if tr.starts_with("def ") || tr.starts_with("async def ") {
                if let Some(rest) = tr.strip_prefix("def ").or_else(|| tr.strip_prefix("async def ")) {
                    if let Some(name) = rest.split('(').next() {
                        symbols.push(format!("fn:{}", name.trim()));
                    }
                }
            } else if tr.starts_with("class ") {
                if let Some(rest) = tr.strip_prefix("class ") {
                    let name = rest.split(&['(', ':'][..]).next().unwrap_or("").trim();
                    symbols.push(format!("class:{}", name));
                }
            } else if tr.starts_with("pub fn ") || tr.starts_with("fn ") {
                let rest = tr.strip_prefix("pub fn ").unwrap_or_else(|| tr.strip_prefix("fn ").unwrap());
                if let Some(name) = rest.split('(').next() {
                    symbols.push(format!("fn:{}", name.trim()));
                }
            }
        }

        nodes.push(FileContextNode {
            path: p.to_string_lossy().to_string(),
            relative_path: rel_path,
            extension: ext,
            lines,
            raw_tokens: raw_toks,
            pruned_tokens: pruned_toks,
            symbols,
            snippet,
        });
    }

    let reduction = if total_raw_tokens > 0 {
        ((total_raw_tokens.saturating_sub(total_pruned_tokens)) as f64 / total_raw_tokens as f64) * 100.0
    } else {
        0.0
    };

    // Format human-readable ASCII context tree
    let mut tree_lines = Vec::new();
    tree_lines.push(format!(
        "T-ZERO CONTEXT TREE (Tier {}: {:?}) | {} files, {} lines",
        tier, tier_enum, nodes.len(), total_lines
    ));
    tree_lines.push(format!(
        "Tokens: {} raw -> {} context ({}% reduction)",
        total_raw_tokens, total_pruned_tokens, format!("{:.1}", reduction)
    ));
    tree_lines.push("------------------------------------------------------------------------".to_string());

    for node in &nodes {
        tree_lines.push(format!("+-- {} ({} lines, ~{} tokens)", node.relative_path, node.lines, node.pruned_tokens));
        if tier_enum != ContextTier::Overview && !node.symbols.is_empty() {
            for sym in node.symbols.iter().take(6) {
                tree_lines.push(format!("    |-- {}", sym));
            }
            if node.symbols.len() > 6 {
                tree_lines.push(format!("    |-- ... ({} more symbols)", node.symbols.len() - 6));
            }
        }
    }

    let formatted_tree = tree_lines.join("\n");

    ContextTreeResult {
        root_dir: root_dir.to_string(),
        tier,
        total_files: nodes.len(),
        total_lines,
        raw_tokens: total_raw_tokens,
        pruned_tokens: total_pruned_tokens,
        token_reduction_percent: (reduction * 10.0).round() / 10.0,
        files: nodes,
        formatted_tree,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn test_build_context_tree_basic() {
        let unique_id = format!("tzero_test_{}", std::process::id());
        let test_dir = std::env::temp_dir().join(unique_id);
        fs::create_dir_all(&test_dir).unwrap();
        let file1 = test_dir.join("calc.py");
        let mut f1 = fs::File::create(&file1).unwrap();
        writeln!(f1, "def add(a, b):\n    return a + b\n\ndef sub(a, b):\n    return a - b\n").unwrap();

        let res = build_context_tree(test_dir.to_str().unwrap(), 3, None);
        assert_eq!(res.total_files, 1);
        assert!(res.raw_tokens > 0);
        assert_eq!(res.tier, 3);
        assert!(res.formatted_tree.contains("calc.py"));

        let _ = fs::remove_dir_all(test_dir);
    }
}
