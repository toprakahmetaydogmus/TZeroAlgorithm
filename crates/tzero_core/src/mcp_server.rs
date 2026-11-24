// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! T-Zero Native JSON-RPC 2.0 Model Context Protocol (MCP) Server.
//! Embedded lightweight stdio MCP daemon exposing all AST context engineering,
//! Shannon entropy zero-leak auditing, and code complexity tools natively without Python.

use std::io::{self, BufRead, Write};
use serde_json::{json, Value};

use crate::ast_pruner::{detect_language, prune_code_with_stats};
use crate::bm25_search::{Bm25Index, SearchDocument};
use crate::boundary_guard::enforce_boundaries;
use crate::complexity::analyze_file_complexity;
use crate::context_tree::build_context_tree;
use crate::contracts::compare_api_contracts;
use crate::duplicity::find_code_duplicity;
use crate::entropy_guard::scan_entropy_secrets;
use crate::hallucination_guard::verify_hallucinations;
use crate::pagerank::compute_pagerank;
use crate::symbol_graph::DependencyEdge;
use crate::token_cost::compare_all_models;

pub fn run_mcp_stdio_server() -> io::Result<()> {
    let stdin = io::stdin();
    let mut stdout = io::stdout();

    for line in stdin.lock().lines() {
        let line = match line {
            Ok(l) => l,
            Err(_) => break,
        };
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }

        let parsed: Value = match serde_json::from_str(trimmed) {
            Ok(v) => v,
            Err(_) => continue,
        };

        let id = parsed.get("id").cloned();
        let method = parsed.get("method").and_then(|m| m.as_str()).unwrap_or("");
        let params = parsed.get("params").cloned().unwrap_or(Value::Null);

        let response = match method {
            "initialize" => {
                json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {
                            "name": "tzero-core-mcp",
                            "version": env!("CARGO_PKG_VERSION")
                        },
                        "capabilities": {
                            "tools": {}
                        }
                    }
                })
            }
            "ping" => {
                json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {}
                })
            }
            "tools/list" => {
                json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "tools": [
                            {
                                "name": "tzero_prune",
                                "description": "Prunes AST bodies down to signatures delivering up to 95% token savings",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "code": {"type": "string"},
                                        "language": {"type": "string"}
                                    },
                                    "required": ["code"]
                                }
                            },
                            {
                                "name": "tzero_audit",
                                "description": "100% Zero-Leak Shannon entropy security scanner for API tokens and secrets",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"}
                                    },
                                    "required": ["text"]
                                }
                            },
                            {
                                "name": "tzero_complexity",
                                "description": "Calculates AST cyclomatic, cognitive complexity, and Maintainability Index",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "file_path": {"type": "string"},
                                        "content": {"type": "string"}
                                    },
                                    "required": ["file_path", "content"]
                                }
                            },
                            {
                                "name": "tzero_tree",
                                "description": "Builds multi-tier hierarchical AST context tree (T-1 to T-4) from target directory",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "root_dir": {"type": "string"},
                                        "tier": {"type": "integer"}
                                    },
                                    "required": ["root_dir"]
                                }
                            },
                            {
                                "name": "tzero_cost",
                                "description": "Estimates exact token API dollar costs and team ROI savings across models",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "raw_input_tokens": {"type": "integer"},
                                        "pruned_input_tokens": {"type": "integer"},
                                        "output_tokens": {"type": "integer"}
                                    },
                                    "required": ["raw_input_tokens", "pruned_input_tokens"]
                                }
                            },
                            {
                                "name": "tzero_hallucination_guard",
                                "description": "Eliminates AI coding hallucinations by checking code against valid workspace symbols",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "code": {"type": "string"},
                                        "valid_symbols": {"type": "array", "items": {"type": "string"}}
                                    },
                                    "required": ["code", "valid_symbols"]
                                }
                            },
                            {
                                "name": "tzero_guard",
                                "description": "Enforces architectural boundary rules and identifies cyclic module dependencies",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "edges": {
                                            "type": "array",
                                            "items": {"type": "array", "items": {"type": "string"}}
                                        }
                                    },
                                    "required": ["edges"]
                                }
                            },
                            {
                                "name": "tzero_contracts",
                                "description": "Compares API symbol contracts between versions and suggests SemVer bump",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "old_code": {"type": "string"},
                                        "new_code": {"type": "string"}
                                    },
                                    "required": ["old_code", "new_code"]
                                }
                            },
                            {
                                "name": "tzero_duplicity",
                                "description": "Detects duplicate code blocks across files using rolling window hashing",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "files": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "path": {"type": "string"},
                                                    "content": {"type": "string"}
                                                },
                                                "required": ["path", "content"]
                                            }
                                        },
                                        "min_lines": {"type": "integer"}
                                    },
                                    "required": ["files"]
                                }
                            },
                            {
                                "name": "tzero_pagerank",
                                "description": "Computes PageRank architectural backbone centrality scores over dependency edges",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "edges": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "source": {"type": "string"},
                                                    "target": {"type": "string"},
                                                    "kind": {"type": "string"}
                                                },
                                                "required": ["source", "target"]
                                            }
                                        }
                                    },
                                    "required": ["edges"]
                                }
                            },
                            {
                                "name": "tzero_search",
                                "description": "100% private local Okapi BM25 hybrid semantic search across code snippets",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {"type": "string"},
                                        "documents": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "string"},
                                                    "path": {"type": "string"},
                                                    "content": {"type": "string"}
                                                },
                                                "required": ["id", "path", "content"]
                                            }
                                        },
                                        "top_k": {"type": "integer"}
                                    },
                                    "required": ["query", "documents"]
                                }
                            }
                        ]
                    }
                })
            }
            "tools/call" => {
                let tool_name = params.get("name").and_then(|n| n.as_str()).unwrap_or("");
                let args = params.get("arguments").cloned().unwrap_or(Value::Null);

                let result_text = match tool_name {
                    "tzero_prune" => {
                        let code = args.get("code").and_then(|c| c.as_str()).unwrap_or("");
                        let lang_str = args.get("language").and_then(|l| l.as_str()).unwrap_or("python");
                        let lang = detect_language(lang_str);
                        let stats = prune_code_with_stats(code, lang);
                        serde_json::to_string_pretty(&stats).unwrap_or_default()
                    }
                    "tzero_audit" => {
                        let text = args.get("text").and_then(|t| t.as_str()).unwrap_or("");
                        let findings = scan_entropy_secrets(text, None, None);
                        serde_json::to_string_pretty(&findings).unwrap_or_default()
                    }
                    "tzero_complexity" => {
                        let path = args.get("file_path").and_then(|p| p.as_str()).unwrap_or("snippet.py");
                        let content = args.get("content").and_then(|c| c.as_str()).unwrap_or("");
                        let lang = detect_language(path);
                        let rep = analyze_file_complexity(path, content, lang);
                        serde_json::to_string_pretty(&rep).unwrap_or_default()
                    }
                    "tzero_tree" => {
                        let root = args.get("root_dir").and_then(|r| r.as_str()).unwrap_or(".");
                        let tier = args.get("tier").and_then(|t| t.as_u64()).unwrap_or(3) as u32;
                        let tree = build_context_tree(root, tier, None);
                        serde_json::to_string_pretty(&tree).unwrap_or_default()
                    }
                    "tzero_cost" => {
                        let raw = args.get("raw_input_tokens").and_then(|r| r.as_u64()).unwrap_or(100_000) as usize;
                        let pruned = args.get("pruned_input_tokens").and_then(|p| p.as_u64()).unwrap_or(10_000) as usize;
                        let out = args.get("output_tokens").and_then(|o| o.as_u64()).unwrap_or(2_000) as usize;
                        let rep = compare_all_models(raw, pruned, out, Some("gpt-4o"));
                        serde_json::to_string_pretty(&rep).unwrap_or_default()
                    }
                    "tzero_hallucination_guard" => {
                        let code = args.get("code").and_then(|c| c.as_str()).unwrap_or("");
                        let empty_vec = Vec::new();
                        let symbols_val = args.get("valid_symbols").and_then(|s| s.as_array()).unwrap_or(&empty_vec);
                        let symbols: Vec<&str> = symbols_val.iter().filter_map(|v| v.as_str()).collect();
                        let rep = verify_hallucinations(code, &symbols);
                        serde_json::to_string_pretty(&rep).unwrap_or_default()
                    }
                    "tzero_guard" => {
                        let empty_edges = Vec::new();
                        let edges_arr = args.get("edges").and_then(|e| e.as_array()).unwrap_or(&empty_edges);
                        let mut string_pairs = Vec::new();
                        for item in edges_arr {
                            if let Some(pair) = item.as_array() {
                                if pair.len() >= 2 {
                                    if let (Some(s), Some(d)) = (pair[0].as_str(), pair[1].as_str()) {
                                        string_pairs.push((s.to_string(), d.to_string()));
                                    }
                                }
                            }
                        }
                        let edges_ref: Vec<(&str, &str)> = string_pairs.iter().map(|(s, d)| (s.as_str(), d.as_str())).collect();
                        let rep = enforce_boundaries(&edges_ref, None);
                        serde_json::to_string_pretty(&rep).unwrap_or_default()
                    }
                    "tzero_contracts" => {
                        let old_code = args.get("old_code").and_then(|c| c.as_str()).unwrap_or("");
                        let new_code = args.get("new_code").and_then(|c| c.as_str()).unwrap_or("");
                        let rep = compare_api_contracts(old_code, new_code);
                        serde_json::to_string_pretty(&rep).unwrap_or_default()
                    }
                    "tzero_duplicity" => {
                        let empty_files = Vec::new();
                        let files_arr = args.get("files").and_then(|f| f.as_array()).unwrap_or(&empty_files);
                        let min_lines = args.get("min_lines").and_then(|m| m.as_u64()).map(|m| m as usize);
                        let mut file_data: Vec<(String, String)> = Vec::new();
                        for item in files_arr {
                            let path = item.get("path").and_then(|p| p.as_str()).unwrap_or("file");
                            let content = item.get("content").and_then(|c| c.as_str()).unwrap_or("");
                            file_data.push((path.to_string(), content.to_string()));
                        }
                        let file_refs: Vec<(&str, &str)> = file_data.iter().map(|(p, c)| (p.as_str(), c.as_str())).collect();
                        let rep = find_code_duplicity(&file_refs, min_lines);
                        serde_json::to_string_pretty(&rep).unwrap_or_default()
                    }
                    "tzero_pagerank" => {
                        let empty_edges = Vec::new();
                        let edges_arr = args.get("edges").and_then(|e| e.as_array()).unwrap_or(&empty_edges);
                        let mut dep_edges = Vec::new();
                        for item in edges_arr {
                            let src = item.get("source").and_then(|s| s.as_str()).unwrap_or("");
                            let tgt = item.get("target").and_then(|t| t.as_str()).unwrap_or("");
                            let knd = item.get("kind").and_then(|k| k.as_str()).unwrap_or("import");
                            if !src.is_empty() && !tgt.is_empty() {
                                dep_edges.push(DependencyEdge {
                                    source: src.to_string(),
                                    target: tgt.to_string(),
                                    kind: knd.to_string(),
                                });
                            }
                        }
                        let ranks = compute_pagerank(&dep_edges, None, None, None);
                        serde_json::to_string_pretty(&ranks).unwrap_or_default()
                    }
                    "tzero_search" => {
                        let query = args.get("query").and_then(|q| q.as_str()).unwrap_or("");
                        let empty_docs = Vec::new();
                        let docs_arr = args.get("documents").and_then(|d| d.as_array()).unwrap_or(&empty_docs);
                        let top_k = args.get("top_k").and_then(|k| k.as_u64()).unwrap_or(5) as usize;
                        let mut docs = Vec::new();
                        for item in docs_arr {
                            let id = item.get("id").and_then(|i| i.as_str()).unwrap_or("");
                            let path = item.get("path").and_then(|p| p.as_str()).unwrap_or("");
                            let content = item.get("content").and_then(|c| c.as_str()).unwrap_or("");
                            docs.push(SearchDocument {
                                id: id.to_string(),
                                path: path.to_string(),
                                content: content.to_string(),
                            });
                        }
                        let mut index = Bm25Index::new();
                        index.index_documents(docs);
                        let results = index.search(query, top_k);
                        serde_json::to_string_pretty(&results).unwrap_or_default()
                    }
                    _ => {
                        format!("Unknown tool: {}", tool_name)
                    }
                };

                json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result_text
                            }
                        ]
                    }
                })
            }
            _ => {
                json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "error": {
                        "code": -32601,
                        "message": format!("Method not found: {}", method)
                    }
                })
            }
        };

        writeln!(stdout, "{}", serde_json::to_string(&response).unwrap())?;
        stdout.flush()?;
    }

    Ok(())
}
