// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)
// Additional terms under AGPL-3.0 section 7: see NOTICE in the distribution
// or https://github.com/toprakahmetaydogmus/TZeroAlgorithm/blob/main/NOTICE.

// -*- coding: utf-8 -*-
//! T-Zero Turbo Rust Hybrid Core Engine (v12.1.4)
//! Ultra-High Performance Multi-Language AST Pruning, Shannon Entropy Zero-Leak Guard & BPE Tokenizer.
//! Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
//! License: AGPL-3.0-only

pub mod ast_pruner;
pub mod bm25_search;
pub mod boundary_guard;
pub mod complexity;
pub mod context_tree;
pub mod contracts;
pub mod duplicity;
pub mod entropy_guard;
pub mod fuzzy_matcher;
pub mod hallucination_guard;
pub mod mcp_server;
pub mod pagerank;
pub mod python_bindings;
pub mod reachability;
pub mod symbol_graph;
pub mod token_cost;
pub mod tokenizer;

pub use ast_pruner::{detect_language, prune_code, prune_code_with_stats, SupportedLanguage};
pub use boundary_guard::{enforce_boundaries, ArchLayer, BoundaryReport, BoundaryViolation, CircularDependency};
pub use complexity::{
    analyze_file_complexity, calculate_cognitive_complexity, calculate_cyclomatic_complexity,
    calculate_maintainability_index, mi_to_rating, FileComplexityReport, FunctionComplexity,
};
pub use context_tree::{build_context_tree, ContextTier, ContextTreeResult, FileContextNode};
pub use contracts::{compare_api_contracts, ContractDiff, ContractReport, SemVerBump};
pub use duplicity::{find_code_duplicity, DuplicateBlock, DuplicityReport};
pub use entropy_guard::{
    calculate_shannon_entropy, calculate_shannon_entropy_bytes, is_placeholder, is_whitelisted,
    redact_entropy_secrets, scan_entropy_secrets, EntropyFinding, MIN_ENTROPY_LENGTH,
    MIN_ENTROPY_THRESHOLD,
};
pub use fuzzy_matcher::{
    damerau_levenshtein_distance, fuzzy_similarity, fuzzy_symbol_search, FuzzyMatch,
};
pub use hallucination_guard::{verify_hallucinations, HallucinatedSymbol, HallucinationReport};
pub use mcp_server::run_mcp_stdio_server;
pub use pagerank::{compute_pagerank, PageRankResult};
pub use reachability::{analyze_reachability, ReachabilityReport};
pub use token_cost::{
    compare_all_models, estimate_cost_for_model, get_standard_pricing,
    ModelComparisonReport, ModelPricing, TokenCostEstimate,
};
pub use tokenizer::{count_tokens, count_tokens_by_encoding, resolve_encoding_name};

use std::collections::HashSet;
use std::slice;

use pyo3::prelude::*;

/// Deterministic 64-bit FNV-1a hash matching Python `RustCoreBridge.fnv1a_hash`.
pub fn fnv1a_hash64_bytes(bytes: &[u8]) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for &b in bytes {
        h ^= b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}

/// Deterministic byte n-gram Jaccard similarity in [0.0, 1.0].
pub fn jaccard_shingles_bytes(a: &[u8], b: &[u8], ngram: usize) -> f64 {
    if a == b {
        return 1.0;
    }
    let n = ngram.max(1);
    if a.len() < n || b.len() < n {
        let sa = String::from_utf8_lossy(a);
        let sb = String::from_utf8_lossy(b);
        let ta: HashSet<&str> = sa.split_whitespace().collect();
        let tb: HashSet<&str> = sb.split_whitespace().collect();
        let union = ta.union(&tb).count();
        return if union == 0 {
            1.0
        } else {
            ta.intersection(&tb).count() as f64 / union as f64
        };
    }
    let ta: HashSet<u64> = a.windows(n).map(fnv1a_hash64_bytes).collect();
    let tb: HashSet<u64> = b.windows(n).map(fnv1a_hash64_bytes).collect();
    let union = ta.union(&tb).count();
    if union == 0 {
        1.0
    } else {
        ta.intersection(&tb).count() as f64 / union as f64
    }
}

// ==============================================================================
// C-ABI EXPORTS (usable from ctypes and WASI hosts)
// ==============================================================================

/// C-ABI export for 64-bit FNV-1a hash computation.
#[no_mangle]
pub unsafe extern "C" fn tzero_fnv1a_hash64(ptr: *const u8, len: usize) -> u64 {
    if ptr.is_null() {
        return 0;
    }
    let data = slice::from_raw_parts(ptr, len);
    fnv1a_hash64_bytes(data)
}

/// C-ABI export for shingle Jaccard similarity in [0.0, 1.0].
#[no_mangle]
pub unsafe extern "C" fn tzero_jaccard_shingles_f64(
    a_ptr: *const u8,
    a_len: usize,
    b_ptr: *const u8,
    b_len: usize,
    ngram: usize,
) -> f64 {
    if a_ptr.is_null() || b_ptr.is_null() {
        return 0.0;
    }
    let a = slice::from_raw_parts(a_ptr, a_len);
    let b = slice::from_raw_parts(b_ptr, b_len);
    jaccard_shingles_bytes(a, b, ngram)
}

/// C-ABI export for Shannon entropy calculation.
#[no_mangle]
pub unsafe extern "C" fn tzero_shannon_entropy(ptr: *const u8, len: usize) -> f64 {
    if ptr.is_null() || len == 0 {
        return 0.0;
    }
    let data = slice::from_raw_parts(ptr, len);
    match std::str::from_utf8(data) {
        Ok(s) => calculate_shannon_entropy(s),
        Err(_) => calculate_shannon_entropy_bytes(data),
    }
}

/// C-ABI export for Damerau-Levenshtein distance.
#[no_mangle]
pub unsafe extern "C" fn tzero_damerau_levenshtein(
    a_ptr: *const u8,
    a_len: usize,
    b_ptr: *const u8,
    b_len: usize,
) -> usize {
    if a_ptr.is_null() || b_ptr.is_null() {
        return 0;
    }
    let sa = String::from_utf8_lossy(slice::from_raw_parts(a_ptr, a_len));
    let sb = String::from_utf8_lossy(slice::from_raw_parts(b_ptr, b_len));
    damerau_levenshtein_distance(&sa, &sb)
}

/// C-ABI export for fuzzy similarity.
#[no_mangle]
pub unsafe extern "C" fn tzero_fuzzy_similarity_f64(
    a_ptr: *const u8,
    a_len: usize,
    b_ptr: *const u8,
    b_len: usize,
) -> f64 {
    if a_ptr.is_null() || b_ptr.is_null() {
        return 0.0;
    }
    let sa = String::from_utf8_lossy(slice::from_raw_parts(a_ptr, a_len));
    let sb = String::from_utf8_lossy(slice::from_raw_parts(b_ptr, b_len));
    fuzzy_similarity(&sa, &sb)
}

// ==============================================================================
// PyO3 PYTHON MODULE DEFINITION
// ==============================================================================

#[pymodule]
fn tzero_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    python_bindings::register_python_bindings(m)?;
    Ok(())
}
