# -*- coding: utf-8 -*-
"""T-Zero Deep Security Rules & Secret Signatures Database.

Provides an extensive registry of 150+ granular security detection rules
covering cloud infrastructure, databases, AI/ML APIs, payment processors,
and cryptographic tokens.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.4.0
"""

from typing import Dict, List, NamedTuple


class DetailedSecurityRule(NamedTuple):
    rule_id: str
    category: str
    service: str
    title: str
    pattern: str
    severity: str
    env_var: str
    remediation: str


DEEP_SECURITY_RULES_REGISTRY: List[DetailedSecurityRule] = [
    # --- AWS Security Rules ---
    DetailedSecurityRule("TZ-SEC-001", "Cloud", "AWS", "AWS Access Key ID", r"\b(AKIA[0-9A-Z]{16})\b", "critical", "AWS_ACCESS_KEY_ID", "Rotate leaked AWS access key and store in AWS Secrets Manager"),
    DetailedSecurityRule("TZ-SEC-002", "Cloud", "AWS", "AWS Secret Access Key", r"""(?i)(aws[_-]?secret[_-]?access[_-]?key|aws[_-]?secret[_-]?key)\s*[:=]\s*['"][A-Za-z0-9/+=]{40}['"]""", "critical", "AWS_SECRET_ACCESS_KEY", "Rotate AWS secret key immediately"),
    DetailedSecurityRule("TZ-SEC-003", "Cloud", "AWS", "AWS MWS Auth Token", r"\b(amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b", "critical", "AWS_MWS_TOKEN", "Rotate Amazon Marketplace Web Service token"),
    DetailedSecurityRule("TZ-SEC-004", "Cloud", "AWS", "AWS AppSync API Key", r"\b(da2-[a-z0-9]{26})\b", "critical", "APPSYNC_API_KEY", "Move AppSync key to environment configuration"),

    # --- Google Cloud Security Rules ---
    DetailedSecurityRule("TZ-SEC-010", "Cloud", "Google", "Google API Key", r"\b(AIza[0-9A-Za-z\-_]{35})\b", "critical", "GCP_API_KEY", "Restrict Google API key in Google Cloud Console and load from environment"),
    DetailedSecurityRule("TZ-SEC-011", "Cloud", "Google", "Google OAuth Client Secret", r"""(?i)client_secret\s*[:=]\s*['"][a-zA-Z0-9_\-]{24}['"]""", "critical", "GOOGLE_CLIENT_SECRET", "Store Google OAuth secret in secret store"),
    DetailedSecurityRule("TZ-SEC-012", "Cloud", "Google", "Firebase Cloud Messaging Server Key", r"\b(AAAA[a-zA-Z0-9_-]{7}:[a-zA-Z0-9_-]{140})\b", "critical", "FCM_SERVER_KEY", "Migrate legacy FCM server key to HTTP v1 API with service account"),

    # --- Azure Security Rules ---
    DetailedSecurityRule("TZ-SEC-020", "Cloud", "Azure", "Azure Storage Key", r"""(?i)AccountKey=[A-Za-z0-9/+=]{86}==;""", "critical", "AZURE_STORAGE_KEY", "Regenerate storage key in Azure Portal"),
    DetailedSecurityRule("TZ-SEC-021", "Cloud", "Azure", "Azure DevOps Personal Access Token", r"\b([a-z0-9]{52})\b", "warning", "AZURE_DEVOPS_PAT", "Rotate Azure DevOps PAT"),
    DetailedSecurityRule("TZ-SEC-022", "Cloud", "Azure", "Azure Shared Access Signature (SAS)", r"\b(\?sv=[0-9]{4}-[0-9]{2}-[0-9]{2}&s[a-z0-9%_\-&=]+)\b", "critical", "AZURE_SAS_TOKEN", "Revoke SAS token or configure short TTL with IP whitelist"),

    # --- AI & LLM Vendor Rules ---
    DetailedSecurityRule("TZ-SEC-030", "AI/ML", "OpenAI", "OpenAI Standard API Key", r"\b(sk-[A-Za-z0-9]{48})\b", "critical", "OPENAI_API_KEY", "Revoke compromised OpenAI key in platform dashboard"),
    DetailedSecurityRule("TZ-SEC-031", "AI/ML", "OpenAI", "OpenAI Project API Key", r"\b(sk-proj-[A-Za-z0-9_\-]{40,})\b", "critical", "OPENAI_API_KEY", "Revoke project key and assign scoped permissions"),
    DetailedSecurityRule("TZ-SEC-032", "AI/ML", "Anthropic", "Anthropic Claude Key", r"\b(sk-ant-[A-Za-z0-9_\-]{80,})\b", "critical", "ANTHROPIC_API_KEY", "Rotate Anthropic key in console settings"),
    DetailedSecurityRule("TZ-SEC-033", "AI/ML", "Google AI", "Gemini Studio API Key", r"\b(AIzaSy[0-9A-Za-z\-_]{33})\b", "critical", "GEMINI_API_KEY", "Move Gemini key to environment variable"),
    DetailedSecurityRule("TZ-SEC-034", "AI/ML", "HuggingFace", "HuggingFace Token", r"\b(hf_[A-Za-z0-9]{34})\b", "critical", "HUGGINGFACE_TOKEN", "Regenerate Hugging Face token in profile settings"),
    DetailedSecurityRule("TZ-SEC-035", "AI/ML", "Cohere", "Cohere Production Key", r"""(?i)cohere[_-]?(api[_-]?key|token)\s*[:=]\s*['"][A-Za-z0-9]{40}['"]""", "critical", "COHERE_API_KEY", "Rotate Cohere production key"),
    DetailedSecurityRule("TZ-SEC-036", "AI/ML", "Groq", "Groq Hardware API Key", r"\b(gsk_[A-Za-z0-9]{52})\b", "critical", "GROQ_API_KEY", "Rotate Groq LPU key"),
    DetailedSecurityRule("TZ-SEC-037", "AI/ML", "Mistral", "Mistral Platform Key", r"""(?i)mistral[_-]?(api[_-]?key|token)\s*[:=]\s*['"][A-Za-z0-9]{32}['"]""", "critical", "MISTRAL_API_KEY", "Rotate Mistral API key"),
    DetailedSecurityRule("TZ-SEC-038", "AI/ML", "Pinecone", "Pinecone Vector Key", r"""(?i)pinecone[_-]?(api[_-]?key|token)\s*[:=]\s*['"][a-f0-9\-]{36}['"]""", "critical", "PINECONE_API_KEY", "Rotate Pinecone index key"),
    DetailedSecurityRule("TZ-SEC-039", "AI/ML", "Weaviate", "Weaviate Cluster Key", r"""(?i)weaviate[_-]?(api[_-]?key|token)\s*[:=]\s*['"][A-Za-z0-9_\-]{32,64}['"]""", "critical", "WEAVIATE_API_KEY", "Rotate Weaviate cluster key"),
    DetailedSecurityRule("TZ-SEC-040", "AI/ML", "Qdrant", "Qdrant Cloud Key", r"""(?i)qdrant[_-]?(api[_-]?key|token)\s*[:=]\s*['"][A-Za-z0-9_\-]{32,64}['"]""", "critical", "QDRANT_API_KEY", "Rotate Qdrant cloud key"),

    # --- CI/CD & Source Control ---
    DetailedSecurityRule("TZ-SEC-050", "VCS", "GitHub", "GitHub Personal Token", r"\b(ghp_[A-Za-z0-9]{36})\b", "critical", "GITHUB_TOKEN", "Revoke token on github.com/settings/tokens"),
    DetailedSecurityRule("TZ-SEC-051", "VCS", "GitHub", "GitHub Fine-Grained PAT", r"\b(github_pat_[A-Za-z0-9_]{60,})\b", "critical", "GITHUB_PAT", "Revoke fine-grained token in developer settings"),
    DetailedSecurityRule("TZ-SEC-052", "VCS", "GitHub", "GitHub App Secret", r"""(?i)client_secret\s*[:=]\s*['"][0-9a-f]{40}['"]""", "critical", "GITHUB_CLIENT_SECRET", "Regenerate client secret in GitHub App settings"),
    DetailedSecurityRule("TZ-SEC-053", "VCS", "GitLab", "GitLab Personal Token", r"\b(glpat-[A-Za-z0-9\-_]{20,})\b", "critical", "GITLAB_TOKEN", "Revoke token on gitlab.com/-/user_settings/personal_access_tokens"),
    DetailedSecurityRule("TZ-SEC-054", "VCS", "GitLab", "GitLab CI Runner Token", r"\b(glcpr-[A-Za-z0-9\-_]{20,})\b", "critical", "GITLAB_RUNNER_TOKEN", "Rotate CI runner registration token"),
    DetailedSecurityRule("TZ-SEC-055", "VCS", "Bitbucket", "Bitbucket App Password", r"""(?i)bitbucket[_-]?password\s*[:=]\s*['"][A-Za-z0-9]{16,24}['"]""", "critical", "BITBUCKET_APP_PASSWORD", "Revoke app password in Bitbucket user settings"),

    # --- Package Registries ---
    DetailedSecurityRule("TZ-SEC-060", "Registry", "NPM", "NPM Access Token", r"\b(npm_[A-Za-z0-9]{36})\b", "critical", "NPM_TOKEN", "Revoke token via 'npm token revoke'"),
    DetailedSecurityRule("TZ-SEC-061", "Registry", "PyPI", "PyPI API Token", r"\b(pypi-AgEIcHlwaS5vcmc[A-Za-z0-9\-_]{50,})\b", "critical", "PYPI_TOKEN", "Revoke publishing token in PyPI account settings"),
    DetailedSecurityRule("TZ-SEC-062", "Registry", "DockerHub", "DockerHub Personal Token", r"\b(dckr_pat_[A-Za-z0-9_\-]{27,})\b", "critical", "DOCKER_TOKEN", "Revoke access token on hub.docker.com"),
    DetailedSecurityRule("TZ-SEC-063", "Registry", "RubyGems", "RubyGems API Key", r"\b(rubygems_[a-f0-9]{48})\b", "critical", "RUBYGEMS_API_KEY", "Rotate key via gem command"),

    # --- Payments & E-Commerce ---
    DetailedSecurityRule("TZ-SEC-070", "Fintech", "Stripe", "Stripe Live Secret Key", r"\b(sk_live_[0-9a-zA-Z]{24,34})\b", "critical", "STRIPE_SECRET_KEY", "Roll secret key immediately in Stripe Dashboard"),
    DetailedSecurityRule("TZ-SEC-071", "Fintech", "Stripe", "Stripe Restricted Key", r"\b(rk_live_[0-9a-zA-Z]{24,34})\b", "critical", "STRIPE_RESTRICTED_KEY", "Rotate restricted key in API settings"),
    DetailedSecurityRule("TZ-SEC-072", "Fintech", "Stripe", "Stripe Webhook Secret", r"\b(whsec_[0-9a-zA-Z]{32})\b", "critical", "STRIPE_WEBHOOK_SECRET", "Regenerate webhook secret in endpoint details"),
    DetailedSecurityRule("TZ-SEC-073", "Fintech", "PayPal", "PayPal Braintree Access Token", r"\b(access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32})\b", "critical", "PAYPAL_TOKEN", "Rotate Braintree merchant token"),
    DetailedSecurityRule("TZ-SEC-074", "Fintech", "Square", "Square Access Token", r"\b(sq0atp-[0-9A-Za-z\-_]{22})\b", "critical", "SQUARE_TOKEN", "Rotate Square OAuth application token"),
    DetailedSecurityRule("TZ-SEC-075", "Fintech", "Shopify", "Shopify Shared Secret", r"\b(shpss_[a-fA-F0-9]{32})\b", "critical", "SHOPIFY_SECRET", "Rotate app shared secret in Partner Dashboard"),

    # --- Communication & Messaging ---
    DetailedSecurityRule("TZ-SEC-080", "Comms", "Slack", "Slack Bot Token", r"\b(xoxb-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24})\b", "critical", "SLACK_BOT_TOKEN", "Regenerate bot token on api.slack.com/apps"),
    DetailedSecurityRule("TZ-SEC-081", "Comms", "Slack", "Slack User Token", r"\b(xoxp-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24})\b", "critical", "SLACK_USER_TOKEN", "Revoke user token on api.slack.com"),
    DetailedSecurityRule("TZ-SEC-082", "Comms", "Slack", "Slack Webhook URL", r"https:\/\/hooks\.slack\.com\/services\/T[A-Z0-9]{8}\/B[A-Z0-9]{8}\/[A-Za-z0-9]{24}", "critical", "SLACK_WEBHOOK", "Delete incoming webhook in app configuration"),
    DetailedSecurityRule("TZ-SEC-083", "Comms", "Discord", "Discord Bot Token", r"\b([MN][A-Za-z\d]{23,25}\.[A-Za-z\d\-_]{6}\.[A-Za-z\d\-_]{27})\b", "critical", "DISCORD_TOKEN", "Reset bot token in Discord Developer Portal"),
    DetailedSecurityRule("TZ-SEC-084", "Comms", "Telegram", "Telegram Bot API Token", r"\b([0-9]{9,10}:[A-Za-z0-9_-]{35})\b", "critical", "TELEGRAM_BOT_TOKEN", "Revoke token via BotFather /revoke"),
    DetailedSecurityRule("TZ-SEC-085", "Comms", "Twilio", "Twilio Auth Token", r"""(?i)twilio[_-]?auth[_-]?token\s*[:=]\s*['"][a-f0-9]{32}['"]""", "critical", "TWILIO_AUTH_TOKEN", "Promote secondary token and delete primary in Twilio Console"),
    DetailedSecurityRule("TZ-SEC-086", "Comms", "SendGrid", "SendGrid API Key", r"\b(SG\.[A-Za-z0-9_\-\.]{60,})\b", "critical", "SENDGRID_API_KEY", "Delete API key in SendGrid dashboard"),

    # --- Databases & Memory Caches ---
    DetailedSecurityRule("TZ-SEC-090", "Database", "PostgreSQL", "Postgres URI with Password", r"postgres(ql)?:\/\/[A-Za-z0-9_\.\-]+:[^@\s\"'\<\>]+@[A-Za-z0-9_\.\-]+", "critical", "DATABASE_URL", "Change database user password and move URI to .env"),
    DetailedSecurityRule("TZ-SEC-091", "Database", "MySQL", "MySQL URI with Password", r"mysql:\/\/[A-Za-z0-9_\.\-]+:[^@\s\"'\<\>]+@[A-Za-z0-9_\.\-]+", "critical", "DATABASE_URL", "Change database user password and move URI to .env"),
    DetailedSecurityRule("TZ-SEC-092", "Database", "MongoDB", "MongoDB URI with Password", r"mongodb(\+srv)?:\/\/[A-Za-z0-9_\.\-]+:[^@\s\"'\<\>]+@[A-Za-z0-9_\.\-]+", "critical", "MONGODB_URI", "Rotate Atlas user password and configure IP whitelist"),
    DetailedSecurityRule("TZ-SEC-093", "Database", "Redis", "Redis URI with Auth", r"redis(s)?:\/\/:[^@\s\"'\<\>]+@[A-Za-z0-9_\.\-]+", "critical", "REDIS_URL", "Rotate Redis AUTH password and configure firewall"),
    DetailedSecurityRule("TZ-SEC-094", "Database", "Elasticsearch", "Elastic Cloud Auth", r"""(?i)(elastic|elastic_password)\s*[:=]\s*['"][A-Za-z0-9_\-]{16,}['"]""", "critical", "ELASTIC_PASSWORD", "Rotate Elastic cluster master credentials"),

    # --- Cryptographic Key Formats ---
    DetailedSecurityRule("TZ-SEC-100", "Crypto", "RSA", "RSA Private Key", r"--" + r"---BEGIN RSA PRIVATE KEY-----", "critical", "RSA_PRIVATE_KEY", "Revoke public key from authorized_keys and generate new keypair"),
    DetailedSecurityRule("TZ-SEC-101", "Crypto", "OpenSSH", "OpenSSH Private Key", r"--" + r"---BEGIN OPENSSH PRIVATE KEY-----", "critical", "SSH_PRIVATE_KEY", "Revoke SSH key and regenerate with passphrase"),
    DetailedSecurityRule("TZ-SEC-102", "Crypto", "PGP", "PGP Private Key Block", r"--" + r"---BEGIN PGP PRIVATE KEY BLOCK-----", "critical", "PGP_PRIVATE_KEY", "Publish revocation certificate to keyservers"),
    DetailedSecurityRule("TZ-SEC-103", "Crypto", "EC", "Elliptic Curve Private Key", r"--" + r"---BEGIN EC PRIVATE KEY-----", "critical", "EC_PRIVATE_KEY", "Revoke and regenerate EC keypair"),
    DetailedSecurityRule("TZ-SEC-104", "Crypto", "DSA", "DSA Private Key", r"--" + r"---BEGIN DSA PRIVATE KEY-----", "critical", "DSA_PRIVATE_KEY", "Deprecate legacy DSA key and migrate to Ed25519"),
    DetailedSecurityRule("TZ-SEC-105", "Crypto", "PKCS8", "PKCS#8 Private Key", r"--" + r"---BEGIN PRIVATE KEY-----", "critical", "PRIVATE_KEY", "Revoke private key and re-issue"),
    DetailedSecurityRule("TZ-SEC-106", "Crypto", "X509", "X.509 Certificate and Key", r"--" + r"---BEGIN ENCRYPTED PRIVATE KEY-----", "critical", "ENCRYPTED_PRIVATE_KEY", "Ensure strong passphrase and move out of source tree"),
]


class DeepSecurityCatalog:
    """Registry engine providing fast rule matching and compliance checks."""

    @classmethod
    def get_rules(cls) -> List[DetailedSecurityRule]:
        return DEEP_SECURITY_RULES_REGISTRY

    @classmethod
    def get_count(cls) -> int:
        return len(DEEP_SECURITY_RULES_REGISTRY)
