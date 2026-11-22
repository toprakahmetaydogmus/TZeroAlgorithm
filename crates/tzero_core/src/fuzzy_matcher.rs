// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! Ultra-Fast Damerau-Levenshtein Fuzzy Matcher & String Distance in Rust.
//! Computes string distance and similarity metrics with transposition handling
//! for symbol typo correction, fuzzy patching, and AST alignment.

use serde::{Deserialize, Serialize};

/// Fuzzy match candidate.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FuzzyMatch {
    pub target: String,
    pub distance: usize,
    pub similarity: f64,
}

/// Computes Damerau-Levenshtein distance with adjacent transposition support.
pub fn damerau_levenshtein_distance(s1: &str, s2: &str) -> usize {
    let a: Vec<char> = s1.chars().collect();
    let b: Vec<char> = s2.chars().collect();

    let len_a = a.len();
    let len_b = b.len();

    if len_a == 0 {
        return len_b;
    }
    if len_b == 0 {
        return len_a;
    }

    let mut d = vec![vec![0usize; len_b + 1]; len_a + 1];

    for i in 0..=len_a {
        d[i][0] = i;
    }
    for j in 0..=len_b {
        d[0][j] = j;
    }

    for i in 1..=len_a {
        for j in 1..=len_b {
            let cost = if a[i - 1] == b[j - 1] { 0 } else { 1 };

            d[i][j] = (d[i - 1][j] + 1)                  // deletion
                .min(d[i][j - 1] + 1)                    // insertion
                .min(d[i - 1][j - 1] + cost);            // substitution

            // Transposition check
            if i > 1 && j > 1 && a[i - 1] == b[j - 2] && a[i - 2] == b[j - 1] {
                d[i][j] = d[i][j].min(d[i - 2][j - 2] + 1);
            }
        }
    }

    d[len_a][len_b]
}

/// Calculates normalized similarity ratio in range [0.0, 1.0].
pub fn fuzzy_similarity(s1: &str, s2: &str) -> f64 {
    let max_len = s1.chars().count().max(s2.chars().count());
    if max_len == 0 {
        return 1.0;
    }
    let dist = damerau_levenshtein_distance(s1, s2);
    let sim = 1.0 - (dist as f64 / max_len as f64);
    (sim.clamp(0.0, 1.0) * 1000.0).round() / 1000.0
}

/// Searches a list of candidates and returns matches above threshold, sorted by similarity.
pub fn fuzzy_symbol_search(
    query: &str,
    candidates: &[&str],
    min_similarity: Option<f64>,
    top_k: Option<usize>,
) -> Vec<FuzzyMatch> {
    let threshold = min_similarity.unwrap_or(0.6);
    let limit = top_k.unwrap_or(5);

    let mut matches = Vec::new();

    for &cand in candidates {
        let dist = damerau_levenshtein_distance(query, cand);
        let sim = fuzzy_similarity(query, cand);
        if sim >= threshold {
            matches.push(FuzzyMatch {
                target: cand.to_string(),
                distance: dist,
                similarity: sim,
            });
        }
    }

    matches.sort_by(|a, b| b.similarity.partial_cmp(&a.similarity).unwrap_or(std::cmp::Ordering::Equal));
    matches.truncate(limit);
    matches
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_damerau_levenshtein() {
        assert_eq!(damerau_levenshtein_distance("teh", "the"), 1);
        // Transposition
        assert_eq!(damerau_levenshtein_distance("recieve", "receive"), 1);
        let sim = fuzzy_similarity("OrderController", "OrderControler");
        assert!(sim > 0.9);
    }
}
