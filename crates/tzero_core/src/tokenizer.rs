// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! T-Zero High-Performance BPE Tokenizer Module.
//! Integrates `tiktoken-rs` for deterministic, sub-millisecond Byte-Pair Encoding
//! token counting across OpenAI, Anthropic, Gemini, DeepSeek, and open-weight models.

use std::sync::OnceLock;
use tiktoken_rs::CoreBPE;

static O200K_BPE: OnceLock<Option<CoreBPE>> = OnceLock::new();
static CL100K_BPE: OnceLock<Option<CoreBPE>> = OnceLock::new();

fn get_o200k() -> Option<&'static CoreBPE> {
    O200K_BPE.get_or_init(|| tiktoken_rs::o200k_base().ok()).as_ref()
}

fn get_cl100k() -> Option<&'static CoreBPE> {
    CL100K_BPE.get_or_init(|| tiktoken_rs::cl100k_base().ok()).as_ref()
}

/// Resolves the canonical BPE encoding name matching Python `count_bpe_tokens`.
pub fn resolve_encoding_name(model_name: &str) -> &'static str {
    let lower = model_name.to_lowercase();
    if lower.contains("gpt-4o")
        || lower.contains("o1")
        || lower.contains("o3")
        || lower.contains("o4")
        || lower.contains("gpt-5")
        || lower.contains("gemini")
        || lower.contains("deepseek")
    {
        "o200k_base"
    } else if lower.contains("claude")
        || lower.contains("gpt-4")
        || lower.contains("gpt-3.5")
        || lower.contains("llama")
        || lower.contains("mistral")
        || lower.contains("qwen")
    {
        "cl100k_base"
    } else {
        "o200k_base"
    }
}

/// Fast fallback token estimator using standard 4-chars-per-token heuristic.
#[inline]
pub fn fallback_token_estimate(text: &str) -> usize {
    if text.is_empty() {
        0
    } else {
        (text.len() / 4).max(1)
    }
}

/// Counts BPE tokens for the given text using the resolved model encoding.
pub fn count_tokens(text: &str, model_name: &str) -> usize {
    if text.is_empty() {
        return 0;
    }

    let enc_name = resolve_encoding_name(model_name);
    count_tokens_by_encoding(text, enc_name)
}

/// Counts BPE tokens directly given an encoding name ("o200k_base", "cl100k_base", etc.).
pub fn count_tokens_by_encoding(text: &str, encoding: &str) -> usize {
    if text.is_empty() {
        return 0;
    }

    let lower = encoding.to_lowercase();
    if lower.contains("cl100k") {
        if let Some(bpe) = get_cl100k() {
            return bpe.encode_with_special_tokens(text).len().max(1);
        }
    } else {
        if let Some(bpe) = get_o200k() {
            return bpe.encode_with_special_tokens(text).len().max(1);
        }
        if let Some(bpe) = get_cl100k() {
            return bpe.encode_with_special_tokens(text).len().max(1);
        }
    }

    fallback_token_estimate(text)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_string_counts_zero() {
        assert_eq!(count_tokens("", "gpt-4o"), 0);
        assert_eq!(count_tokens("", "claude-3-7-sonnet"), 0);
    }

    #[test]
    fn test_encoding_resolution() {
        assert_eq!(resolve_encoding_name("gpt-4o"), "o200k_base");
        assert_eq!(resolve_encoding_name("o1-preview"), "o200k_base");
        assert_eq!(resolve_encoding_name("claude-3-5-sonnet"), "cl100k_base");
        assert_eq!(resolve_encoding_name("deepseek-r1"), "o200k_base");
        assert_eq!(resolve_encoding_name("gpt-4-turbo"), "cl100k_base");
    }

    #[test]
    fn test_fallback_estimation() {
        let text = "Hello world from T-Zero";
        assert!(fallback_token_estimate(text) > 0);
    }
}
