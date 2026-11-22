// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! T-Zero Turbo Rust Native CLI (`tzero-core`).
//! Standalone high-performance binary for deterministic AST pruning, Shannon entropy auditing,
//! cyclomatic complexity computation, API contract guarding, and BM25 local code search.

use std::env;
use std::fs;
use std::path::Path;
use std::process;

use tzero_core::ast_pruner::{detect_language, prune_code_with_stats};
use tzero_core::complexity::analyze_file_complexity;
use tzero_core::contracts::compare_api_contracts;
use tzero_core::duplicity::find_code_duplicity;
use tzero_core::entropy_guard::scan_entropy_secrets;

fn print_usage() {
    println!(r#"
T-Zero Turbo Rust Hybrid Core CLI (v12.1.4)
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: AGPL-3.0-only

USAGE:
    tzero-core <SUBCOMMAND> [OPTIONS]

SUBCOMMANDS:
    prune <file>                     Prunes AST to signatures/stubs with token metrics
    audit <file>                     Zero-Leak Shannon entropy security audit (H >= 4.75)
    complexity <file>                Computes cyclomatic, cognitive complexity & MI rating
    contracts <old_file> <new_file>  Compares API signatures and recommends SemVer bump
    duplicity <file1> <file2>...     Finds duplicate code blocks (>= 6 lines)
    version                          Prints engine version and build metadata
"#);
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        print_usage();
        process::exit(1);
    }

    match args[1].as_str() {
        "version" | "--version" | "-v" => {
            println!("tzero-core v12.1.4 (x86_64 native AGPL-3.0)");
            println!("Features: AST-Pruning, Shannon-Entropy, BM25, PageRank, Complexity, Contracts, Duplicity");
        }
        "prune" => {
            if args.len() < 3 {
                eprintln!("Error: 'prune' requires a file path.");
                process::exit(1);
            }
            let file_path = &args[2];
            let content = fs::read_to_string(file_path).unwrap_or_else(|e| {
                eprintln!("Failed to read file {}: {}", file_path, e);
                process::exit(1);
            });
            let lang = detect_language(file_path);
            let stats = prune_code_with_stats(&content, lang);
            println!("{}", serde_json::to_string_pretty(&stats).unwrap());
        }
        "audit" => {
            if args.len() < 3 {
                eprintln!("Error: 'audit' requires a file path.");
                process::exit(1);
            }
            let file_path = &args[2];
            let content = fs::read_to_string(file_path).unwrap_or_else(|e| {
                eprintln!("Failed to read file {}: {}", file_path, e);
                process::exit(1);
            });
            let findings = scan_entropy_secrets(&content, None, None);
            println!("{}", serde_json::to_string_pretty(&findings).unwrap());
        }
        "complexity" => {
            if args.len() < 3 {
                eprintln!("Error: 'complexity' requires a file path.");
                process::exit(1);
            }
            let file_path = &args[2];
            let content = fs::read_to_string(file_path).unwrap_or_else(|e| {
                eprintln!("Failed to read file {}: {}", file_path, e);
                process::exit(1);
            });
            let lang = detect_language(file_path);
            let report = analyze_file_complexity(file_path, &content, lang);
            println!("{}", serde_json::to_string_pretty(&report).unwrap());
        }
        "contracts" => {
            if args.len() < 4 {
                eprintln!("Error: 'contracts' requires <old_file> and <new_file>.");
                process::exit(1);
            }
            let old_code = fs::read_to_string(&args[2]).unwrap_or_default();
            let new_code = fs::read_to_string(&args[3]).unwrap_or_default();
            let report = compare_api_contracts(&old_code, &new_code);
            println!("{}", serde_json::to_string_pretty(&report).unwrap());
        }
        "duplicity" => {
            if args.len() < 4 {
                eprintln!("Error: 'duplicity' requires at least 2 file paths.");
                process::exit(1);
            }
            let mut file_contents = Vec::new();
            for path_str in &args[2..] {
                if let Ok(content) = fs::read_to_string(path_str) {
                    file_contents.push((path_str.as_str(), content));
                }
            }
            let files_ref: Vec<(&str, &str)> = file_contents.iter().map(|(p, c)| (*p, c.as_str())).collect();
            let report = find_code_duplicity(&files_ref, Some(6));
            println!("{}", serde_json::to_string_pretty(&report).unwrap());
        }
        _ => {
            print_usage();
            process::exit(1);
        }
    }
}
