// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)
// Additional terms under AGPL-3.0 section 7: see NOTICE in the distribution
// or https://github.com/toprakahmetaydogmus/TZeroAlgorithm/blob/main/NOTICE.

// -*- coding: utf-8 -*-
//! T-Zero Turbo Rust Hybrid Core Engine (v12.0.0)
//! Ultra-High Performance Multi-Language AST Pruning, Shannon Entropy Zero-Leak Guard & BPE Tokenizer.
//! Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
//! License: AGPL-3.0-only

pub mod ast_pruner;
pub mod bm25_search;
pub mod entropy_guard;
pub mod python_bindings;
pub mod symbol_graph;
pub mod tokenizer;

pub use ast_pruner::{detect_language, prune_code, prune_code_with_stats, SupportedLanguage};
pub use entropy_guard::{
    calculate_shannon_entropy, calculate_shannon_entropy_bytes, is_placeholder, is_whitelisted,
    redact_entropy_secrets, scan_entropy_secrets, EntropyFinding, MIN_ENTROPY_LENGTH,
    MIN_ENTROPY_THRESHOLD,
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

// ==============================================================================
// PyO3 PYTHON MODULE DEFINITION
// ==============================================================================

#[pymodule]
fn tzero_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    python_bindings::register_python_bindings(m)?;
    Ok(())
}
