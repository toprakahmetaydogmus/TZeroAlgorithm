// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! Autonomous AST Public API Contract & Semantic Versioning Guardian in Rust.
//! Inspects function signatures and public symbols between revisions, identifying breaking
//! changes (removed symbols, non-default parameters) and recommending SemVer bumps.

use std::collections::{HashMap, HashSet};
use serde::{Deserialize, Serialize};

/// SemVer bump classification.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SemVerBump {
    Patch,
    Minor,
    Major,
}

impl SemVerBump {
    pub fn as_str(&self) -> &'static str {
        match self {
            SemVerBump::Patch => "PATCH",
            SemVerBump::Minor => "MINOR",
            SemVerBump::Major => "MAJOR",
        }
    }
}

/// Description of a specific contract modification or violation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContractDiff {
    pub severity: String, // "BREAKING", "ADDITION", "MODIFICATION"
    pub category: String, // "REMOVED_SYMBOL", "ADDED_PARAM_WITHOUT_DEFAULT", "NEW_SYMBOL"
    pub symbol: String,
    pub details: String,
}

/// Comprehensive API contract audit report.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContractReport {
    pub recommended_bump: String, // "MAJOR", "MINOR", "PATCH"
    pub is_breaking: bool,
    pub breaking_changes: Vec<ContractDiff>,
    pub non_breaking_additions: Vec<ContractDiff>,
    pub internal_modifications: Vec<ContractDiff>,
}

/// Extracted parameter representation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ParameterSignature {
    pub name: String,
    pub has_default: bool,
}

/// Compares public function signatures between two source code snapshots.
pub fn compare_api_contracts(
    old_code: &str,
    new_code: &str,
) -> ContractReport {
    let old_funcs = parse_signatures(old_code);
    let new_funcs = parse_signatures(new_code);

    let mut breaking = Vec::new();
    let mut additions = Vec::new();
    let mut modifications = Vec::new();

    let old_names: HashSet<&String> = old_funcs.keys().collect();
    let new_names: HashSet<&String> = new_funcs.keys().collect();

    // 1. Check for removed public symbols -> MAJOR BREAKING
    for &removed in old_names.difference(&new_names) {
        if !removed.starts_with('_') {
            breaking.push(ContractDiff {
                severity: "BREAKING".to_string(),
                category: "REMOVED_SYMBOL".to_string(),
                symbol: removed.clone(),
                details: format!("Public function/symbol '{}' was removed.", removed),
            });
        }
    }

    // 2. Check for newly added symbols -> MINOR ADDITION
    for &added in new_names.difference(&old_names) {
        if !added.starts_with('_') {
            additions.push(ContractDiff {
                severity: "ADDITION".to_string(),
                category: "NEW_SYMBOL".to_string(),
                symbol: added.clone(),
                details: format!("New public function/symbol '{}' was introduced.", added),
            });
        }
    }

    // 3. Check for modified existing signatures
    for &common in old_names.intersection(&new_names) {
        let old_sig = &old_funcs[common];
        let new_sig = &new_funcs[common];

        if old_sig != new_sig {
            // Check if required parameters without defaults were added
            let old_param_names: HashSet<String> = old_sig.iter().map(|p| p.name.clone()).collect();
            let mut broke = false;

            for p in new_sig {
                if !old_param_names.contains(&p.name) && !p.has_default {
                    breaking.push(ContractDiff {
                        severity: "BREAKING".to_string(),
                        category: "ADDED_PARAM_WITHOUT_DEFAULT".to_string(),
                        symbol: common.clone(),
                        details: format!(
                            "Required parameter '{}' added to '{}' without default value.",
                            p.name, common
                        ),
                    });
                    broke = true;
                    break;
                }
            }

            if !broke {
                modifications.push(ContractDiff {
                    severity: "MODIFICATION".to_string(),
                    category: "SIGNATURE_TWEAK".to_string(),
                    symbol: common.clone(),
                    details: format!("Signature of '{}' updated compatibly.", common),
                });
            }
        }
    }

    let is_breaking = !breaking.is_empty();
    let recommended_bump = if is_breaking {
        SemVerBump::Major
    } else if !additions.is_empty() {
        SemVerBump::Minor
    } else {
        SemVerBump::Patch
    };

    ContractReport {
        recommended_bump: recommended_bump.as_str().to_string(),
        is_breaking,
        breaking_changes: breaking,
        non_breaking_additions: additions,
        internal_modifications: modifications,
    }
}

/// Parses function definitions and extract parameters with default-value flags.
fn parse_signatures(code: &str) -> HashMap<String, Vec<ParameterSignature>> {
    let mut map = HashMap::new();
    for line in code.lines() {
        let trimmed = line.trim();
        // Python def, Rust fn, TS function
        let is_func = trimmed.starts_with("def ")
            || trimmed.starts_with("pub fn ")
            || trimmed.starts_with("fn ")
            || trimmed.starts_with("export function ")
            || trimmed.starts_with("function ");

        if !is_func {
            continue;
        }

        let name_start = if trimmed.starts_with("def ") {
            4
        } else if trimmed.starts_with("pub fn ") {
            7
        } else if trimmed.starts_with("fn ") {
            3
        } else if trimmed.starts_with("export function ") {
            16
        } else {
            9
        };

        if let Some(open_paren) = trimmed[name_start..].find('(') {
            let func_name = trimmed[name_start..name_start + open_paren].trim().to_string();
            if let Some(close_paren) = trimmed.find(')') {
                let params_str = &trimmed[name_start + open_paren + 1..close_paren];
                let mut params = Vec::new();
                for raw_p in params_str.split(',') {
                    let p = raw_p.trim();
                    if p.is_empty() || p == "self" || p == "&self" || p == "&mut self" {
                        continue;
                    }
                    let has_default = p.contains('=');
                    let p_name = p.split([':', '=']).next().unwrap_or(p).trim().to_string();
                    params.push(ParameterSignature {
                        name: p_name,
                        has_default,
                    });
                }
                map.insert(func_name, params);
            }
        }
    }
    map
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_breaking_change_detection() {
        let old = "def process_order(order_id: int): pass\ndef fetch_data(): pass\n";
        let new_breaking = "def process_order(order_id: int, new_flag: bool): pass\n"; // Removed fetch_data & added required param

        let report = compare_api_contracts(old, new_breaking);
        assert!(report.is_breaking);
        assert_eq!(report.recommended_bump, "MAJOR");
        assert!(report.breaking_changes.iter().any(|b| b.category == "REMOVED_SYMBOL"));
    }

    #[test]
    fn test_compatible_addition() {
        let old = "def compute(x: int): pass\n";
        let new_compatible = "def compute(x: int, bonus: int = 0): pass\ndef helper(): pass\n";

        let report = compare_api_contracts(old, new_compatible);
        assert!(!report.is_breaking);
        assert_eq!(report.recommended_bump, "MINOR");
    }
}
