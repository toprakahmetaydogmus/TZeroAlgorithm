// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! T-Zero Turbo Rust Native CLI (`tzero-core`).
//! Standalone high-performance binary for deterministic AST pruning, Shannon entropy auditing,
//! cyclomatic complexity computation, API contract guarding, context tree generation,
//! architectural boundaries enforcement, and native stdio MCP server daemon.

use std::env;
use std::fs;
use std::process;

use tzero_core::ast_pruner::{detect_language, prune_code_with_stats};
use tzero_core::boundary_guard::enforce_boundaries;
use tzero_core::complexity::analyze_file_complexity;
use tzero_core::context_tree::build_context_tree;
use tzero_core::contracts::compare_api_contracts;
use tzero_core::duplicity::find_code_duplicity;
use tzero_core::entropy_guard::scan_entropy_secrets;
use tzero_core::hallucination_guard::verify_hallucinations;
use tzero_core::mcp_server::run_mcp_stdio_server;
use tzero_core::token_cost::compare_all_models;

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
    tree <dir> [tier]                Generates multi-tier AST context tree (T-1 to T-4)
    guard <edges_json>               Enforces architectural boundary layers and circular imports
    hallucination <file> <syms_csv>  Validates code against symbol map to stop hallucinations
    cost <raw_tok> <pruned_tok>      Calculates multi-model API costs and team financial ROI
    mcp                              Runs embedded native stdio JSON-RPC 2.0 MCP server
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
            println!("Features: AST-Pruning, Shannon-Entropy, BM25, PageRank, Complexity, Contracts, Duplicity, Context-Tree, Boundary-Guard, MCP");
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
        "tree" => {
            let dir_path = if args.len() > 2 { &args[2] } else { "." };
            let tier: u32 = if args.len() > 3 {
                args[3].parse().unwrap_or(3)
            } else {
                3
            };
            let result = build_context_tree(dir_path, tier, None);
            println!("{}", result.formatted_tree);
        }
        "guard" => {
            if args.len() < 3 {
                eprintln!("Error: 'guard' requires an edges json file or 'source:target' pair.");
                process::exit(1);
            }
            let target = &args[2];
            let mut edges = Vec::new();
            let storage: Vec<(String, String)>;

            if let Ok(json_content) = fs::read_to_string(target) {
                if let Ok(parsed) = serde_json::from_str::<Vec<(String, String)>>(&json_content) {
                    storage = parsed;
                    for (s, d) in &storage {
                        edges.push((s.as_str(), d.as_str()));
                    }
                }
            } else if target.contains(':') {
                let parts: Vec<&str> = target.split(':').collect();
                if parts.len() == 2 {
                    edges.push((parts[0], parts[1]));
                }
            }
            let report = enforce_boundaries(&edges, None);
            println!("{}", serde_json::to_string_pretty(&report).unwrap());
        }
        "hallucination" => {
            if args.len() < 4 {
                eprintln!("Error: 'hallucination' requires <code_file> <valid_symbols_csv>.");
                process::exit(1);
            }
            let code = fs::read_to_string(&args[2]).unwrap_or_default();
            let symbols_csv = &args[3];
            let symbols: Vec<&str> = symbols_csv.split(',').map(|s| s.trim()).filter(|s| !s.is_empty()).collect();
            let report = verify_hallucinations(&code, &symbols);
            println!("{}", serde_json::to_string_pretty(&report).unwrap());
        }
        "cost" => {
            if args.len() < 4 {
                eprintln!("Error: 'cost' requires <raw_tokens> <pruned_tokens> [output_tokens] [model].");
                process::exit(1);
            }
            let raw: usize = args[2].parse().unwrap_or(100_000);
            let pruned: usize = args[3].parse().unwrap_or(10_000);
            let out: usize = if args.len() > 4 { args[4].parse().unwrap_or(2_000) } else { 2_000 };
            let model = if args.len() > 5 { Some(args[5].as_str()) } else { Some("gpt-4o") };
            let report = compare_all_models(raw, pruned, out, model);
            println!("{}", serde_json::to_string_pretty(&report).unwrap());
        }
        "mcp" => {
            if let Err(e) = run_mcp_stdio_server() {
                eprintln!("MCP server stopped with error: {}", e);
                process::exit(1);
            }
        }
        _ => {
            print_usage();
            process::exit(1);
        }
    }
}
