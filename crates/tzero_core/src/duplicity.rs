// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! High-Performance Code Duplication & Clone Scanner in Rust.
//! Scans files with a sliding window across normalized lines/tokens to detect
//! copy-pasted code blocks (>= 6 lines) with 100% deterministic hashing.

use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use crate::fnv1a_hash64_bytes;

/// Duplicate code block instance.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DuplicateBlock {
    pub file_a: String,
    pub start_line_a: usize,
    pub file_b: String,
    pub start_line_b: usize,
    pub line_count: usize,
    pub snippet: String,
}

/// Overall duplication scan summary.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DuplicityReport {
    pub total_files_scanned: usize,
    pub duplicate_block_count: usize,
    pub total_duplicate_lines: usize,
    pub duplicate_percentage: f64,
    pub blocks: Vec<DuplicateBlock>,
}

/// Scans multiple files for identical code blocks of length >= min_lines (default 6).
pub fn find_code_duplicity(
    files: &[(&str, &str)], // (path, content)
    min_lines: Option<usize>,
) -> DuplicityReport {
    let window_size = min_lines.unwrap_or(6).max(3);
    let mut block_hashes: HashMap<u64, (String, usize, String)> = HashMap::new();
    let mut duplicates = Vec::new();
    let mut total_lines = 0usize;

    for &(path, content) in files {
        let lines: Vec<&str> = content.lines().collect();
        total_lines += lines.len();

        if lines.len() < window_size {
            continue;
        }

        for i in 0..=lines.len() - window_size {
            let window = &lines[i..i + window_size];
            // Normalize: strip leading/trailing whitespace and empty comments
            let normalized: String = window
                .iter()
                .map(|l| l.trim())
                .filter(|l| !l.is_empty() && !l.starts_with('#') && !l.starts_with("//"))
                .collect::<Vec<&str>>()
                .join("\n");

            if normalized.lines().count() < window_size.saturating_sub(1) {
                continue;
            }

            let hash = fnv1a_hash64_bytes(normalized.as_bytes());

            if let Some((prev_path, prev_line, prev_snippet)) = block_hashes.get(&hash) {
                if prev_path != path || (i + 1) != *prev_line {
                    duplicates.push(DuplicateBlock {
                        file_a: prev_path.clone(),
                        start_line_a: *prev_line,
                        file_b: path.to_string(),
                        start_line_b: i + 1,
                        line_count: window_size,
                        snippet: prev_snippet.clone(),
                    });
                }
            } else {
                let snippet = window.join("\n");
                block_hashes.insert(hash, (path.to_string(), i + 1, snippet));
            }
        }
    }

    let dup_lines = duplicates.len() * window_size;
    let percentage = if total_lines > 0 {
        ((dup_lines as f64 / total_lines as f64) * 1000.0).round() / 10.0
    } else {
        0.0
    };

    DuplicityReport {
        total_files_scanned: files.len(),
        duplicate_block_count: duplicates.len(),
        total_duplicate_lines: dup_lines,
        duplicate_percentage: percentage.min(100.0),
        blocks: duplicates,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_duplicate_block_detection() {
        let block = "line_one = 1\nline_two = 2\nline_three = 3\nline_four = 4\nline_five = 5\nline_six = 6\n";
        let file1 = format!("def a():\n{}", block);
        let file2 = format!("def b():\n{}", block);

        let files = vec![("file1.py", file1.as_str()), ("file2.py", file2.as_str())];
        let rep = find_code_duplicity(&files, Some(6));
        assert!(rep.duplicate_block_count >= 1);
        assert_eq!(rep.blocks[0].file_a, "file1.py");
        assert_eq!(rep.blocks[0].file_b, "file2.py");
    }
}
