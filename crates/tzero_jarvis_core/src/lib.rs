// -*- coding: utf-8 -*-
//! T-Zero Jarvis Autonomous Core Engine (Rust Native)
//! Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
//! Version: 6.0.0

pub mod triplet;
pub mod codebook;
pub mod reinjection;
pub mod causal;
pub mod search;
pub mod lsh;

pub use triplet::{SemanticTriplet, SemanticTripletExtractor, TypedEntity, EntityType};
pub use codebook::VectorQuantizedCodebook;
pub use reinjection::{DynamicVirtualMemoryInjector, CompressionResult};
pub use causal::{CausalTemporalGraph, CausalRelation, CausalEdge, CausalNode};
pub use search::{InvertedSearchEngine, SearchHit, IndexedDoc};
pub use lsh::{RustMinHashLSH, RustMinHashSignature};

use std::collections::HashSet;
use std::slice;

/// Deterministic 64-bit FNV-1a hash matching Python `tzero_rust_bridge`.
pub fn fnv1a_hash64_bytes(bytes: &[u8]) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for &b in bytes {
        h ^= b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}

/// Deterministic byte n-gram Jaccard similarity in `[0.0, 1.0]`.
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
        return if union == 0 { 1.0 } else { ta.intersection(&tb).count() as f64 / union as f64 };
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

/// C-ABI export usable from Python `ctypes` and WASI hosts.
#[no_mangle]
pub unsafe extern "C" fn tzero_fnv1a_hash64(ptr: *const u8, len: usize) -> u64 {
    if ptr.is_null() {
        return 0;
    }
    let data = slice::from_raw_parts(ptr, len);
    fnv1a_hash64_bytes(data)
}

/// C-ABI shingle Jaccard similarity usable from Python `ctypes`.
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
