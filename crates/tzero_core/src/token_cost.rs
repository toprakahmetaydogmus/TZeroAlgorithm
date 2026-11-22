// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş (Siber Akademi)

//! T-Zero Token Cost & Multi-Model Financial ROI Engine.
//! Computes exact API dollar costs and team ROI savings across OpenAI,
//! Anthropic, Google Gemini, and DeepSeek model architectures.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelPricing {
    pub model_id: String,
    pub provider: String,
    pub input_cost_per_m: f64,
    pub output_cost_per_m: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenCostEstimate {
    pub model_id: String,
    pub provider: String,
    pub input_tokens: usize,
    pub output_tokens: usize,
    pub total_tokens: usize,
    pub input_cost_usd: f64,
    pub output_cost_usd: f64,
    pub total_cost_usd: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelComparisonReport {
    pub input_tokens: usize,
    pub output_tokens: usize,
    pub pruned_input_tokens: usize,
    pub baseline_model: String,
    pub baseline_cost_usd: f64,
    pub optimized_cost_usd: f64,
    pub cost_savings_usd: f64,
    pub cost_reduction_percent: f64,
    pub monthly_projected_savings_usd: f64,
    pub models: Vec<TokenCostEstimate>,
}

pub fn get_standard_pricing() -> Vec<ModelPricing> {
    vec![
        ModelPricing { model_id: "gpt-4o".to_string(), provider: "OpenAI".to_string(), input_cost_per_m: 2.50, output_cost_per_m: 10.00 },
        ModelPricing { model_id: "gpt-4o-mini".to_string(), provider: "OpenAI".to_string(), input_cost_per_m: 0.15, output_cost_per_m: 0.60 },
        ModelPricing { model_id: "o3-mini".to_string(), provider: "OpenAI".to_string(), input_cost_per_m: 1.10, output_cost_per_m: 4.40 },
        ModelPricing { model_id: "claude-3-5-sonnet".to_string(), provider: "Anthropic".to_string(), input_cost_per_m: 3.00, output_cost_per_m: 15.00 },
        ModelPricing { model_id: "claude-3-5-haiku".to_string(), provider: "Anthropic".to_string(), input_cost_per_m: 0.80, output_cost_per_m: 4.00 },
        ModelPricing { model_id: "gemini-1-5-pro".to_string(), provider: "Google".to_string(), input_cost_per_m: 1.25, output_cost_per_m: 5.00 },
        ModelPricing { model_id: "gemini-1-5-flash".to_string(), provider: "Google".to_string(), input_cost_per_m: 0.075, output_cost_per_m: 0.30 },
        ModelPricing { model_id: "gemini-2-0-flash".to_string(), provider: "Google".to_string(), input_cost_per_m: 0.10, output_cost_per_m: 0.40 },
        ModelPricing { model_id: "deepseek-v3".to_string(), provider: "DeepSeek".to_string(), input_cost_per_m: 0.14, output_cost_per_m: 0.28 },
        ModelPricing { model_id: "deepseek-r1".to_string(), provider: "DeepSeek".to_string(), input_cost_per_m: 0.55, output_cost_per_m: 2.19 },
    ]
}

pub fn estimate_cost_for_model(
    input_tokens: usize,
    output_tokens: usize,
    pricing: &ModelPricing,
) -> TokenCostEstimate {
    let in_cost = (input_tokens as f64 / 1_000_000.0) * pricing.input_cost_per_m;
    let out_cost = (output_tokens as f64 / 1_000_000.0) * pricing.output_cost_per_m;
    let total = in_cost + out_cost;

    TokenCostEstimate {
        model_id: pricing.model_id.clone(),
        provider: pricing.provider.clone(),
        input_tokens,
        output_tokens,
        total_tokens: input_tokens + output_tokens,
        input_cost_usd: (in_cost * 100_000.0).round() / 100_000.0,
        output_cost_usd: (out_cost * 100_000.0).round() / 100_000.0,
        total_cost_usd: (total * 100_000.0).round() / 100_000.0,
    }
}

pub fn compare_all_models(
    raw_input_tokens: usize,
    pruned_input_tokens: usize,
    output_tokens: usize,
    baseline_model_id: Option<&str>,
) -> ModelComparisonReport {
    let prices = get_standard_pricing();
    let mut estimates = Vec::new();

    let target_model = baseline_model_id.unwrap_or("gpt-4o");
    let mut baseline_cost = 0.0;
    let mut optimized_cost = 0.0;

    for p in &prices {
        let est = estimate_cost_for_model(raw_input_tokens, output_tokens, p);
        if p.model_id == target_model {
            baseline_cost = est.total_cost_usd;
            let opt_est = estimate_cost_for_model(pruned_input_tokens, output_tokens, p);
            optimized_cost = opt_est.total_cost_usd;
        }
        estimates.push(est);
    }

    let savings = (baseline_cost - optimized_cost).max(0.0);
    let reduction_percent = if baseline_cost > 0.0 {
        (savings / baseline_cost) * 100.0
    } else {
        0.0
    };

    // Assume typical active engineering team generates 20,000 LLM calls per month
    let monthly_projected = savings * 20_000.0;

    ModelComparisonReport {
        input_tokens: raw_input_tokens,
        output_tokens,
        pruned_input_tokens,
        baseline_model: target_model.to_string(),
        baseline_cost_usd: (baseline_cost * 100_000.0).round() / 100_000.0,
        optimized_cost_usd: (optimized_cost * 100_000.0).round() / 100_000.0,
        cost_savings_usd: (savings * 100_000.0).round() / 100_000.0,
        cost_reduction_percent: (reduction_percent * 10.0).round() / 10.0,
        monthly_projected_savings_usd: (monthly_projected * 100.0).round() / 100.0,
        models: estimates,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_gpt4o_cost_calculation() {
        let pricing = ModelPricing {
            model_id: "gpt-4o".to_string(),
            provider: "OpenAI".to_string(),
            input_cost_per_m: 2.50,
            output_cost_per_m: 10.00,
        };
        let est = estimate_cost_for_model(1_000_000, 500_000, &pricing);
        assert_eq!(est.input_cost_usd, 2.50);
        assert_eq!(est.output_cost_usd, 5.00);
        assert_eq!(est.total_cost_usd, 7.50);
    }

    #[test]
    fn test_compare_all_models_reduction() {
        let rep = compare_all_models(100_000, 10_000, 2_000, Some("gpt-4o"));
        assert!(rep.cost_savings_usd > 0.0);
        assert!(rep.cost_reduction_percent > 70.0);
    }
}
