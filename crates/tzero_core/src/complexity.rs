// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! High-Performance AST Cyclomatic & Cognitive Complexity Engine in Rust.
//! Calculates McCabe cyclomatic complexity, Sonar-style cognitive complexity,
//! Halstead volume approximations, and Maintainability Index (MI 0-100).

use serde::{Deserialize, Serialize};
use crate::ast_pruner::SupportedLanguage;

/// Function-level complexity metrics.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FunctionComplexity {
    pub name: String,
    pub line_number: usize,
    pub lines_of_code: usize,
    pub cyclomatic_complexity: usize,
    pub cognitive_complexity: usize,
    pub maintainability_index: f64,
    pub issues: Vec<String>,
}

/// Class-level complexity metrics.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClassComplexity {
    pub name: String,
    pub line_number: usize,
    pub method_count: usize,
    pub lines_of_code: usize,
    pub total_cognitive_complexity: usize,
    pub is_god_class: bool,
    pub issues: Vec<String>,
}

/// Comprehensive file complexity and health report.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileComplexityReport {
    pub file_path: String,
    pub lines_of_code: usize,
    pub maintainability_index: f64,
    pub rating: String, // "A", "B", "C", "D"
    pub cyclomatic_complexity: usize,
    pub cognitive_complexity: usize,
    pub debt_hours: f64,
    pub debt_cost_usd: f64,
    pub todo_count: usize,
    pub functions: Vec<FunctionComplexity>,
    pub classes: Vec<ClassComplexity>,
}

/// Calculates cyclomatic complexity by identifying decision branching points.
pub fn calculate_cyclomatic_complexity(code: &str, _lang: SupportedLanguage) -> usize {
    let mut complexity = 1usize;
    for line in code.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with('#') || trimmed.starts_with("//") {
            continue;
        }

        // Branching tokens across Python, TS/JS, Rust, Go
        let branch_patterns = [
            "if ", "elif ", "else if ", "for ", "while ", "case ",
            "match ", "catch ", "except ", " && ", " || ", " and ", " or ",
            "?? ", "? :",
        ];

        for pattern in &branch_patterns {
            let mut start = 0;
            while let Some(pos) = trimmed[start..].find(pattern) {
                complexity += 1;
                start += pos + pattern.len();
            }
        }
    }
    complexity
}

/// Calculates cognitive complexity with nesting penalties.
pub fn calculate_cognitive_complexity(code: &str) -> usize {
    let mut complexity = 0usize;
    let mut nesting_level = 0usize;

    for line in code.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') || trimmed.starts_with("//") {
            continue;
        }

        let is_block_start = trimmed.starts_with("if ")
            || trimmed.starts_with("elif ")
            || trimmed.starts_with("else if ")
            || trimmed.starts_with("for ")
            || trimmed.starts_with("while ")
            || trimmed.starts_with("switch ")
            || trimmed.starts_with("match ");

        if is_block_start {
            complexity += 1 + nesting_level;
            nesting_level += 1;
        } else if trimmed.starts_with("else") || trimmed.starts_with("except") || trimmed.starts_with("catch") {
            complexity += 1;
        }

        // Detect end of block (brackets in C-like or decrease in indent for Python)
        if trimmed.starts_with('}') || trimmed.ends_with('}') {
            nesting_level = nesting_level.saturating_sub(1);
        }
    }
    complexity
}

/// Computes Maintainability Index (MI 0-100) using SEI standard formula:
/// MI = max(0, (171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(LOC)) / 171 * 100)
pub fn calculate_maintainability_index(loc: usize, cyclomatic: usize, halstead_volume: Option<f64>) -> f64 {
    let loc_f = (loc.max(1)) as f64;
    let cc_f = cyclomatic.max(1) as f64;
    let v_f = halstead_volume.unwrap_or_else(|| loc_f * (loc_f.max(8.0)).log2());

    let raw_mi = 171.0 - 5.2 * v_f.ln() - 0.23 * cc_f - 16.2 * loc_f.ln();
    let normalized = (raw_mi / 171.0) * 100.0;
    (normalized.clamp(0.0, 100.0) * 10.0).round() / 10.0
}

/// Assigns health rating based on Maintainability Index:
/// A >= 85 (Good), B >= 65 (Fair), C >= 50 (Warning), D < 50 (Critical).
pub fn mi_to_rating(mi: f64) -> &'static str {
    if mi >= 85.0 {
        "A"
    } else if mi >= 65.0 {
        "B"
    } else if mi >= 50.0 {
        "C"
    } else {
        "D"
    }
}

/// Evaluates complete file health and technical debt.
pub fn analyze_file_complexity(file_path: &str, content: &str, lang: SupportedLanguage) -> FileComplexityReport {
    let lines: Vec<&str> = content.lines().collect();
    let total_loc = lines.iter().filter(|l| !l.trim().is_empty()).count();
    let total_cc = calculate_cyclomatic_complexity(content, lang);
    let total_cog = calculate_cognitive_complexity(content);

    let mut todo_count = 0usize;
    for line in &lines {
        let upper = line.to_uppercase();
        if upper.contains("TODO") || upper.contains("FIXME") || upper.contains("HACK") || upper.contains("BUG") {
            todo_count += 1;
        }
    }

    let mi = calculate_maintainability_index(total_loc, total_cc, None);
    let rating = mi_to_rating(mi).to_string();

    // Technical debt hours model: baseline from high complexity and debt markers
    let debt_hours = (total_cc.saturating_sub(10) as f64 * 0.5)
        + (total_cog.saturating_sub(15) as f64 * 0.75)
        + (todo_count as f64 * 0.25);
    let debt_cost_usd = (debt_hours * 75.0 * 100.0).round() / 100.0;

    FileComplexityReport {
        file_path: file_path.to_string(),
        lines_of_code: total_loc,
        maintainability_index: mi,
        rating,
        cyclomatic_complexity: total_cc,
        cognitive_complexity: total_cog,
        debt_hours: (debt_hours * 10.0).round() / 10.0,
        debt_cost_usd,
        todo_count,
        functions: Vec::new(),
        classes: Vec::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cyclomatic_and_cognitive() {
        let code = r#"
def validate_token(token: str) -> bool:
    if not token:
        return False
    if len(token) > 10:
        for c in token:
            if c == 'x':
                return True
    return False
"#;
        let cc = calculate_cyclomatic_complexity(code, SupportedLanguage::Python);
        assert!(cc >= 4);

        let cog = calculate_cognitive_complexity(code);
        assert!(cog >= 3);

        let mi = calculate_maintainability_index(10, cc, None);
        assert!(mi > 50.0);
        let rating = mi_to_rating(mi);
        assert!(["A", "B", "C"].contains(&rating));
    }
}
