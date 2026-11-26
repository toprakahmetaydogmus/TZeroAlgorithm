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
        description="Private Key Block or Header (RSA, EC, OPENSSH, DSA, PGP)",
        pattern=re.compile(r"-----BEGIN (?:[A-Z0-9 ]{1,32} )?PRIVATE KEY-----"),
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
    _PEM_BEGIN_RE = re.compile(r"-----BEGIN (?:[A-Z0-9 ]{1,32} )?PRIVATE KEY-----")
    _PEM_END_RE = re.compile(r"-----END (?:[A-Z0-9 ]{1,32} )?PRIVATE KEY-----")

    @classmethod
    def _iter_pem_block_spans(cls, text: str) -> List[Tuple[int, int]]:
        """Linearly locates complete PEM BEGIN..END block byte spans without polynomial regex backtracking."""
        spans: List[Tuple[int, int]] = []
        pos = 0
        for begin_match in cls._PEM_BEGIN_RE.finditer(text):
            if begin_match.start() < pos:
                continue
            end_match = cls._PEM_END_RE.search(text, begin_match.end())
            if not end_match:
                break
            spans.append((begin_match.start(), end_match.end()))
            pos = end_match.end()
        return spans

    @classmethod
    def _mask_pem_blocks(cls, text: str, replacement: str = "[ZERO_LEAK_MASKED_PRIVATE_KEY]") -> str:
        """Replaces complete PEM BEGIN..END blocks linearly cleanly."""
        spans = cls._iter_pem_block_spans(text)
        if not spans:
            return text
        chunks: List[str] = []
        last = 0
        for s, e in spans:
            chunks.append(text[last:s])
            chunks.append(replacement)
            last = e
        chunks.append(text[last:])
        return "".join(chunks)

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
        """Scans in-memory text (including comments and multiline PEM blocks) for secrets."""
        if not text:
            return []

        findings: List[SecretFinding] = []
        lines = text.splitlines()

        # Pre-compute line numbers covered by complete multi-line PEM blocks
        pem_ranges: List[Tuple[int, int]] = []
        for s_pos, e_pos in cls._iter_pem_block_spans(text):
            block_txt = text[s_pos:e_pos]
            start_line = text[:s_pos].count("\n") + 1
            end_line = text[:e_pos].count("\n") + 1
            pem_ranges.append((start_line, end_line))
            findings.append(SecretFinding(
                rule_id="SEC-CRYPTO-001",
                provider="PKI",
                description="Private Key Block (PEM)",
                severity="CRITICAL",
                line_no=start_line,
                preview="[ZERO_LEAK_MASKED_PRIVATE_KEY]",
                entropy=round(calculate_shannon_entropy(block_txt), 2),
                is_entropy_anomaly=False,
                secret_value=block_txt,
            ))

        def _in_pem_block(ln: int) -> bool:
            return any(s <= ln <= e for s, e in pem_ranges)

        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or _in_pem_block(lineno):
                continue

            # 1. Signature Rule Matching (scans code AND comment lines alike)
            has_specific_provider_match = False
            for rule in SECRET_RULES:
                if rule.rule_id == "SEC-CRYPTO-001":
                    if cls._PEM_BEGIN_RE.search(line):
                        val = cls._PEM_BEGIN_RE.search(line).group(0)
                        findings.append(SecretFinding(
                            rule_id=rule.rule_id,
                            provider=rule.provider,
                            description=rule.description,
                            severity=rule.severity,
                            line_no=lineno,
                            preview=cls.mask_preview(line),
                            entropy=round(calculate_shannon_entropy(val), 2),
                            is_entropy_anomaly=False,
                            secret_value=val,
                        ))
                        has_specific_provider_match = True
                    continue

                # If a specific provider rule matched, avoid duplicate generic rule hit on same line
                if rule.rule_id == "SEC-GENERIC-001" and has_specific_provider_match:
                    continue

                for match in rule.pattern.finditer(line):
                    # Preserve capture group 1 for generic/Bearer assignment rules so LHS variable stays intact
                    if rule.rule_id in ("SEC-GENERIC-001", "SEC-AUTH-002") and match.lastindex and match.lastindex >= 1:
                        val = match.group(1)
                    else:
                        val = match.group(0)
                    if cls.is_placeholder(val) or cls.is_placeholder(match.group(0)):
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
                        secret_value=val,
                    ))
                    if rule.provider != "Generic":
                        has_specific_provider_match = True

            # 2. Shannon Entropy Scanner for Unmatched Candidate Tokens
            if check_entropy and not stripped.startswith(("#", "//", "*", "/*")):
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
                                secret_value=tok,
                            ))

        return findings

    @classmethod
    def mask_preview(cls, line: str, max_len: int = 70) -> str:
        """Sanitizes line for safe terminal output and logging."""
        sanitized = cls.sanitize_text(line, allow_incomplete_pem=True)
        if len(sanitized) > max_len:
            return sanitized[:max_len] + "..."
        return sanitized

    @classmethod
    def sanitize_text(cls, text: str, allow_incomplete_pem: bool = False) -> str:
        """Sanitizes text by masking all detected secrets with Zero-Leak tokens."""
        if not text:
            return ""

        sanitized = cls._mask_pem_blocks(text, "[ZERO_LEAK_MASKED_PRIVATE_KEY]")

        if cls._PEM_BEGIN_RE.search(sanitized):
            if not allow_incomplete_pem:
                raise ValueError(
                    "Incomplete PEM private key block detected without END delimiter; aborting redaction to prevent body leak."
                )
            sanitized = cls._PEM_BEGIN_RE.sub("[ZERO_LEAK_MASKED_PRIVATE_KEY]", sanitized)

        # 1. Mask specific patterns
        for rule in SECRET_RULES:
            if rule.rule_id == "SEC-CRYPTO-001":
                continue

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
    def _sanitize_string_value(cls, val: str, allow_incomplete_pem: bool = False) -> str:
        """Sanitize an extracted string value even when unquoted inside an AST literal."""
        cleaned = cls.sanitize_text(val, allow_incomplete_pem=allow_incomplete_pem)
        if cleaned != val:
            return cleaned
        # Strip unquoted high-entropy raw tokens inside AST constants if scan_text flags them
        stripped = val.strip()
        if cls.scan_text(f'val = "{stripped}"'):
            if len(stripped) >= cls.MIN_ENTROPY_LENGTH and calculate_shannon_entropy(stripped) >= 4.4 and not cls.is_placeholder(stripped):
                return f"{stripped[:4]}...[ZERO_LEAK_HIGH_ENTROPY_SECRET]"
            if len(stripped) >= 12 and not cls.is_placeholder(stripped):
                return "[ZERO_LEAK_MASKED_VALUE]"
        return cleaned

    @classmethod
    def sanitize_ast(cls, tree: ast.AST) -> ast.AST:
        """Walks an AST tree and replaces hardcoded string literals containing secrets."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                node.value = cls._sanitize_string_value(node.value)
        ast.fix_missing_locations(tree)
        # Re-verify unparsed code so no AST literal secret survives
        try:
            rendered = ast.unparse(tree)
            remaining = cls.scan_text(rendered)
            if remaining:
                secret_vals = {f.secret_value for f in remaining if f.secret_value}
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        for sv in secret_vals:
                            if sv and sv in node.value:
                                node.value = node.value.replace(sv, "[ZERO_LEAK_MASKED_VALUE]")
        except Exception:
            pass
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
    def scan_workspace(cls, workspace_dir: str = ".", exclude_tests: bool = True) -> dict:
        """Scans a workspace directory for any hardcoded secrets and returns violations dict."""
        files_map = {}
        ignored_dirs = {"__pycache__", "venv", ".venv", "node_modules", "dist", "build", ".git"}
        if exclude_tests:
            ignored_dirs.update({"tests", "test", "fixtures"})
        for root, dirs, files in os.walk(workspace_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ignored_dirs]
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
    def resolve_project_root(cls, target_path: str) -> str:
        """Resolve nearest project root (.git ancestor) or target directory consistently."""
        abs_p = os.path.abspath(target_path)
        start = abs_p if os.path.isdir(abs_p) else os.path.dirname(abs_p)
        curr = start
        while True:
            if os.path.isdir(os.path.join(curr, ".git")):
                return curr
            parent = os.path.dirname(curr)
            if parent == curr:
                return start
            curr = parent

    @classmethod
    def check_env_git_status(
        cls, env_file_path: str, gitignore_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Use Git check-ignore/ls-files when available (fallback to real rule parsing)."""
        import subprocess
        abs_env = os.path.abspath(env_file_path)
        proj_root = cls.resolve_project_root(abs_env)
        env_name = os.path.basename(abs_env)
        in_git = os.path.isdir(os.path.join(proj_root, ".git"))
        tracked = False
        ignored = False

        if in_git:
            rel_env = os.path.relpath(abs_env, proj_root).replace("\\", "/")
            tr = subprocess.run(
                ["git", "-C", proj_root, "ls-files", "--error-unmatch", rel_env],
                capture_output=True, text=True, check=False,
            )
            tracked = tr.returncode == 0
            ig = subprocess.run(
                ["git", "-C", proj_root, "check-ignore", "-q", abs_env],
                capture_output=True, text=True, check=False,
            )
            ignored = ig.returncode == 0
        elif gitignore_path and os.path.isfile(gitignore_path):
            with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as gf:
                for raw_line in gf:
                    rule = raw_line.strip()
                    if not rule or rule.startswith("#") or rule.startswith("!"):
                        continue
                    norm = rule.lstrip("/")
                    if norm in (env_name, "*.env") or (norm == ".env" and env_name == ".env"):
                        ignored = True
                        break
        return {
            "in_git": in_git,
            "tracked": tracked,
            "ignored": ignored,
            "warning": f"WARNING: {abs_env} is already tracked by Git! Run `git rm --cached {env_name}`." if tracked else "",
        }

    @classmethod
    def _load_existing_env(cls, env_file_path: Optional[str]) -> Dict[str, str]:
        env_map: Dict[str, str] = {}
        if env_file_path and os.path.isfile(env_file_path):
            with open(env_file_path, "r", encoding="utf-8", errors="replace") as ef:
                for raw in ef:
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    k = k.strip()
                    if k:
                        env_map[k] = v.strip()
        return env_map

    @classmethod
    def auto_migrate_to_env(
        cls,
        code_str: str,
        env_file_path: Optional[str] = None,
        gitignore_path: Optional[str] = None,
        shared_env_registry: Optional[Dict[str, str]] = None,
        dry_run: bool = False,
    ) -> Tuple[str, str, int, str]:
        """Extract hardcoded secrets to .env atomically without variable collisions or partial writes."""
        findings = cls.scan_text(code_str)
        valid_findings = [f for f in findings if f.secret_value and not cls.is_placeholder(f.secret_value)]

        if not valid_findings:
            return code_str, "# No secrets detected.", 0, "### 100% Zero-Leak Certified\nNo hardcoded credentials found in source code."

        migrated_code = code_str
        env_registry: Dict[str, str] = shared_env_registry if shared_env_registry is not None else cls._load_existing_env(env_file_path)
        new_env_entries: Dict[str, str] = {}

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
            "PKI": "PRIVATE_KEY_PEM",
            "PrivateKey": "PRIVATE_KEY_PEM",
        }

        report_lines = [
            "### T-Zero Zero-Leak Auto-Vault Migration",
            f"Extracted and secured **{len(unique_findings)}** hardcoded secret(s) into environment configuration:\n",
            "| Provider | Variable Assigned | Redacted Secret |",
            "| :--- | :--- | :--- |",
        ]

        # Build reverse map secret_value -> existing env var for idempotent reuse
        val_to_var = {v: k for k, v in env_registry.items()}

        for f in unique_findings:
            if f.secret_value in val_to_var:
                var_name = val_to_var[f.secret_value]
            else:
                base_var = provider_map.get(f.provider, "")
                if not base_var:
                    clean_desc = re.sub(r"[^A-Z0-9_]", "_", f.description.upper()[:20]).strip("_")
                    base_var = f"{clean_desc or 'APP'}_SECRET"

                var_name = base_var
                idx = 2
                while var_name in env_registry:
                    var_name = f"{base_var}_{idx}"
                    idx += 1
                env_registry[var_name] = f.secret_value
                val_to_var[f.secret_value] = var_name
                new_env_entries[var_name] = f.secret_value

            redacted = f.secret_value[:6] + "..." + f.secret_value[-4:] if len(f.secret_value) > 12 else "***"
            report_lines.append(f"| `{f.provider}` | `{var_name}` | `{redacted}` |")

            pat_d = f'"{f.secret_value}"'
            pat_s = f"'{f.secret_value}'"
            replacement = f'os.environ.get("{var_name}", "")'
            if pat_d in migrated_code:
                migrated_code = migrated_code.replace(pat_d, replacement)
            elif pat_s in migrated_code:
                migrated_code = migrated_code.replace(pat_s, replacement)
            else:
                # Preserve surrounding quotes/assignment cleanly if matched inside a quoted value
                escaped_v = re.escape(f.secret_value)
                if re.search(rf"""(['"]){escaped_v}\1""", migrated_code):
                    migrated_code = re.sub(rf"""(['"]){escaped_v}\1""", replacement, migrated_code)
                else:
                    migrated_code = migrated_code.replace(f.secret_value, replacement)

        if "os.environ" in migrated_code and "import os" not in migrated_code and "from os import" not in migrated_code:
            lines_m = migrated_code.splitlines(keepends=True)
            ins_idx = 0
            for idx_l, ln_txt in enumerate(lines_m):
                s_ln = ln_txt.strip()
                if idx_l == 0 and s_ln.startswith("#!"):
                    ins_idx = idx_l + 1
                elif s_ln.startswith("# -*-") or s_ln.startswith("# coding"):
                    ins_idx = idx_l + 1
                elif s_ln.startswith("from __future__ import"):
                    ins_idx = idx_l + 1
                elif s_ln and not s_ln.startswith("#"):
                    break
            lines_m.insert(ins_idx, "import os\n")
            migrated_code = "".join(lines_m)

        env_lines = ["# Auto-Vault Generated by T-Zero Zero-Leak Engine", "# DO NOT COMMIT THIS FILE TO PUBLIC REPOSITORIES", ""]
        for k, v in env_registry.items():
            env_lines.append(f"{k}={v}")
        env_content = "\n".join(env_lines) + "\n"

        # Stage & commit physical .gitignore and .env atomically BEFORE returning success
        if not dry_run and (env_file_path or gitignore_path):
            import tempfile
            if env_file_path and gitignore_path is None:
                gitignore_path = os.path.join(os.path.dirname(os.path.abspath(env_file_path)), ".gitignore")

            gi_staged = None
            env_staged = None
            try:
                if gitignore_path and env_file_path:
                    git_status = cls.check_env_git_status(env_file_path, gitignore_path)
                    if git_status.get("warning"):
                        report_lines.append(f"\n> {git_status['warning']}")
                    if not git_status.get("ignored"):
                        existing_gi = ""
                        if os.path.isfile(gitignore_path):
                            with open(gitignore_path, "r", encoding="utf-8") as gf:
                                existing_gi = gf.read()
                        env_base = os.path.basename(os.path.abspath(env_file_path))
                        sep = "\n" if existing_gi and not existing_gi.endswith("\n") else ""
                        new_gi = f"{existing_gi}{sep}{env_base}\n"
                        gi_dir = os.path.dirname(os.path.abspath(gitignore_path)) or "."
                        os.makedirs(gi_dir, exist_ok=True)
                        with tempfile.NamedTemporaryFile("w", dir=gi_dir, delete=False, encoding="utf-8", prefix=".tzero_gi_") as tf:
                            tf.write(new_gi)
                            gi_staged = tf.name

                if env_file_path:
                    env_dir = os.path.dirname(os.path.abspath(env_file_path)) or "."
                    os.makedirs(env_dir, exist_ok=True)
                    with tempfile.NamedTemporaryFile("w", dir=env_dir, delete=False, encoding="utf-8", prefix=".tzero_env_") as tf:
                        tf.write(env_content)
                        env_staged = tf.name

                if gi_staged:
                    os.replace(gi_staged, gitignore_path)
                    gi_staged = None
                if env_staged:
                    os.replace(env_staged, env_file_path)
                    env_staged = None
            except Exception as exc:
                for p in (gi_staged, env_staged):
                    if p and os.path.exists(p):
                        try:
                            os.remove(p)
                        except OSError:
                            pass
                raise RuntimeError(f"Auto-Vault failed to persist environment/gitignore safely: {exc}") from exc

        return migrated_code, env_content, len(unique_findings), "\n".join(report_lines)

    @classmethod
    def migrate_files_atomically(
        cls,
        file_paths: List[str],
        env_file_path: str,
        gitignore_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Atomically migrate multiple files using a shared env table with rollback on write errors."""
        import tempfile
        abs_env = os.path.abspath(env_file_path)
        abs_gi = os.path.abspath(gitignore_path) if gitignore_path else os.path.join(os.path.dirname(abs_env), ".gitignore")
        orig_sources: Dict[str, str] = {}
        staged_sources: Dict[str, str] = {}
        orig_env = None
        if os.path.isfile(abs_env):
            with open(abs_env, "r", encoding="utf-8") as _ef:
                orig_env = _ef.read()
        orig_gi = None
        if os.path.isfile(abs_gi):
            with open(abs_gi, "r", encoding="utf-8") as _gf:
                orig_gi = _gf.read()
        shared_env = cls._load_existing_env(abs_env)
        total_migrated = 0

        try:
            for fp in file_paths:
                abs_fp = os.path.abspath(fp)
                with open(abs_fp, "r", encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
                migrated, _, cnt, _ = cls.auto_migrate_to_env(
                    raw,
                    env_file_path=abs_env,
                    gitignore_path=abs_gi,
                    shared_env_registry=shared_env,
                    dry_run=True,
                )
                if cnt > 0 and migrated != raw:
                    if abs_fp.endswith(".py"):
                        ast.parse(migrated, filename=abs_fp)
                    orig_sources[abs_fp] = raw
                    fdir = os.path.dirname(abs_fp) or "."
                    with tempfile.NamedTemporaryFile("w", dir=fdir, delete=False, encoding="utf-8", prefix=".tzero_src_") as tf:
                        tf.write(migrated)
                        staged_sources[abs_fp] = tf.name
                    total_migrated += cnt

            if total_migrated == 0:
                return {"success": True, "migrated_count": 0, "env_file": abs_env, "warning": ""}

            # Write .gitignore and .env atomically BEFORE mutating any source files
            git_status = cls.check_env_git_status(abs_env, abs_gi)
            if not git_status.get("ignored"):
                existing_gi = orig_gi or ""
                env_base = os.path.basename(abs_env)
                sep = "\n" if existing_gi and not existing_gi.endswith("\n") else ""
                os.makedirs(os.path.dirname(abs_gi) or ".", exist_ok=True)
                with tempfile.NamedTemporaryFile("w", dir=os.path.dirname(abs_gi) or ".", delete=False, encoding="utf-8", prefix=".tzero_gi_") as tf:
                    tf.write(f"{existing_gi}{sep}{env_base}\n")
                    gi_tmp = tf.name
                os.replace(gi_tmp, abs_gi)

            env_lines = ["# Auto-Vault Generated by T-Zero Zero-Leak Engine", "# DO NOT COMMIT THIS FILE TO PUBLIC REPOSITORIES", ""]
            for k, v in shared_env.items():
                env_lines.append(f"{k}={v}")
            os.makedirs(os.path.dirname(abs_env) or ".", exist_ok=True)
            with tempfile.NamedTemporaryFile("w", dir=os.path.dirname(abs_env) or ".", delete=False, encoding="utf-8", prefix=".tzero_env_") as tf:
                tf.write("\n".join(env_lines) + "\n")
                env_tmp = tf.name
            os.replace(env_tmp, abs_env)

            # Commit staged sources
            for abs_fp, tmp_p in staged_sources.items():
                os.replace(tmp_p, abs_fp)
            staged_sources.clear()

            return {
                "success": True,
                "migrated_count": total_migrated,
                "env_file": abs_env,
                "gitignore_file": abs_gi,
                "warning": git_status.get("warning", ""),
            }
        except Exception as exc:
            # Rollback .env / .gitignore / any partially touched sources
            for tmp_p in staged_sources.values():
                if os.path.exists(tmp_p):
                    try:
                        os.remove(tmp_p)
                    except OSError:
                        pass
            if orig_env is not None:
                try:
                    with open(abs_env, "w", encoding="utf-8") as ef:
                        ef.write(orig_env)
                except OSError:
                    pass
            elif os.path.exists(abs_env):
                try:
                    os.remove(abs_env)
                except OSError:
                    pass
            if orig_gi is not None:
                try:
                    with open(abs_gi, "w", encoding="utf-8") as gf:
                        gf.write(orig_gi)
                except OSError:
                    pass
            return {"success": False, "error": str(exc), "migrated_count": 0}

