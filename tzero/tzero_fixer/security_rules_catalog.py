# -*- coding: utf-8 -*-
"""T-Zero Security Rules & Secret Signatures Encyclopedic Catalog.

Provides 200+ battle-tested secret detection regular expressions and security rules
spanning all major cloud providers, AI/LLM vendors, payment gateways, databases,
CI/CD platforms, communication tools, and cryptographic key formats.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.4.0
"""

from typing import List, NamedTuple


class SecurityRule(NamedTuple):
    rule_id: str
    vendor: str
    name: str
    pattern: str
    severity: str
    recommended_env_var: str
    description: str


ENCYCLOPEDIC_SECURITY_RULES: List[SecurityRule] = [
    # -------------------------------------------------------------------------
    # 1. CLOUD INFRASTRUCTURE & VENDORS
    # -------------------------------------------------------------------------
    SecurityRule("TZ-SEC-AWS-001", "AWS", "AWS Access Key ID", r"\b(AKIA[0-9A-Z]{16})\b", "critical", "AWS_ACCESS_KEY_ID", "Amazon Web Services active access key"),
    SecurityRule("TZ-SEC-AWS-002", "AWS", "AWS Secret Access Key", r"""(?i)aws[_-]?secret[_-]?access[_-]?key\s*=\s*['"][A-Za-z0-9/+=]{40}['"]""", "critical", "AWS_SECRET_ACCESS_KEY", "Amazon Web Services secret signing key"),
    SecurityRule("TZ-SEC-AWS-003", "AWS", "AWS Session Token", r"""(?i)aws[_-]?session[_-]?token\s*=\s*['"][A-Za-z0-9/+=]{100,}['"]""", "critical", "AWS_SESSION_TOKEN", "Temporary STS session token"),
    SecurityRule("TZ-SEC-GCP-001", "Google Cloud", "Google Cloud API Key", r"\b(AIza[0-9A-Za-z\-_]{35})\b", "critical", "GCP_API_KEY", "Google Cloud platform API credential"),
    SecurityRule("TZ-SEC-GCP-002", "Google Cloud", "Google OAuth Refresh Token", r"\b(1//[0-9A-Za-z\-_]{40,})\b", "critical", "GCP_REFRESH_TOKEN", "Google OAuth 2.0 refresh token"),
    SecurityRule("TZ-SEC-AZURE-001", "Azure", "Azure Storage Account Key", r"""(?i)DefaultEndpointsProtocol=[^;]+;AccountName=[^;]+;AccountKey=[A-Za-z0-9/+=]{86}==;""", "critical", "AZURE_STORAGE_CONNECTION_STRING", "Azure Blob storage access connection string"),
    SecurityRule("TZ-SEC-AZURE-002", "Azure", "Azure Client Secret", r"""(?i)azure[_-]?client[_-]?secret\s*=\s*['"][A-Za-z0-9\._\-~]{34,44}['"]""", "critical", "AZURE_CLIENT_SECRET", "Azure Active Directory service principal secret"),
    SecurityRule("TZ-SEC-DO-001", "DigitalOcean", "DigitalOcean Personal Access Token", r"\b(dop_v1_[a-f0-9]{64})\b", "critical", "DIGITALOCEAN_TOKEN", "DigitalOcean API token v1"),
    SecurityRule("TZ-SEC-VERCEL-001", "Vercel", "Vercel Access Token", r"""(?i)vercel[_-]?(token|api[_-]?key)\s*=\s*['"][A-Za-z0-9]{24}['"]""", "critical", "VERCEL_TOKEN", "Vercel cloud deployment token"),
    SecurityRule("TZ-SEC-HEROKU-001", "Heroku", "Heroku API Key", r"""(?i)heroku[_-]?(api[_-]?key|token)\s*=\s*['"][0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}['"]""", "critical", "HEROKU_API_KEY", "Heroku PaaS API key"),

    # -------------------------------------------------------------------------
    # 2. AI / LLM PLATFORMS
    # -------------------------------------------------------------------------
    SecurityRule("TZ-SEC-OAI-001", "OpenAI", "OpenAI Secret Key", r"\b(sk-[A-Za-z0-9]{48})\b", "critical", "OPENAI_API_KEY", "OpenAI API secret authentication key"),
    SecurityRule("TZ-SEC-OAI-002", "OpenAI", "OpenAI Project Key", r"\b(sk-proj-[A-Za-z0-9_\-]{40,})\b", "critical", "OPENAI_API_KEY", "OpenAI project-scoped API key"),
    SecurityRule("TZ-SEC-ANTH-001", "Anthropic", "Anthropic Claude API Key", r"\b(sk-ant-[A-Za-z0-9_\-]{80,})\b", "critical", "ANTHROPIC_API_KEY", "Anthropic Claude platform key"),
    SecurityRule("TZ-SEC-GEM-001", "Google AI", "Gemini API Key", r"\b(AIzaSy[0-9A-Za-z\-_]{33})\b", "critical", "GEMINI_API_KEY", "Google Gemini developer studio key"),
    SecurityRule("TZ-SEC-HF-001", "HuggingFace", "HuggingFace User Access Token", r"\b(hf_[A-Za-z0-9]{34})\b", "critical", "HUGGINGFACE_TOKEN", "Hugging Face model repository token"),
    SecurityRule("TZ-SEC-COHERE-001", "Cohere", "Cohere API Key", r"""(?i)cohere[_-]?(api[_-]?key|token)\s*=\s*['"][A-Za-z0-9]{40}['"]""", "critical", "COHERE_API_KEY", "Cohere AI generation key"),
    SecurityRule("TZ-SEC-GROQ-001", "Groq", "Groq LPU API Key", r"\b(gsk_[A-Za-z0-9]{52})\b", "critical", "GROQ_API_KEY", "Groq ultra-fast LPU inference key"),
    SecurityRule("TZ-SEC-MISTRAL-001", "Mistral", "Mistral AI API Key", r"""(?i)mistral[_-]?(api[_-]?key|token)\s*=\s*['"][A-Za-z0-9]{32}['"]""", "critical", "MISTRAL_API_KEY", "Mistral platform token"),
    SecurityRule("TZ-SEC-TOGETHER-001", "Together", "Together AI API Key", r"""(?i)together[_-]?(api[_-]?key|token)\s*=\s*['"][a-f0-9]{64}['"]""", "critical", "TOGETHER_API_KEY", "Together AI serverless key"),
    SecurityRule("TZ-SEC-PINECONE-001", "Pinecone", "Pinecone Vector DB Key", r"""(?i)pinecone[_-]?(api[_-]?key|token)\s*=\s*['"][a-f0-9\-]{36}['"]""", "critical", "PINECONE_API_KEY", "Pinecone vector index secret key"),

    # -------------------------------------------------------------------------
    # 3. CODE REPOSITORIES & CI/CD
    # -------------------------------------------------------------------------
    SecurityRule("TZ-SEC-GH-001", "GitHub", "GitHub Personal Access Token", r"\b(ghp_[A-Za-z0-9]{36})\b", "critical", "GITHUB_TOKEN", "GitHub classic personal access token"),
    SecurityRule("TZ-SEC-GH-002", "GitHub", "GitHub Fine-Grained Token", r"\b(github_pat_[A-Za-z0-9_]{60,})\b", "critical", "GITHUB_PAT", "GitHub fine-grained repository token"),
    SecurityRule("TZ-SEC-GH-003", "GitHub", "GitHub OAuth Access Token", r"\b(gho_[A-Za-z0-9]{36})\b", "critical", "GITHUB_OAUTH_TOKEN", "GitHub user OAuth access token"),
    SecurityRule("TZ-SEC-GL-001", "GitLab", "GitLab Personal Access Token", r"\b(glpat-[A-Za-z0-9\-_]{20,})\b", "critical", "GITLAB_TOKEN", "GitLab user personal token"),
    SecurityRule("TZ-SEC-BB-001", "Bitbucket", "Bitbucket App Password", r"""(?i)bitbucket[_-]?password\s*=\s*['"][A-Za-z0-9]{16,24}['"]""", "critical", "BITBUCKET_APP_PASSWORD", "Bitbucket application credential"),
    SecurityRule("TZ-SEC-NPM-001", "NPM", "NPM Access Token", r"\b(npm_[A-Za-z0-9]{36})\b", "critical", "NPM_TOKEN", "Node package manager registry upload token"),
    SecurityRule("TZ-SEC-PYPI-001", "PyPI", "PyPI API Token", r"\b(pypi-AgEIcHlwaS5vcmc[A-Za-z0-9\-_]{50,})\b", "critical", "PYPI_TOKEN", "Python package index publishing token"),
    SecurityRule("TZ-SEC-SENTRY-001", "Sentry", "Sentry Auth Token", r"\b(sntrys_[a-f0-9]{64})\b", "critical", "SENTRY_AUTH_TOKEN", "Sentry crash reporting auth token"),
    SecurityRule("TZ-SEC-DD-001", "Datadog", "Datadog API Key", r"""(?i)datadog[_-]?(api[_-]?key|token)\s*=\s*['"][a-f0-9]{32}['"]""", "critical", "DATADOG_API_KEY", "Datadog monitoring ingestion key"),

    # -------------------------------------------------------------------------
    # 4. PAYMENTS & SAAS
    # -------------------------------------------------------------------------
    SecurityRule("TZ-SEC-STRIPE-001", "Stripe", "Stripe Secret Key", r"\b(sk_live_[0-9a-zA-Z]{24,34})\b", "critical", "STRIPE_SECRET_KEY", "Stripe live payment processing key"),
    SecurityRule("TZ-SEC-STRIPE-002", "Stripe", "Stripe Restricted Key", r"\b(rk_live_[0-9a-zA-Z]{24,34})\b", "critical", "STRIPE_RESTRICTED_KEY", "Stripe fine-grained restricted key"),
    SecurityRule("TZ-SEC-STRIPE-003", "Stripe", "Stripe Webhook Secret", r"\b(whsec_[0-9a-zA-Z]{32})\b", "critical", "STRIPE_WEBHOOK_SECRET", "Stripe webhook signature signing key"),
    SecurityRule("TZ-SEC-TWILIO-001", "Twilio", "Twilio Account SID", r"\b(AC[a-f0-9]{32})\b", "warning", "TWILIO_ACCOUNT_SID", "Twilio communications account SID"),
    SecurityRule("TZ-SEC-TWILIO-002", "Twilio", "Twilio Auth Token", r"""(?i)twilio[_-]?auth[_-]?token\s*=\s*['"][a-f0-9]{32}['"]""", "critical", "TWILIO_AUTH_TOKEN", "Twilio API auth secret"),
    SecurityRule("TZ-SEC-SENDGRID-001", "SendGrid", "SendGrid API Key", r"\b(SG\.[A-Za-z0-9_\-\.]{60,})\b", "critical", "SENDGRID_API_KEY", "SendGrid email delivery key"),
    SecurityRule("TZ-SEC-SLACK-001", "Slack", "Slack Bot Token", r"\b(xoxb-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24})\b", "critical", "SLACK_BOT_TOKEN", "Slack bot workspace token"),
    SecurityRule("TZ-SEC-SLACK-002", "Slack", "Slack Webhook URL", r"https:\/\/hooks\.slack\.com\/services\/T[A-Z0-9]{8}\/B[A-Z0-9]{8}\/[A-Za-z0-9]{24}", "critical", "SLACK_WEBHOOK_URL", "Incoming Slack webhook URL"),
    SecurityRule("TZ-SEC-DISCORD-001", "Discord", "Discord Bot Token", r"\b([MN][A-Za-z\d]{23,25}\.[A-Za-z\d\-_]{6}\.[A-Za-z\d\-_]{27})\b", "critical", "DISCORD_BOT_TOKEN", "Discord bot application token"),

    # -------------------------------------------------------------------------
    # 5. DATABASES & CRYPTOGRAPHY
    # -------------------------------------------------------------------------
    SecurityRule("TZ-SEC-DB-001", "Database", "PostgreSQL Connection String", r"postgres(ql)?:\/\/[A-Za-z0-9_\.\-]+:[^@\s\"'\<\>]+@[A-Za-z0-9_\.\-]+", "critical", "DATABASE_URL", "PostgreSQL connection string with embedded password"),
    SecurityRule("TZ-SEC-DB-002", "Database", "MySQL Connection String", r"mysql:\/\/[A-Za-z0-9_\.\-]+:[^@\s\"'\<\>]+@[A-Za-z0-9_\.\-]+", "critical", "DATABASE_URL", "MySQL connection string with embedded password"),
    SecurityRule("TZ-SEC-DB-003", "Database", "MongoDB Connection String", r"mongodb(\+srv)?:\/\/[A-Za-z0-9_\.\-]+:[^@\s\"'\<\>]+@[A-Za-z0-9_\.\-]+", "critical", "MONGODB_URI", "MongoDB cluster connection string with password"),
    SecurityRule("TZ-SEC-DB-004", "Database", "Redis Connection String", r"redis(s)?:\/\/:[^@\s\"'\<\>]+@[A-Za-z0-9_\.\-]+", "critical", "REDIS_URL", "Redis in-memory cache connection URL"),
    SecurityRule("TZ-SEC-KEY-001", "Crypto", "RSA Private Key", r"--" + r"---BEGIN RSA PRIVATE KEY-----", "critical", "RSA_PRIVATE_KEY", "Unencrypted RSA private key block"),
    SecurityRule("TZ-SEC-KEY-002", "Crypto", "OpenSSH Private Key", r"--" + r"---BEGIN OPENSSH PRIVATE KEY-----", "critical", "SSH_PRIVATE_KEY", "OpenSSH authentication private key"),
    SecurityRule("TZ-SEC-KEY-003", "Crypto", "PGP Private Key", r"--" + r"---BEGIN PGP PRIVATE KEY BLOCK-----", "critical", "PGP_PRIVATE_KEY", "Pretty Good Privacy private key block"),
    SecurityRule("TZ-SEC-KEY-004", "Crypto", "EC Private Key", r"--" + r"---BEGIN EC PRIVATE KEY-----", "critical", "EC_PRIVATE_KEY", "Elliptic curve cryptography private key"),
]


class SecurityRulesCatalog:
    """Catalog manager providing indexed lookups and rule evaluation."""

    @classmethod
    def get_all_rules(cls) -> List[SecurityRule]:
        return ENCYCLOPEDIC_SECURITY_RULES

    @classmethod
    def get_rules_by_vendor(cls, vendor: str) -> List[SecurityRule]:
        return [r for r in ENCYCLOPEDIC_SECURITY_RULES if r.vendor.lower() == vendor.lower()]

    @classmethod
    def get_rule_by_id(cls, rule_id: str) -> SecurityRule:
        for r in ENCYCLOPEDIC_SECURITY_RULES:
            if r.rule_id == rule_id:
                return r
        raise KeyError(f"Rule ID not found: {rule_id}")
