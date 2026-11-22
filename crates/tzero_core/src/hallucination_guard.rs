// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! T-Zero AST Hallucination Guard & Proof Engine.
//! Eliminates AI coding hallucinations before code is committed by validating
//! imported modules, class names, and function call signatures against the workspace AST symbol map.

use std::collections::HashSet;
use regex::Regex;
use serde::{Deserialize, Serialize};

use crate::fuzzy_matcher::fuzzy_similarity;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HallucinatedSymbol {
    pub symbol: String,
    pub kind: String,
    pub line: usize,
    pub suggested_replacement: Option<String>,
    pub similarity_confidence: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HallucinationReport {
    pub total_symbols_checked: usize,
    pub hallucination_count: usize,
    pub hallucination_free: bool,
    pub safety_score: f64,
    pub hallucinations: Vec<HallucinatedSymbol>,
}

/// Standard language built-ins and keywords to avoid false positive hallucinations.
const STANDARD_BUILTINS: &[&str] = &[
    "print", "len", "range", "str", "int", "float", "bool", "list", "dict", "set",
    "tuple", "enumerate", "zip", "map", "filter", "min", "max", "sum", "sorted",
    "open", "isinstance", "issubclass", "hasattr", "getattr", "setattr", "delattr",
    "any", "all", "round", "abs", "repr", "iter", "next", "super", "format",
    "console", "require", "process", "Math", "JSON", "Promise", "Array", "Object",
    "String", "Number", "Boolean", "RegExp", "Error", "println", "eprintln", "format",
    "vec", "panic", "assert", "assert_eq", "Some", "None", "Ok", "Err"
];

/// Validates proposed code against a slice of known valid repository symbols.
pub fn verify_hallucinations(
    proposed_code: &str,
    valid_symbols: &[&str],
) -> HallucinationReport {
    let mut valid_set: HashSet<&str> = valid_symbols.iter().copied().collect();
    for &b in STANDARD_BUILTINS {
        valid_set.insert(b);
    }

    let mut detected = Vec::new();
    let mut checked_count: usize = 0;

    let import_regex = Regex::new(r"(?m)^(?:from\s+([a-zA-Z0-9_\.]+)\s+import\s+([a-zA-Z0-9_,\s]+)|import\s+([a-zA-Z0-9_,\s]+))").unwrap();
    let call_regex = Regex::new(r"([a-zA-Z0-9_]+)\s*\(").unwrap();

    // Check imports
    for cap in import_regex.captures_iter(proposed_code) {
        if let Some(m) = cap.get(2) {
            for part in m.as_str().split(',') {
                let sym = part.trim();
                if !sym.is_empty() && !sym.contains('*') {
                    checked_count += 1;
                    if !valid_set.contains(sym) {
                        let (best_match, score) = find_best_candidate(sym, valid_symbols);
                        detected.push(HallucinatedSymbol {
                            symbol: sym.to_string(),
                            kind: "imported_symbol".to_string(),
                            line: 1,
                            suggested_replacement: best_match,
                            similarity_confidence: score,
                        });
                    }
                }
            }
        }
    }

    // Check invocations
    for (line_idx, line) in proposed_code.lines().enumerate() {
        let trimmed = line.trim();
        if trimmed.starts_with('#')
            || trimmed.starts_with("//")
            || trimmed.starts_with("def ")
            || trimmed.starts_with("async def ")
            || trimmed.starts_with("class ")
            || trimmed.starts_with("fn ")
            || trimmed.starts_with("pub fn ")
        {
            continue;
        }

        for cap in call_regex.captures_iter(line) {
            if let Some(m) = cap.get(1) {
                let call_name = m.as_str();
                // Ignore language keywords
                if matches!(call_name, "if" | "while" | "for" | "with" | "match" | "switch" | "catch") {
                    continue;
                }

                checked_count += 1;
                if !valid_set.contains(call_name) {
                    let (best_match, score) = find_best_candidate(call_name, valid_symbols);
                    // Only flag if not a private method or very common pattern
                    if score >= 0.6 || !call_name.starts_with('_') {
                        detected.push(HallucinatedSymbol {
                            symbol: call_name.to_string(),
                            kind: "call_identifier".to_string(),
                            line: line_idx + 1,
                            suggested_replacement: best_match,
                            similarity_confidence: score,
                        });
                    }
                }
            }
        }
    }

    // Deduplicate detections by (symbol, kind)
    let mut seen = HashSet::new();
    let unique_detected: Vec<HallucinatedSymbol> = detected
        .into_iter()
        .filter(|d| seen.insert((d.symbol.clone(), d.kind.clone())))
        .collect();

    let total: usize = checked_count.max(1);
    let hallucination_count: usize = unique_detected.len();
    let safety_score: f64 = ((total.saturating_sub(hallucination_count)) as f64 / total as f64) * 100.0_f64;

    HallucinationReport {
        total_symbols_checked: total,
        hallucination_count,
        hallucination_free: hallucination_count == 0,
        safety_score: (safety_score * 10.0).round() / 10.0,
        hallucinations: unique_detected,
    }
}

fn find_best_candidate(target: &str, candidates: &[&str]) -> (Option<String>, f64) {
    let mut best_score = 0.0;
    let mut best_str = None;

    for &c in candidates {
        let sim = fuzzy_similarity(target, c);
        if sim > best_score && sim >= 0.5 {
            best_score = sim;
            best_str = Some(c.to_string());
        }
    }

    (best_str, (best_score * 100.0).round() / 100.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_code_no_hallucinations() {
        let valid = ["calculate_total", "fetch_user", "DatabaseClient"];
        let code = r#"
from mymodule import fetch_user, DatabaseClient

def run():
    client = DatabaseClient()
    user = fetch_user(123)
    print(user)
"#;
        let rep = verify_hallucinations(code, &valid);
        assert!(rep.hallucination_free);
        assert_eq!(rep.hallucination_count, 0);
    }

    #[test]
    fn test_detect_hallucinated_function() {
        let valid = ["calculate_total", "fetch_user"];
        let code = r#"
def run():
    x = calculate_totals() # Typo / hallucination
    print(x)
"#;
        let rep = verify_hallucinations(code, &valid);
        assert!(!rep.hallucination_free);
        assert_eq!(rep.hallucination_count, 1);
        assert_eq!(rep.hallucinations[0].symbol, "calculate_totals");
        assert_eq!(rep.hallucinations[0].suggested_replacement.as_deref(), Some("calculate_total"));
    }
}
