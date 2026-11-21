// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! High-Performance Local BM25 Hybrid Code Search Engine in Rust.
//! Tokenizes code identifiers (camelCase, snake_case), builds an in-memory inverted index,
//! and scores documents/snippets using Okapi BM25 ($k_1=1.2, b=0.75$) with zero cloud APIs.

use std::collections::{HashMap, HashSet};
use serde::{Deserialize, Serialize};

/// Document entry indexed by the BM25 search engine.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchDocument {
    pub id: String,
    pub path: String,
    pub content: String,
}

/// Scored search result returned to caller.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub id: String,
    pub path: String,
    pub score: f64,
    pub snippet: String,
}

/// Splits camelCase, PascalCase, snake_case, and kebab-case tokens into normalized lowercase terms.
pub fn tokenize_code(text: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut current = String::with_capacity(32);

    let chars: Vec<char> = text.chars().collect();
    let len = chars.len();

    for i in 0..len {
        let c = chars[i];
        if c.is_alphanumeric() {
            if c.is_uppercase() && !current.is_empty() {
                // If previous was lowercase or next is lowercase, split camelCase
                let prev_is_lower = chars.get(i.saturating_sub(1)).map_or(false, |p| p.is_lowercase());
                let next_is_lower = chars.get(i + 1).map_or(false, |n| n.is_lowercase());
                if prev_is_lower || (next_is_lower && current.len() > 1) {
                    tokens.push(current.to_lowercase());
                    current.clear();
                }
            }
            current.push(c);
        } else {
            if !current.is_empty() {
                tokens.push(current.to_lowercase());
                current.clear();
            }
        }
    }

    if !current.is_empty() {
        tokens.push(current.to_lowercase());
    }

    // Filter single char noise except common single-letter variables
    tokens.into_iter().filter(|t| t.len() >= 2).collect()
}

/// In-Memory Okapi BM25 Index.
pub struct Bm25Index {
    pub documents: Vec<SearchDocument>,
    pub doc_lengths: Vec<usize>,
    pub avg_doc_length: f64,
    pub inverted_index: HashMap<String, Vec<(usize, u32)>>, // term -> [(doc_idx, term_freq)]
    pub doc_freq: HashMap<String, usize>,                  // term -> doc_count
    pub k1: f64,
    pub b: f64,
}

impl Bm25Index {
    /// Creates a new BM25 index with default Okapi parameters ($k_1=1.2, b=0.75$).
    pub fn new() -> Self {
        Self {
            documents: Vec::new(),
            doc_lengths: Vec::new(),
            avg_doc_length: 0.0,
            inverted_index: HashMap::new(),
            doc_freq: HashMap::new(),
            k1: 1.2,
            b: 0.75,
        }
    }

    /// Indexes a collection of documents in one pass.
    pub fn index_documents(&mut self, docs: Vec<SearchDocument>) {
        self.documents = docs;
        self.doc_lengths.clear();
        self.inverted_index.clear();
        self.doc_freq.clear();

        let total_docs = self.documents.len();
        if total_docs == 0 {
            self.avg_doc_length = 0.0;
            return;
        }

        let mut total_length: usize = 0;

        for (idx, doc) in self.documents.iter().enumerate() {
            let tokens = tokenize_code(&doc.content);
            let len = tokens.len();
            self.doc_lengths.push(len);
            total_length += len;

            let mut tf_map: HashMap<String, u32> = HashMap::new();
            for t in tokens {
                *tf_map.entry(t).or_insert(0) += 1;
            }

            for (term, freq) in tf_map {
                self.inverted_index.entry(term.clone()).or_default().push((idx, freq));
                *self.doc_freq.entry(term).or_insert(0) += 1;
            }
        }

        self.avg_doc_length = total_length as f64 / total_docs as f64;
    }

    /// Computes Inverse Document Frequency (IDF) with Robertson-Sparck-Jones smoothing.
    pub fn idf(&self, term: &str) -> f64 {
        let n = self.documents.len() as f64;
        let df = self.doc_freq.get(term).copied().unwrap_or(0) as f64;
        if df == 0.0 {
            return 0.0;
        }
        ((n - df + 0.5) / (df + 0.5) + 1.0).ln().max(0.0)
    }

    /// Searches the index with a query and returns top-K ranked results.
    pub fn search(&self, query: &str, top_k: usize) -> Vec<SearchResult> {
        let query_terms = tokenize_code(query);
        if query_terms.is_empty() || self.documents.is_empty() {
            return Vec::new();
        }

        let mut scores: HashMap<usize, f64> = HashMap::new();
        let query_set: HashSet<&String> = query_terms.iter().collect();

        for term in query_set {
            if let Some(postings) = self.inverted_index.get(term) {
                let idf = self.idf(term);
                for &(doc_idx, tf) in postings {
                    let doc_len = self.doc_lengths[doc_idx] as f64;
                    let numerator = (tf as f64) * (self.k1 + 1.0);
                    let denominator = (tf as f64) + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_length));
                    let term_score = idf * (numerator / denominator);
                    *scores.entry(doc_idx).or_insert(0.0) += term_score;
                }
            }
        }

        let mut ranked: Vec<(usize, f64)> = scores.into_iter().collect();
        ranked.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

        let k = top_k.min(ranked.len());
        let mut results = Vec::with_capacity(k);

        for (doc_idx, score) in ranked.into_iter().take(k) {
            let doc = &self.documents[doc_idx];
            let snippet = extract_snippet(&doc.content, &query_terms, 240);
            results.push(SearchResult {
                id: doc.id.clone(),
                path: doc.path.clone(),
                score,
                snippet,
            });
        }

        results
    }
}

/// Extracts a representative contextual snippet around matching query terms.
fn extract_snippet(content: &str, terms: &[String], max_chars: usize) -> String {
    let lower = content.to_lowercase();
    let mut first_match = None;

    for term in terms {
        if let Some(pos) = lower.find(term) {
            first_match = Some(pos);
            break;
        }
    }

    let start = first_match.unwrap_or(0);
    let slice_start = start.saturating_sub(60);
    let slice_end = (slice_start + max_chars).min(content.len());

    let mut snippet = content[slice_start..slice_end].replace('\n', " ");
    if slice_start > 0 {
        snippet = format!("...{}", snippet);
    }
    if slice_end < content.len() {
        snippet = format!("{}...", snippet);
    }
    snippet
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bm25_search_ranking() {
        let mut index = Bm25Index::new();
        index.index_documents(vec![
            SearchDocument {
                id: "1".into(),
                path: "tzero/entropy.py".into(),
                content: "def calculate_shannon_entropy(token): pass".into(),
            },
            SearchDocument {
                id: "2".into(),
                path: "tzero/pruner.py".into(),
                content: "def prune_ast_signatures(tree): pass".into(),
            },
            SearchDocument {
                id: "3".into(),
                path: "tzero/bridge.py".into(),
                content: "class RustCoreBridge: def entropy_scan(self): pass".into(),
            },
        ]);

        let results = index.search("shannon entropy", 2);
        assert!(!results.is_empty());
        assert_eq!(results[0].path, "tzero/entropy.py");
        assert!(results[0].score > 0.0);
    }
}
