// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! PyO3 Native Python Bindings for T-Zero Turbo Rust Core.
//! Exposes tree-sitter AST pruner, Shannon entropy scanner, and BPE tokenizer to Python.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::ast_pruner::{detect_language, prune_code, prune_code_with_stats};
use crate::bm25_search::{Bm25Index, SearchDocument};
use crate::entropy_guard::{
    calculate_shannon_entropy as calc_entropy,
    redact_entropy_secrets as redact_secrets,
    scan_entropy_secrets as scan_secrets,
    MIN_ENTROPY_LENGTH, MIN_ENTROPY_THRESHOLD,
};
use crate::symbol_graph::extract_symbols_from_source;
use crate::tokenizer::count_tokens;
use crate::{fnv1a_hash64_bytes, jaccard_shingles_bytes};

/// Computes the Shannon entropy (bits per symbol) of a given string.
#[pyfunction]
#[pyo3(name = "calculate_shannon_entropy")]
pub fn py_calculate_shannon_entropy(data: &str) -> PyResult<f64> {
    Ok(calc_entropy(data))
}

/// Scans in-memory text for candidate high-entropy secrets ($H \ge 4.75$).
#[pyfunction]
#[pyo3(name = "scan_entropy_secrets", signature = (text, threshold = None, min_length = None))]
pub fn py_scan_entropy_secrets<'py>(
    py: Python<'py>,
    text: &str,
    threshold: Option<f64>,
    min_length: Option<usize>,
) -> PyResult<Bound<'py, PyList>> {
    let t = threshold.unwrap_or(MIN_ENTROPY_THRESHOLD);
    let ml = min_length.unwrap_or(MIN_ENTROPY_LENGTH);
    let findings = scan_secrets(text, Some(t), Some(ml));

    let list = PyList::empty_bound(py);
    for f in findings {
        let dict = PyDict::new_bound(py);
        dict.set_item("token", f.token)?;
        dict.set_item("entropy", f.entropy)?;
        dict.set_item("line", f.line)?;
        dict.set_item("column", f.column)?;
        dict.set_item("is_anomaly", f.is_anomaly)?;
        dict.set_item("rule_id", f.rule_id)?;
        dict.set_item("provider", f.provider)?;
        dict.set_item("description", f.description)?;
        list.append(dict)?;
    }
    Ok(list)
}

/// Redacts candidate high-entropy secrets in text, returning `(redacted_text, count)`.
#[pyfunction]
#[pyo3(name = "redact_entropy_secrets", signature = (text, threshold = None))]
pub fn py_redact_entropy_secrets(text: &str, threshold: Option<f64>) -> PyResult<(String, usize)> {
    Ok(redact_secrets(text, threshold))
}

/// Prunes function and method bodies down to `...` for Python, TypeScript, Rust, and Go.
#[pyfunction]
#[pyo3(name = "prune_ast", signature = (code, language = None))]
pub fn py_prune_ast(code: &str, language: Option<&str>) -> PyResult<String> {
    let lang = detect_language(language.unwrap_or("python"));
    Ok(prune_code(code, lang))
}

/// Prunes AST with detailed metrics (original lines, pruned lines, reduction ratio).
#[pyfunction]
#[pyo3(name = "prune_ast_stats", signature = (code, language = None))]
pub fn py_prune_ast_stats<'py>(
    py: Python<'py>,
    code: &str,
    language: Option<&str>,
) -> PyResult<Bound<'py, PyDict>> {
    let lang = detect_language(language.unwrap_or("python"));
    let res = prune_code_with_stats(code, lang);
    let dict = PyDict::new_bound(py);
    dict.set_item("pruned_code", res.pruned_code)?;
    dict.set_item("original_lines", res.original_lines)?;
    dict.set_item("pruned_lines", res.pruned_lines)?;
    dict.set_item("reduction_ratio", res.reduction_ratio)?;
    dict.set_item("language", format!("{:?}", res.language))?;
    Ok(dict)
}

/// Counts BPE tokens using cached local tiktoken encodings (o200k_base / cl100k_base).
#[pyfunction]
#[pyo3(name = "count_bpe_tokens", signature = (text, model_name = None))]
pub fn py_count_bpe_tokens(text: &str, model_name: Option<&str>) -> PyResult<usize> {
    let model = model_name.unwrap_or("gpt-4o");
    Ok(count_tokens(text, model))
}

/// Deterministic 64-bit FNV-1a hash matching Python `RustCoreBridge.fnv1a_hash`.
#[pyfunction]
#[pyo3(name = "fnv1a_hash")]
pub fn py_fnv1a_hash(text: &str) -> PyResult<u64> {
    Ok(fnv1a_hash64_bytes(text.as_bytes()))
}

/// Deterministic byte n-gram Jaccard similarity in [0.0, 1.0].
#[pyfunction]
#[pyo3(name = "shingle_similarity", signature = (a, b, ngram = None))]
pub fn py_shingle_similarity(a: &str, b: &str, ngram: Option<usize>) -> PyResult<f64> {
    let n = ngram.unwrap_or(3);
    Ok(jaccard_shingles_bytes(a.as_bytes(), b.as_bytes(), n))
}

/// Performs ultra-fast local BM25 hybrid search across documents without cloud APIs.
#[pyfunction]
#[pyo3(name = "bm25_search", signature = (documents, query, top_k = None))]
pub fn py_bm25_search<'py>(
    py: Python<'py>,
    documents: Bound<'py, PyList>,
    query: &str,
    top_k: Option<usize>,
) -> PyResult<Bound<'py, PyList>> {
    let mut docs = Vec::with_capacity(documents.len());
    for item in documents.iter() {
        if let Ok(dict) = item.downcast::<PyDict>() {
            let id = dict.get_item("id")?.map(|v| v.extract::<String>()).transpose()?.unwrap_or_default();
            let path = dict.get_item("path")?.map(|v| v.extract::<String>()).transpose()?.unwrap_or_default();
            let content = dict.get_item("content")?.map(|v| v.extract::<String>()).transpose()?.unwrap_or_default();
            docs.push(SearchDocument { id, path, content });
        }
    }

    let mut index = Bm25Index::new();
    index.index_documents(docs);
    let results = index.search(query, top_k.unwrap_or(10));

    let py_list = PyList::empty_bound(py);
    for r in results {
        let dict = PyDict::new_bound(py);
        dict.set_item("id", r.id)?;
        dict.set_item("path", r.path)?;
        dict.set_item("score", r.score)?;
        dict.set_item("snippet", r.snippet)?;
        py_list.append(dict)?;
    }
    Ok(py_list)
}

/// Extracts symbols and dependency edges from source code in native Rust.
#[pyfunction]
#[pyo3(name = "extract_symbols", signature = (path, content))]
pub fn py_extract_symbols<'py>(
    py: Python<'py>,
    path: &str,
    content: &str,
) -> PyResult<Bound<'py, PyDict>> {
    let (symbols, edges) = extract_symbols_from_source(path, content);
    let out_dict = PyDict::new_bound(py);

    let py_symbols = PyList::empty_bound(py);
    for s in symbols {
        let d = PyDict::new_bound(py);
        d.set_item("name", s.name)?;
        d.set_item("kind", s.kind)?;
        d.set_item("line", s.line)?;
        d.set_item("path", s.path)?;
        d.set_item("signature", s.signature)?;
        py_symbols.append(d)?;
    }

    let py_edges = PyList::empty_bound(py);
    for e in edges {
        let d = PyDict::new_bound(py);
        d.set_item("source", e.source)?;
        d.set_item("target", e.target)?;
        d.set_item("kind", e.kind)?;
        py_edges.append(d)?;
    }

    out_dict.set_item("symbols", py_symbols)?;
    out_dict.set_item("edges", py_edges)?;
    Ok(out_dict)
}

/// Returns True when running within native Rust compiled extension module.
#[pyfunction]
#[pyo3(name = "is_native")]
pub fn py_is_native() -> PyResult<bool> {
    Ok(true)
}

/// Returns the native Rust core version string.
#[pyfunction]
#[pyo3(name = "core_version")]
pub fn py_core_version() -> PyResult<&'static str> {
    Ok("12.0.0")
}

/// Registers all Python functions onto the target PyModule bound handle.
pub fn register_python_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(py_calculate_shannon_entropy, m)?)?;
    m.add_function(wrap_pyfunction!(py_scan_entropy_secrets, m)?)?;
    m.add_function(wrap_pyfunction!(py_redact_entropy_secrets, m)?)?;
    m.add_function(wrap_pyfunction!(py_prune_ast, m)?)?;
    m.add_function(wrap_pyfunction!(py_prune_ast_stats, m)?)?;
    m.add_function(wrap_pyfunction!(py_count_bpe_tokens, m)?)?;
    m.add_function(wrap_pyfunction!(py_fnv1a_hash, m)?)?;
    m.add_function(wrap_pyfunction!(py_shingle_similarity, m)?)?;
    m.add_function(wrap_pyfunction!(py_bm25_search, m)?)?;
    m.add_function(wrap_pyfunction!(py_extract_symbols, m)?)?;
    m.add_function(wrap_pyfunction!(py_is_native, m)?)?;
    m.add_function(wrap_pyfunction!(py_core_version, m)?)?;
    m.add("__version__", "12.0.0")?;
    m.add("__doc__", "T-Zero Turbo Rust Hybrid Core Native Extension Module")?;
    Ok(())
}
