// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! T-Zero Deterministic Multi-Language AST Pruning Engine.
//! Leverages `tree-sitter` for Python, TypeScript, Rust, and Go to prune function
//! and method bodies down to `...` while preserving complete type annotations,
//! signatures, classes, interfaces, structs, and docstrings.

use serde::{Deserialize, Serialize};

/// Supported target languages for deterministic AST pruning.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum SupportedLanguage {
    Python,
    TypeScript,
    JavaScript,
    Rust,
    Go,
    Unknown,
}

/// Statistics and output of an AST pruning operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PruneResult {
    pub pruned_code: String,
    pub original_lines: usize,
    pub pruned_lines: usize,
    pub reduction_ratio: f64,
    pub language: SupportedLanguage,
}

/// Detects the target language from a file extension or language identifier string.
pub fn detect_language(identifier_or_ext: &str) -> SupportedLanguage {
    let s = identifier_or_ext.trim().to_lowercase();
    let ext = if let Some(idx) = s.rfind('.') {
        &s[idx..]
    } else {
        s.as_str()
    };

    match ext {
        "py" | "pyw" | "python" | ".py" | ".pyw" => SupportedLanguage::Python,
        "ts" | "tsx" | "typescript" | ".ts" | ".tsx" => SupportedLanguage::TypeScript,
        "js" | "jsx" | "mjs" | "cjs" | "javascript" | ".js" | ".jsx" | ".mjs" | ".cjs" => {
            SupportedLanguage::JavaScript
        }
        "rs" | "rust" | ".rs" => SupportedLanguage::Rust,
        "go" | "golang" | ".go" => SupportedLanguage::Go,
        _ => SupportedLanguage::Unknown,
    }
}

/// Prunes source code using tree-sitter AST parsing for the detected language,
/// falling back to robust lexical skeletonization if tree-sitter is unavailable or fails.
pub fn prune_code(code: &str, lang: SupportedLanguage) -> String {
    if code.trim().is_empty() {
        return String::new();
    }

    match lang {
        SupportedLanguage::Python => prune_python_ast(code),
        SupportedLanguage::TypeScript | SupportedLanguage::JavaScript => prune_typescript_ast(code),
        SupportedLanguage::Rust => prune_rust_ast(code),
        SupportedLanguage::Go => prune_go_ast(code),
        SupportedLanguage::Unknown => prune_lexical_fallback(code),
    }
}

/// Prunes source code and returns detailed metrics including line reduction ratio.
pub fn prune_code_with_stats(code: &str, lang: SupportedLanguage) -> PruneResult {
    let original_lines = code.lines().count().max(1);
    let pruned_code = prune_code(code, lang);
    let pruned_lines = pruned_code.lines().count();
    let reduction_ratio = if original_lines > 0 {
        ((original_lines.saturating_sub(pruned_lines)) as f64 / original_lines as f64 * 100.0)
            .clamp(0.0, 100.0)
    } else {
        0.0
    };

    PruneResult {
        pruned_code,
        original_lines,
        pruned_lines,
        reduction_ratio: (reduction_ratio * 10.0).round() / 10.0,
        language: lang,
    }
}

// -----------------------------------------------------------------------------
// 1. PYTHON AST PRUNER (Tree-sitter & Fallback)
// -----------------------------------------------------------------------------

fn prune_python_ast(code: &str) -> String {
    let mut parser = tree_sitter::Parser::new();
    if parser.set_language(&tree_sitter_python::language()).is_ok() {
        if let Some(tree) = parser.parse(code, None) {
            let mut replacements = Vec::new();
            collect_python_body_replacements(tree.root_node(), code.as_bytes(), &mut replacements);
            if !replacements.is_empty() {
                return apply_byte_replacements(code.as_bytes(), replacements);
            }
        }
    }
    prune_python_lexical(code)
}

fn collect_python_body_replacements(
    node: tree_sitter::Node,
    bytes: &[u8],
    replacements: &mut Vec<(usize, usize, String)>,
) {
    let kind = node.kind();
    if kind == "function_definition" || kind == "async_function_definition" {
        // Find the 'body' child node (kind: "block")
        for i in 0..node.child_count() {
            if let Some(child) = node.child(i) {
                if child.kind() == "block" {
                    let mut docstring_range = None;
                    for j in 0..child.child_count() {
                        if let Some(stmt) = child.child(j) {
                            if stmt.kind() == "expression_statement" {
                                if let Some(expr) = stmt.child(0) {
                                    if expr.kind() == "string" {
                                        docstring_range = Some(stmt.byte_range());
                                    }
                                }
                            }
                            break;
                        }
                    }

                    let block_range = child.byte_range();
                    let start_indent = get_node_indentation(child, bytes);
                    let replacement_text = if let Some(doc_range) = docstring_range {
                        let doc_bytes = &bytes[doc_range.start..doc_range.end];
                        let doc_str = std::str::from_utf8(doc_bytes).unwrap_or("");
                        format!("{}\n{}...", doc_str, start_indent)
                    } else {
                        "...".to_string()
                    };

                    replacements.push((block_range.start, block_range.end, replacement_text));
                    return; // Do not recurse into pruned function body
                }
            }
        }
    }

    // Recurse into classes and outer blocks
    for i in 0..node.child_count() {
        if let Some(child) = node.child(i) {
            collect_python_body_replacements(child, bytes, replacements);
        }
    }
}

// -----------------------------------------------------------------------------
// 2. TYPESCRIPT / JAVASCRIPT AST PRUNER
// -----------------------------------------------------------------------------

fn prune_typescript_ast(code: &str) -> String {
    let mut parser = tree_sitter::Parser::new();
    if parser.set_language(&tree_sitter_typescript::language_typescript()).is_ok() {
        if let Some(tree) = parser.parse(code, None) {
            let mut replacements = Vec::new();
            collect_brace_body_replacements(
                tree.root_node(),
                &["function_declaration", "method_definition", "arrow_function"],
                &["statement_block"],
                "/* ... */",
                &mut replacements,
            );
            if !replacements.is_empty() {
                return apply_byte_replacements(code.as_bytes(), replacements);
            }
        }
    }
    prune_brace_lexical(code, "// ...")
}

// -----------------------------------------------------------------------------
// 3. RUST AST PRUNER
// -----------------------------------------------------------------------------

fn prune_rust_ast(code: &str) -> String {
    let mut parser = tree_sitter::Parser::new();
    if parser.set_language(&tree_sitter_rust::language()).is_ok() {
        if let Some(tree) = parser.parse(code, None) {
            let mut replacements = Vec::new();
            collect_brace_body_replacements(
                tree.root_node(),
                &["function_item"],
                &["block"],
                "/* ... */",
                &mut replacements,
            );
            if !replacements.is_empty() {
                return apply_byte_replacements(code.as_bytes(), replacements);
            }
        }
    }
    prune_brace_lexical(code, "/* ... */")
}

// -----------------------------------------------------------------------------
// 4. GO AST PRUNER
// -----------------------------------------------------------------------------

fn prune_go_ast(code: &str) -> String {
    let mut parser = tree_sitter::Parser::new();
    if parser.set_language(&tree_sitter_go::language()).is_ok() {
        if let Some(tree) = parser.parse(code, None) {
            let mut replacements = Vec::new();
            collect_brace_body_replacements(
                tree.root_node(),
                &["function_declaration", "method_declaration"],
                &["block"],
                "/* ... */",
                &mut replacements,
            );
            if !replacements.is_empty() {
                return apply_byte_replacements(code.as_bytes(), replacements);
            }
        }
    }
    prune_brace_lexical(code, "// ...")
}

// -----------------------------------------------------------------------------
// HELPER: BRACE-BASED AST REPLACEMENTS (TS / Rust / Go)
// -----------------------------------------------------------------------------

fn collect_brace_body_replacements(
    node: tree_sitter::Node,
    fn_kinds: &[&str],
    body_kinds: &[&str],
    stub: &str,
    replacements: &mut Vec<(usize, usize, String)>,
) {
    let kind = node.kind();
    if fn_kinds.contains(&kind) {
        for i in 0..node.child_count() {
            if let Some(child) = node.child(i) {
                if body_kinds.contains(&child.kind()) {
                    let range = child.byte_range();
                    if range.end > range.start + 1 {
                        let replacement = format!("{{ {} }}", stub);
                        replacements.push((range.start, range.end, replacement));
                        return; // Do not recurse into pruned function body
                    }
                }
            }
        }
    }

    for i in 0..node.child_count() {
        if let Some(child) = node.child(i) {
            collect_brace_body_replacements(child, fn_kinds, body_kinds, stub, replacements);
        }
    }
}

fn get_node_indentation(node: tree_sitter::Node, bytes: &[u8]) -> String {
    let start_pos = node.start_byte();
    let mut line_start = start_pos;
    while line_start > 0 && bytes[line_start - 1] != b'\n' {
        line_start -= 1;
    }
    let mut indent = String::new();
    for &b in &bytes[line_start..start_pos] {
        if b == b' ' || b == b'\t' {
            indent.push(b as char);
        } else {
            break;
        }
    }
    if indent.is_empty() {
        "    ".to_string()
    } else {
        indent
    }
}

fn apply_byte_replacements(bytes: &[u8], mut replacements: Vec<(usize, usize, String)>) -> String {
    // Sort replacements by start index ascending
    replacements.sort_by_key(|&(start, _, _)| start);

    let mut result = Vec::new();
    let mut last_idx = 0;

    for (start, end, text) in replacements {
        if start < last_idx {
            continue; // Skip overlapping replacements
        }
        if start > last_idx {
            result.extend_from_slice(&bytes[last_idx..start]);
        }
        result.extend_from_slice(text.as_bytes());
        last_idx = end;
    }

    if last_idx < bytes.len() {
        result.extend_from_slice(&bytes[last_idx..]);
    }

    String::from_utf8_lossy(&result).to_string()
}

// -----------------------------------------------------------------------------
// DETERMINISTIC LEXICAL SKELETONIZERS (FALLBACK)
// -----------------------------------------------------------------------------

fn prune_python_lexical(code: &str) -> String {
    let mut output = Vec::new();
    let lines: Vec<&str> = code.lines().collect();
    let mut i = 0;

    while i < lines.len() {
        let line = lines[i];
        let trimmed = line.trim();

        if trimmed.starts_with("def ") || trimmed.starts_with("async def ") {
            let mut def_block = vec![line];
            let base_indent = line.len() - line.trim_start().len();

            // Handle multi-line def signatures until ':'
            while !def_block.last().unwrap().trim_end().ends_with(':') && i + 1 < lines.len() {
                i += 1;
                def_block.push(lines[i]);
            }

            for l in &def_block {
                output.push(l.to_string());
            }

            // Check if immediate next line is a docstring
            let mut docstring_lines = Vec::new();
            if i + 1 < lines.len() {
                let next_trimmed = lines[i + 1].trim();
                if next_trimmed.starts_with("\"\"\"") || next_trimmed.starts_with("'''") {
                    i += 1;
                    docstring_lines.push(lines[i]);
                    let quote = &next_trimmed[0..3];
                    if !next_trimmed[3..].contains(quote) {
                        while i + 1 < lines.len() {
                            i += 1;
                            docstring_lines.push(lines[i]);
                            if lines[i].contains(quote) {
                                break;
                            }
                        }
                    }
                }
            }

            for dl in docstring_lines {
                output.push(dl.to_string());
            }

            let body_indent = " ".repeat(base_indent + 4);
            output.push(format!("{}...", body_indent));

            // Skip the rest of the function body lines that have higher indentation
            while i + 1 < lines.len() {
                let peek = lines[i + 1];
                if peek.trim().is_empty() {
                    i += 1;
                    continue;
                }
                let peek_indent = peek.len() - peek.trim_start().len();
                if peek_indent > base_indent {
                    i += 1;
                } else {
                    break;
                }
            }
        } else {
            output.push(line.to_string());
        }
        i += 1;
    }

    output.join("\n")
}

fn prune_brace_lexical(code: &str, stub: &str) -> String {
    let mut output = Vec::new();
    let mut brace_depth: i32 = 0;
    let mut inside_fn = false;
    let mut fn_brace_depth: i32 = 0;

    for line in code.lines() {
        let trimmed = line.trim();
        let is_fn_decl = trimmed.starts_with("fn ")
            || trimmed.starts_with("pub fn ")
            || trimmed.starts_with("pub(crate) fn ")
            || trimmed.starts_with("async fn ")
            || trimmed.starts_with("pub async fn ")
            || trimmed.starts_with("function ")
            || trimmed.starts_with("async function ")
            || trimmed.starts_with("export function ")
            || trimmed.starts_with("export async function ")
            || trimmed.starts_with("export default function ")
            || trimmed.starts_with("func ");

        if is_fn_decl && !inside_fn {
            inside_fn = true;
            fn_brace_depth = brace_depth;
        }

        let open_count = trimmed.chars().filter(|&c| c == '{').count() as i32;
        let close_count = trimmed.chars().filter(|&c| c == '}').count() as i32;
        brace_depth += open_count - close_count;

        if inside_fn {
            if trimmed.contains('{') {
                let prefix = line.split('{').next().unwrap_or("");
                output.push(format!("{}{{ {} }}", prefix, stub));
                if brace_depth <= fn_brace_depth {
                    inside_fn = false;
                }
                continue;
            } else if brace_depth <= fn_brace_depth {
                inside_fn = false;
            }
            continue;
        }

        output.push(line.to_string());
    }

    output.join("\n")
}

fn prune_lexical_fallback(code: &str) -> String {
    prune_python_lexical(code)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_python_function_pruning() {
        let code = r#"
def calculate_tax(income: float, rate: float = 0.2) -> float:
    """Calculates tax liability."""
    if income <= 0:
        return 0.0
    return income * rate
"#;
        let pruned = prune_code(code, SupportedLanguage::Python);
        assert!(pruned.contains("def calculate_tax"));
        assert!(pruned.contains("income: float"));
        assert!(pruned.contains("-> float:"));
        assert!(pruned.contains("..."));
        assert!(!pruned.contains("income * rate"));
    }

    #[test]
    fn test_rust_function_pruning() {
        let code = r#"
pub fn compute_sum(a: i32, b: i32) -> i32 {
    let result = a + b;
    result * 2
}
"#;
        let pruned = prune_code(code, SupportedLanguage::Rust);
        assert!(pruned.contains("pub fn compute_sum"));
        assert!(pruned.contains("-> i32"));
        assert!(pruned.contains("/* ... */") || pruned.contains("..."));
        assert!(!pruned.contains("result * 2"));
    }

    #[test]
    fn test_typescript_function_pruning() {
        let code = r#"
export function calculateVelocity(distance: number, time: number): number {
    const v = distance / time;
    return v;
}
"#;
        let pruned = prune_code(code, SupportedLanguage::TypeScript);
        assert!(pruned.contains("calculateVelocity"));
        assert!(pruned.contains("distance: number"));
        assert!(!pruned.contains("const v = distance / time;"));
    }

    #[test]
    fn test_go_function_pruning() {
        let code = r#"
func (s *OrderService) ProcessOrder(orderID string) (bool, error) {
    if orderID == "" {
        return false, errors.New("empty order")
    }
    return true, nil
}
"#;
        let pruned = prune_code(code, SupportedLanguage::Go);
        assert!(pruned.contains("ProcessOrder"));
        assert!(pruned.contains("orderID string"));
        assert!(!pruned.contains("empty order"));
    }
}
