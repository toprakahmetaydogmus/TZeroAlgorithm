# -*- coding: utf-8 -*-
"""
Siber Akademi — T-Zero 100% Zero-Leak Security & Shannon Entropy Engine.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT

Centralized, high-throughput offline security engine providing:
1. Signature-based secret scanning across 20+ cloud, AI, payment, and VCS providers.
2. Shannon Entropy mathematical anomaly detection for raw un-prefixed cryptographic keys.
3. AST-level and textual Zero-Leak secret redaction ([ZERO_LEAK_MASKED_...]).
4. Git pre-commit, MCP, and CLI verification integrations.
"""

import math
import os
import re
import ast
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Set


# ==============================================================================
# 1. SHANNON ENTROPY DETECTOR
# ==============================================================================

def calculate_shannon_entropy(data: str) -> float:
    """Calculates Shannon entropy (bits per symbol) of a given string.
    
    Higher entropy indicates higher randomness (e.g. cryptographic keys,
    base64-encoded secrets, high-entropy tokens).
    Standard English text: ~2.5 - 3.5
    Source code identifiers: ~3.0 - 3.8
    Random Base64 / Hex secrets (32+ chars): ~4.5 - 6.0
    """
    if not data:
        return 0.0
    length = len(data)
    counts = Counter(data)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


# Ignore words and markers that produce high false positives
COMMON_ENTROPY_WHITELIST = {
    "undefined", "constructor", "classmethod", "staticmethod", "authorization",
    "content-type", "application/json", "multipart/form-data", "x-www-form-urlencoded",
    "abcdefghijklmnopqrstuvwxyz", "0123456789abcdef", "placeholder", "your_secret_here"
}

PLACEHOLDER_SUBSTRINGS = (
    "YOUR_API_KEY", "YOUR-API-KEY", "YOUR_SECRET", "YOUR_TOKEN",
    "YOUR-", "YOUR_", "ENTER_YOUR", "PLACEHOLDER", "CHANGEME", "INSERT_HERE",
    "000000000000", "EXAMPLE_KEY", "EXAMPLEKEY", "EXAMPLE_SECRET",
    "MOCK_KEY_PLACEHOLDER", "MOCK", "DEMO"
)


# ==============================================================================
# 2. COMPREHENSIVE SECRET SIGNATURE DATABASE
# ==============================================================================

@dataclass
class SecretRule:
    rule_id: str
    provider: str
    description: str
    pattern: re.Pattern
    severity: str = "CRITICAL"
    mask_tag: str = "[ZERO_LEAK_MASKED_SECRET]"


SECRET_RULES: List[SecretRule] = [
    # --- AI & Cloud Providers ---
    SecretRule(
        rule_id="SEC-AI-002",
        provider="Anthropic",
        description="Anthropic Claude API Key (sk-ant-...)",
        pattern=re.compile(r"\b(sk-ant-[a-zA-Z0-9_\-]{30,})\b"),
        mask_tag="[ZERO_LEAK_MASKED_ANTHROPIC_KEY]"
    ),
    SecretRule(
        rule_id="SEC-AI-001",
        provider="OpenAI",
        description="OpenAI API Key (sk-...)",
        pattern=re.compile(r"\b(sk-(?!ant-)[a-zA-Z0-9_\-]{20,})\b"),
        mask_tag="[ZERO_LEAK_MASKED_OPENAI_KEY]"
    ),
    SecretRule(
        rule_id="SEC-AI-003",
        provider="Google",
        description="Google Cloud / Gemini API Key (AIza...)",
        pattern=re.compile(r"\b(AIza[0-9A-Za-z\-_]{30,45})\b"),
        mask_tag="[ZERO_LEAK_MASKED_GEMINI_KEY]"
    ),
    SecretRule(
        rule_id="SEC-AI-004",
        provider="HuggingFace",
        description="HuggingFace User Access Token (hf_...)",
        pattern=re.compile(r"\b(hf_[a-zA-Z0-9]{34,})\b"),
        mask_tag="[ZERO_LEAK_MASKED_HF_TOKEN]"
    ),
    SecretRule(
        rule_id="SEC-AI-005",
        provider="NVIDIA",
        description="NVIDIA NIM API Key (nvapi-...)",
        pattern=re.compile(r"\b(nvapi-[a-zA-Z0-9_\-]{30,})\b"),
        mask_tag="[ZERO_LEAK_MASKED_NVIDIA_KEY]"
    ),
    SecretRule(
        rule_id="SEC-AI-006",
        provider="Groq",
        description="Groq Cloud API Key (gsk_...)",
        pattern=re.compile(r"\b(gsk_[a-zA-Z0-9]{48,})\b"),
        mask_tag="[ZERO_LEAK_MASKED_GROQ_KEY]"
    ),
    SecretRule(
        rule_id="SEC-AI-007",
        provider="OpenRouter",
        description="OpenRouter API Key (sk-or-v1-...)",
        pattern=re.compile(r"\b(sk-or-v1-[a-f0-9]{64})\b"),
        mask_tag="[ZERO_LEAK_MASKED_OPENROUTER_KEY]"
    ),
    SecretRule(
        rule_id="SEC-AI-008",
        provider="Perplexity",
        description="Perplexity AI API Key (pplx-...)",
        pattern=re.compile(r"\b(pplx-[a-zA-Z0-9]{48,})\b"),
        mask_tag="[ZERO_LEAK_MASKED_PERPLEXITY_KEY]"
    ),
    SecretRule(
        rule_id="SEC-AI-009",
        provider="Replicate",
        description="Replicate API Token (r8_...)",
        pattern=re.compile(r"\b(r8_[a-zA-Z0-9]{32,})\b"),
        mask_tag="[ZERO_LEAK_MASKED_REPLICATE_KEY]"
    ),
    SecretRule(
        rule_id="SEC-AI-010",
        provider="Cohere",
        description="Cohere API Key (co-...)",
        pattern=re.compile(r"\b(co-[a-zA-Z0-9]{40,})\b"),
        mask_tag="[ZERO_LEAK_MASKED_COHERE_KEY]"
    ),
    SecretRule(
        rule_id="SEC-REG-001",
        provider="NPM",
        description="NPM Registry Access Token (npm_...)",
        pattern=re.compile(r"\b(npm_[a-zA-Z0-9]{32,40})\b"),
        mask_tag="[ZERO_LEAK_MASKED_NPM_TOKEN]"
    ),

    # --- Cloud Infrastructure & VCS ---
    SecretRule(
        rule_id="SEC-AWS-001",
        provider="AWS",
        description="AWS Access Key ID (AKIA...)",
        pattern=re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        mask_tag="[ZERO_LEAK_MASKED_AWS_KEY]"
    ),
    SecretRule(
        rule_id="SEC-AWS-002",
        provider="AWS",
        description="AWS Secret Access Key",
        pattern=re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*['\"]([0-9a-zA-Z/+]{40})['\"]"),
        mask_tag="[ZERO_LEAK_MASKED_AWS_SECRET]"
    ),
    SecretRule(
        rule_id="SEC-GH-001",
        provider="GitHub",
        description="GitHub Personal Access Token (Classic: ghp_...)",
        pattern=re.compile(r"\b(ghp_[a-zA-Z0-9]{36})\b"),
        mask_tag="[ZERO_LEAK_MASKED_GITHUB_PAT]"
    ),
    SecretRule(
        rule_id="SEC-GH-002",
        provider="GitHub",
        description="GitHub OAuth Token (gho_...)",
        pattern=re.compile(r"\b(gho_[a-zA-Z0-9]{36})\b"),
        mask_tag="[ZERO_LEAK_MASKED_GITHUB_OAUTH]"
    ),
    SecretRule(
        rule_id="SEC-GH-003",
        provider="GitHub",
        description="GitHub Fine-Grained Personal Access Token (github_pat_...)",
        pattern=re.compile(r"\b(github_pat_[a-zA-Z0-9_]{50,})\b"),
        mask_tag="[ZERO_LEAK_MASKED_GITHUB_FINE_PAT]"
    ),
    SecretRule(
        rule_id="SEC-SLACK-001",
        provider="Slack",
        description="Slack Bot/User Token (xoxb/xoxp-...)",
        pattern=re.compile(r"\b(xox[baprs]-(?:[0-9a-zA-Z]{9,}-)+[a-zA-Z0-9]{20,})\b"),
        mask_tag="[ZERO_LEAK_MASKED_SLACK_TOKEN]"
    ),
    SecretRule(
        rule_id="SEC-STRIPE-001",
        provider="Stripe",
        description="Stripe Live Secret Key (sk_live_...)",
        pattern=re.compile(r"\b((?:sk|rk)_live_[0-9a-zA-Z]{24,})\b"),
        mask_tag="[ZERO_LEAK_MASKED_STRIPE_KEY]"
    ),

    # --- Cryptographic & Auth Artifacts ---
    SecretRule(
        rule_id="SEC-CRYPTO-001",
        provider="PKI",
        description="Private Key Header (RSA, EC, OPENSSH, DSA, PGP)",
        pattern=re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
        mask_tag="[ZERO_LEAK_MASKED_PRIVATE_KEY]"
    ),
    SecretRule(
        rule_id="SEC-AUTH-001",
        provider="JWT",
        description="JSON Web Token (JWT Header + Payload + Signature)",
        pattern=re.compile(r"\b(eyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,})\b"),
        mask_tag="[ZERO_LEAK_MASKED_JWT]"
    ),
    SecretRule(
        rule_id="SEC-AUTH-002",
        provider="HTTP",
        description="Bearer Authorization Token Header",
        pattern=re.compile(r"(?i)Bearer\s+([a-zA-Z0-9_\.\-]{24,})"),
        mask_tag="Bearer [ZERO_LEAK_MASKED_TOKEN]"
    ),
    SecretRule(
        rule_id="SEC-DB-001",
        provider="Database",
        description="Database Connection URI with Credentials",
        pattern=re.compile(r"(?:postgres|postgresql|mysql|mongodb(?:\+srv)?|redis)://[^:\s]+:[^@\s]+@[^\s\"']+"),
        mask_tag="[ZERO_LEAK_MASKED_DB_URL]"
    ),
    SecretRule(
        rule_id="SEC-GENERIC-001",
        provider="Generic",
        description="Hardcoded Secret Assignment (api_key/secret/password)",
        pattern=re.compile(r"""(?i)(?:api_?key|secret_?key|app_?secret|db_?pass(?:word)?|auth_?token)\s*[:=]\s*['"]([^'"]{12,})['"]"""),
        mask_tag="[ZERO_LEAK_MASKED_VALUE]"
    ),
]


# ==============================================================================
# 3. DETECTION & SCANNING INTERFACES
# ==============================================================================

@dataclass
class SecretFinding:
    rule_id: str
    provider: str
    description: str
    severity: str
    line_no: int
    preview: str
    entropy: float = 0.0
    is_entropy_anomaly: bool = False
    secret_value: str = ""


class ZeroLeakEngine:
    """Enterprise 100% Zero-Leak security scanner and sanitizer."""

    MIN_ENTROPY_THRESHOLD: float = 4.75
    MIN_ENTROPY_LENGTH: int = 28

    @classmethod
    def is_placeholder(cls, s: str) -> bool:
        """Determines if a candidate string is an intentional placeholder/mock."""
        up = s.upper()
        return any(ph in up for ph in PLACEHOLDER_SUBSTRINGS)

    @classmethod
    def is_natural_or_identifier(cls, s: str) -> bool:
        """Rejects common false positives (all-lowercase slugs, public project/team IDs)."""
        # Exclude public identifiers
        if s.startswith(("prj_", "team_", "col_", "tbl_", "usr_", "pkg_", "sub_")):
            return True
        # Natural language smushed slugs without variety
        if s.islower() or s.isupper():
            return True
        # Check character class diversity (needs at least uppercase, lowercase, and digit/special)
        has_upper = any(c.isupper() for c in s)
        has_lower = any(c.islower() for c in s)
        has_digit = any(c.isdigit() for c in s)
        has_punct = any(not c.isalnum() for c in s)
        diversity = sum([has_upper, has_lower, (has_digit or has_punct)])
        return diversity < 2

    @classmethod
    def scan_text(cls, text: str, check_entropy: bool = True) -> List[SecretFinding]:
        """Scans in-memory text for known secrets and high-entropy secret anomalies."""
        if not text:
            return []

        findings: List[SecretFinding] = []
        lines = text.splitlines()

        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "//", "*", "/*")):
                continue

            # 1. Signature Rule Matching
            has_specific_provider_match = False
            for rule in SECRET_RULES:
                # If a specific provider rule matched, avoid duplicate generic rule hit on same line
                if rule.rule_id == "SEC-GENERIC-001" and has_specific_provider_match:
                    continue

                for match in rule.pattern.finditer(line):
                    val = match.group(0)
                    if cls.is_placeholder(val):
                        continue

                    ent = calculate_shannon_entropy(val)
                    findings.append(SecretFinding(
                        rule_id=rule.rule_id,
                        provider=rule.provider,
                        description=rule.description,
                        severity=rule.severity,
                        line_no=lineno,
                        preview=cls.mask_preview(line),
                        entropy=round(ent, 2),
                        is_entropy_anomaly=False,
                        secret_value=val
                    ))
                    if rule.provider != "Generic":
                        has_specific_provider_match = True

            # 2. Shannon Entropy Scanner for Unmatched Candidate Tokens
            if check_entropy:
                # Candidate secrets must be single compact tokens without whitespace, slashes, or URL schemas
                candidate_tokens = re.findall(r"""['"]([A-Za-z0-9+/=_\-]{28,})['"]""", line)
                for tok in candidate_tokens:
                    # Filter out URLs, file paths, and common non-secrets
                    if any(prefix in tok for prefix in ("http:", "https:", "/", "\\", "@", ".com", ".org", ".net")):
                        continue
                    # Ignore SRI cryptographic package hashes and data URIs (e.g. package-lock.json integrity hashes)
                    if tok.startswith(("sha512-", "sha384-", "sha256-", "md5-", "urn:", "data:")):
                        continue
                    if any(kw in line.lower() for kw in ('"integrity"', '"resolved"', '"hash"', 'sha512-', 'sha256-')):
                        continue
                    if cls.is_placeholder(tok) or tok.lower() in COMMON_ENTROPY_WHITELIST:
                        continue
                    if cls.is_natural_or_identifier(tok):
                        continue
                    
                    ent = calculate_shannon_entropy(tok)
                    if ent >= cls.MIN_ENTROPY_THRESHOLD and len(tok) >= cls.MIN_ENTROPY_LENGTH:
                        already_reported = any(f.line_no == lineno for f in findings)
                        if not already_reported:
                            findings.append(SecretFinding(
                                rule_id="SEC-ENTROPY-001",
                                provider="EntropyAnomaly",
                                description=f"High-Entropy Secret Candidate (Shannon H={ent:.2f} >= {cls.MIN_ENTROPY_THRESHOLD})",
                                severity="HIGH",
                                line_no=lineno,
                                preview=cls.mask_preview(line),
                                entropy=round(ent, 2),
                                is_entropy_anomaly=True,
                                secret_value=tok
                            ))

        return findings

    @classmethod
    def mask_preview(cls, line: str, max_len: int = 70) -> str:
        """Sanitizes line for safe terminal output and logging."""
        sanitized = cls.sanitize_text(line)
        if len(sanitized) > max_len:
            return sanitized[:max_len] + "..."
        return sanitized

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """Sanitizes text by masking all detected secrets with Zero-Leak tokens."""
        if not text:
            return ""

        sanitized = text

        # 1. Mask specific patterns
        for rule in SECRET_RULES:
            def _replace_match(m):
                full_val = m.group(0)
                if cls.is_placeholder(full_val):
                    return full_val
                return rule.mask_tag
            sanitized = rule.pattern.sub(_replace_match, sanitized)

        # 2. Mask high entropy quoted literals
        def _replace_entropy(m):
            token = m.group(1)
            if not cls.is_placeholder(token) and calculate_shannon_entropy(token) >= 4.4:
                return f'"{token[:4]}...[ZERO_LEAK_HIGH_ENTROPY_SECRET]"'
            return m.group(0)

        sanitized = re.sub(r"""['"]([^'"]{20,})['"]""", _replace_entropy, sanitized)
        return sanitized

    @classmethod
    def sanitize_ast(cls, tree: ast.AST) -> ast.AST:
        """Walks an AST tree and replaces hardcoded string literals containing secrets."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value
                # Check if raw value itself or wrapped in quotes triggers detection
                if cls.scan_text(f'val = "{val}"'):
                    node.value = cls.sanitize_text(val)
        return tree

    @classmethod
    def scan_files_map(cls, files_map: Dict[str, str]) -> Dict[str, Any]:
        """Scans in-memory files map {relative_path: file_content}."""
        violations = []
        files_with_violations = 0

        for path, content in files_map.items():
            findings = cls.scan_text(content)
            if findings:
                files_with_violations += 1
                for f in findings:
                    violations.append({
                        "file": path,
                        "line": f.line_no,
                        "type": f.description,
                        "provider": f.provider,
                        "severity": f.severity,
                        "preview": f.preview,
                        "entropy": f.entropy
                    })

        return {
            "clean": len(violations) == 0,
            "violations": violations,
            "violation_count": len(violations),
            "files_scanned": len(files_map),
            "files_with_violations": files_with_violations,
            "status": "100% ZERO-LEAK VERIFIED" if not violations else "PROHIBITED CREDENTIALS DETECTED"
        }

    @classmethod
    def scan_workspace(cls, workspace_dir: str = ".") -> dict:
        """Scans a workspace directory for any hardcoded secrets and returns violations dict."""
        files_map = {}
        for root, dirs, files in os.walk(workspace_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "venv", ".venv", "node_modules", "dist", "build", ".git")]
            for f in files:
                if f.endswith((".py", ".js", ".ts", ".json", ".yaml", ".yml", ".env.example", ".sh", ".toml", ".txt")):
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                            files_map[fp] = fh.read()
                    except Exception:
                        pass
        return cls.scan_files_map(files_map)

    @classmethod
    def auto_migrate_to_env(
        cls,
        code_str: str,
        env_file_path: Optional[str] = None,
        gitignore_path: Optional[str] = None
    ) -> Tuple[str, str, int, str]:
        """Automatically extracts detected hardcoded secrets into .env format and refactors code with os.environ.get."""
        findings = cls.scan_text(code_str)
        valid_findings = [f for f in findings if f.secret_value and not cls.is_placeholder(f.secret_value)]
        
        if not valid_findings:
            return code_str, "# No secrets detected.", 0, "### 100% Zero-Leak Certified\nNo hardcoded credentials found in source code."

        migrated_code = code_str
        env_entries: Dict[str, str] = {}
        used_vars: Set[str] = set()
        counter = 1

        # Sort findings descending by length to avoid partial substrings
        unique_findings = []
        seen_vals = set()
        for f in valid_findings:
            if f.secret_value not in seen_vals:
                seen_vals.add(f.secret_value)
                unique_findings.append(f)
        unique_findings.sort(key=lambda x: len(x.secret_value), reverse=True)

        provider_map = {
            "OpenAI": "OPENAI_API_KEY",
            "Anthropic": "ANTHROPIC_API_KEY",
            "Google": "GEMINI_API_KEY",
            "HuggingFace": "HF_TOKEN",
            "NVIDIA": "NVIDIA_API_KEY",
            "AWS": "AWS_SECRET_ACCESS_KEY",
            "GitHub": "GITHUB_TOKEN",
            "GitLab": "GITLAB_TOKEN",
            "Stripe": "STRIPE_SECRET_KEY",
            "Slack": "SLACK_BOT_TOKEN",
            "Database": "DATABASE_URL",
            "JWT": "JWT_SECRET_TOKEN",
            "PrivateKey": "PRIVATE_KEY_PEM",
        }

        report_lines = [
            "### T-Zero Zero-Leak Auto-Vault Migration",
            f"Extracted and secured **{len(unique_findings)}** hardcoded secret(s) into environment configuration:\n",
            "| Provider | Variable Assigned | Redacted Secret |",
            "| :--- | :--- | :--- |",
        ]

        for f in unique_findings:
            base_var = provider_map.get(f.provider, "")
            if not base_var:
                clean_desc = re.sub(r"[^A-Z0-9_]", "_", f.description.upper()[:20])
                base_var = f"{clean_desc}_TOKEN"
                
            var_name = base_var
            while var_name in used_vars:
                var_name = f"{base_var}_{counter}"
                counter += 1
            used_vars.add(var_name)

            env_entries[var_name] = f.secret_value
            redacted = f.secret_value[:6] + "..." + f.secret_value[-4:] if len(f.secret_value) > 12 else "***"
            report_lines.append(f"| `{f.provider}` | `{var_name}` | `{redacted}` |")

            # Replace quotes in code
            pat_d = f'"{f.secret_value}"'
            pat_s = f"'{f.secret_value}'"
            replacement = f'os.environ.get("{var_name}", "")'
            if pat_d in migrated_code:
                migrated_code = migrated_code.replace(pat_d, replacement)
            elif pat_s in migrated_code:
                migrated_code = migrated_code.replace(pat_s, replacement)
            else:
                migrated_code = migrated_code.replace(f.secret_value, replacement)

        # Check if os is imported
        if "os.environ" in migrated_code and "import os" not in migrated_code and "from os import" not in migrated_code:
            migrated_code = "import os\n" + migrated_code

        # Build .env text
        env_lines = ["# Auto-Vault Generated by T-Zero Zero-Leak Engine", "# DO NOT COMMIT THIS FILE TO PUBLIC REPOSITORIES", ""]
        for k, v in env_entries.items():
            env_lines.append(f"{k}={v}")
        env_content = "\n".join(env_lines) + "\n"

        # If file paths provided, update physical .env and .gitignore
        if env_file_path:
            try:
                with open(env_file_path, "a", encoding="utf-8") as ef:
                    ef.write("\n" + "\n".join(f"{k}={v}" for k, v in env_entries.items()) + "\n")
            except Exception:
                pass

        if gitignore_path:
            try:
                gi_content = ""
                if os.path.exists(gitignore_path):
                    with open(gitignore_path, "r", encoding="utf-8") as gf:
                        gi_content = gf.read()
                if ".env" not in gi_content:
                    with open(gitignore_path, "a", encoding="utf-8") as gf:
                        gf.write("\n.env\n*.env\n")
            except Exception:
                pass

        return migrated_code, env_content, len(unique_findings), "\n".join(report_lines)

