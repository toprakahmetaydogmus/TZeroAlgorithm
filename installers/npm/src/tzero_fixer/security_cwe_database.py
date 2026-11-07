# -*- coding: utf-8 -*-
"""
T-Zero Security CWE & OWASP Vulnerability Taxonomy
=================================================
Exhaustive vulnerability mapping, remediation encyclopedia, and AST rule engine.
Maps Common Weakness Enumerations (CWE), OWASP Top 10, and CIS Critical Security Controls
to specific static analysis patterns and surgical remediation recipes.

Covers:
  - Injection Flaws (CWE-89 SQL Injection, CWE-78 OS Command Injection, CWE-79 XSS)
  - Broken Access Control & Path Traversal (CWE-22 Path Traversal, CWE-284 Improper Access)
  - Cryptographic Failures & Hardcoded Credentials (CWE-798, CWE-259, CWE-327 Broken Crypto)
  - Insecure Deserialization (CWE-502 Untrusted Deserialization in Python/Java/Node)
  - Security Misconfiguration (CWE-16, CWE-1004 Missing Cookie HttpOnly, CWE-942 CORS)
  - Software & Data Integrity Failures (CWE-494 Missing Integrity Check, CWE-829 Unpinned Deps)

Author: Siber Akademi T-Zero R&D Team
License: MIT (100% Free, Local Offline, Zero-Leak)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Any


@dataclass
class CWERuleDefinition:
    """Taxonomy definition for a specific Common Weakness Enumeration."""
    cwe_id: str
    owasp_category: str
    name: str
    description: str
    impact: str
    affected_languages: List[str]
    detection_heuristic: str
    remediation_strategy: str
    safe_code_pattern: str
    unsafe_code_pattern: str
    cvss_score: float = 7.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CWESecurityDatabase:
    """Master registry of security weaknesses and automated patch strategies."""

    VULNERABILITIES: List[CWERuleDefinition] = [
        # ---------------------------------------------------------------------
        # 1. INJECTION FLAWS (A03:2021 - Injection)
        # ---------------------------------------------------------------------
        CWERuleDefinition(
            cwe_id="CWE-89",
            owasp_category="A03:2021-Injection",
            name="SQL Injection (SQLi) via Dynamic Query Construction",
            description="Software constructs all or part of an SQL command using untrusted input from an upstream component without proper neutralization or parameterization.",
            impact="Unauthorized reading of sensitive data, modification of database contents, administrative execution of database functions.",
            affected_languages=["Python", "JavaScript", "TypeScript", "Go", "Rust", "PHP"],
            detection_heuristic="AST Call node to execute(), raw(), query() where SQL string is formatted with f-string, format(), or '%' operator.",
            remediation_strategy="Replace string formatting with parameterized query bind variables (e.g. cursor.execute('SELECT * FROM users WHERE id = %s', (uid,))).",
            safe_code_pattern="cursor.execute('SELECT * FROM users WHERE username = %s', (username,))",
            unsafe_code_pattern="cursor.execute(f'SELECT * FROM users WHERE username = \"{username}\"')",
            cvss_score=9.8,
        ),
        CWERuleDefinition(
            cwe_id="CWE-78",
            owasp_category="A03:2021-Injection",
            name="OS Command Injection via Shell Interpolation",
            description="The product constructs an OS command using externally-influenced input without neutralizing special elements that could modify the intended command.",
            impact="Arbitrary command execution in the context of the running application process; full host compromise.",
            affected_languages=["Python", "Node.js", "Ruby", "Go", "Shell"],
            detection_heuristic="Call to subprocess.Popen, os.system, exec, or child_process.exec with shell=True and dynamic arguments.",
            remediation_strategy="Pass command and arguments as a structured list with shell=False; sanitize inputs with shlex.quote() if shell is strictly necessary.",
            safe_code_pattern="subprocess.run(['ls', '-la', target_dir], shell=False, check=True)",
            unsafe_code_pattern="os.system('ls -la ' + user_input)",
            cvss_score=9.8,
        ),
        CWERuleDefinition(
            cwe_id="CWE-79",
            owasp_category="A03:2021-Injection",
            name="Improper Neutralization of Input During Web Page Generation (XSS)",
            description="The product does not neutralize or incorrectly neutralizes user-controllable input before placing it in output that is used as a webpage.",
            impact="Execution of malicious client-side JavaScript, cookie theft, session hijacking, defacement.",
            affected_languages=["JavaScript", "TypeScript", "HTML", "Python"],
            detection_heuristic="Use of innerHTML, dangerouslySetInnerHTML, v-html without DOMPurify or context-aware HTML escaping.",
            remediation_strategy="Use textContent or framework data binding; sanitize dynamic HTML with DOMPurify or bleach before rendering.",
            safe_code_pattern="element.textContent = userComment;",
            unsafe_code_pattern="element.innerHTML = '<div>' + userComment + '</div>';",
            cvss_score=7.2,
        ),
        CWERuleDefinition(
            cwe_id="CWE-77",
            owasp_category="A03:2021-Injection",
            name="Improper Neutralization of Special Elements used in a Command",
            description="The product constructs a command string with untrusted parameters without validating or escaping command delimiters.",
            impact="Execution of unauthorized commands, traversal of system boundaries.",
            affected_languages=["Python", "Shell", "Perl"],
            detection_heuristic="String concatenation with pipes (|), semicolons (;), or ampersands (&) passed to system command executors.",
            remediation_strategy="Use strictly typed APIs that accept argument lists rather than strings; enforce strict input regex whitelisting.",
            safe_code_pattern="subprocess.Popen(['ping', '-c', '1', ip_address])",
            unsafe_code_pattern="os.system('ping -c 1 ' + ip_address)",
            cvss_score=8.8,
        ),

        # ---------------------------------------------------------------------
        # 2. BROKEN ACCESS CONTROL & PATH TRAVERSAL (A01:2021)
        # ---------------------------------------------------------------------
        CWERuleDefinition(
            cwe_id="CWE-22",
            owasp_category="A01:2021-Broken Access Control",
            name="Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal')",
            description="The product uses external input to construct a pathname that should be within a restricted directory, but it does not properly neutralize '../' sequences.",
            impact="Arbitrary file reading (sensitive configs, /etc/passwd, private keys), arbitrary file overwrite.",
            affected_languages=["Python", "Node.js", "Go", "Rust", "Java"],
            detection_heuristic="os.path.join or Path() constructor directly consuming request query parameters or filename headers without resolve() boundary check.",
            remediation_strategy="Resolve canonical path using Path(target).resolve() and verify target.startswith(allowed_root).",
            safe_code_pattern="safe_path = (BASE_DIR / user_filename).resolve()\nif not str(safe_path).startswith(str(BASE_DIR)):\n    raise PermissionError()",
            unsafe_code_pattern="with open(os.path.join('/uploads', user_filename), 'rb') as f:\n    data = f.read()",
            cvss_score=8.6,
        ),
        CWERuleDefinition(
            cwe_id="CWE-284",
            owasp_category="A01:2021-Broken Access Control",
            name="Improper Access Control and Missing Authorization Check",
            description="The product does not restrict or incorrectly restricts access to a resource from an unauthorized actor.",
            impact="Horizontal and vertical privilege escalation, unauthorized data modification.",
            affected_languages=["All Frameworks (Django, FastAPI, Express, Spring)"],
            detection_heuristic="Endpoint handlers without authentication or authorization decorator (e.g. @login_required, @depends(get_current_user)).",
            remediation_strategy="Enforce centralized middleware or route-level dependency injection for permission checking on all state-mutating endpoints.",
            safe_code_pattern="@router.delete('/user/{uid}')\ndef delete_user(uid: str, current_user = Depends(require_admin)):\n    ...",
            unsafe_code_pattern="@router.delete('/user/{uid}')\ndef delete_user(uid: str):\n    db.delete_user(uid)",
            cvss_score=8.5,
        ),

        # ---------------------------------------------------------------------
        # 3. CRYPTOGRAPHIC FAILURES & HARDCODED CREDENTIALS (A02:2021)
        # ---------------------------------------------------------------------
        CWERuleDefinition(
            cwe_id="CWE-798",
            owasp_category="A02:2021-Cryptographic Failures",
            name="Use of Hardcoded Credentials in Source Code",
            description="The product contains hardcoded credentials, such as a password or cryptographic key, which it uses for authentication, encryption, or outbound communications.",
            impact="Exposure of entire infrastructure upon repository leak, impersonation of services, unrevocable access.",
            affected_languages=["All Languages"],
            detection_heuristic="High-entropy string matching provider signatures (AKIA*, sk-*, ghp_*, AIzaSy*, etc.) assigned to variables in code.",
            remediation_strategy="Extract secret into environment variables or secrets manager (AWS Secrets Manager, HashiCorp Vault); add file to .gitignore.",
            safe_code_pattern="api_key = os.environ.get('STRIPE_SECRET_KEY')",
            unsafe_code_pattern="api_key = '" + "sk_live_" + "51AbcdEfgh12345678901234567890'",
            cvss_score=9.8,
        ),
        CWERuleDefinition(
            cwe_id="CWE-327",
            owasp_category="A02:2021-Cryptographic Failures",
            name="Use of a Broken or Risky Cryptographic Algorithm (MD5 / SHA1)",
            description="The product uses a broken or cryptographically weakened algorithm for data integrity, hashing, or signatures.",
            impact="Collision attacks, preimage attacks, forgery of digital signatures.",
            affected_languages=["Python", "Java", "Go", "Node.js"],
            detection_heuristic="Calls to hashlib.md5(), hashlib.sha1(), or crypto.createHash('md5') used for security purposes.",
            remediation_strategy="Migrate to modern SHA-256 (hashlib.sha256()) or SHA-3, or Argon2id/bcrypt for password hashing.",
            safe_code_pattern="token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()",
            unsafe_code_pattern="token_hash = hashlib.md5(token.encode('utf-8')).hexdigest()",
            cvss_score=7.4,
        ),
        CWERuleDefinition(
            cwe_id="CWE-338",
            owasp_category="A02:2021-Cryptographic Failures",
            name="Use of Cryptographically Weak Pseudo-Random Number Generator (PRNG)",
            description="The product uses a pseudo-random number generator that is not cryptographically secure to produce values that require high unpredictability (tokens, salts, keys).",
            impact="Predictable session identifiers, tokens, and cryptographic keys.",
            affected_languages=["Python", "JavaScript", "Java"],
            detection_heuristic="Use of standard random module (random.random(), random.randint()) to generate security-sensitive tokens.",
            remediation_strategy="Use secrets module in Python (secrets.token_hex(), secrets.token_urlsafe()) or crypto.getRandomValues() in JavaScript.",
            safe_code_pattern="reset_token = secrets.token_urlsafe(32)",
            unsafe_code_pattern="reset_token = str(random.randint(100000, 999999))",
            cvss_score=7.5,
        ),

        # ---------------------------------------------------------------------
        # 4. INSECURE DESERIALIZATION (A08:2021)
        # ---------------------------------------------------------------------
        CWERuleDefinition(
            cwe_id="CWE-502",
            owasp_category="A08:2021-Software and Data Integrity Failures",
            name="Deserialization of Untrusted Data (pickle / yaml.load)",
            description="The product deserializes untrusted data without sufficiently verifying that the resulting data will be valid.",
            impact="Arbitrary code execution on host machine during object reconstruction.",
            affected_languages=["Python", "Java", "PHP", "Node.js"],
            detection_heuristic="Call to pickle.loads, pickle.load, yaml.load(stream), or marshal.loads on network or file input.",
            remediation_strategy="Use safe data interchange formats (JSON, Protocol Buffers); if YAML is required, use yaml.safe_load().",
            safe_code_pattern="data = yaml.safe_load(yaml_content)",
            unsafe_code_pattern="data = yaml.load(yaml_content) # default loader in older PyYAML",
            cvss_score=9.8,
        ),

        # ---------------------------------------------------------------------
        # 5. SECURITY MISCONFIGURATION & TIMING ATTACKS (A05:2021)
        # ---------------------------------------------------------------------
        CWERuleDefinition(
            cwe_id="CWE-208",
            owasp_category="A02:2021-Cryptographic Failures",
            name="Observable Timing Discrepancy (Timing Attack on Secrets)",
            description="The product performs comparisons of secrets using standard equality operators (==) which terminate early on first mismatched byte.",
            impact="Side-channel recovery of passwords, HMAC tokens, or signature hashes via precision timing measurements.",
            affected_languages=["Python", "Node.js", "Go", "C++"],
            detection_heuristic="Direct '==' comparison between hash digests or secret authentication tokens.",
            remediation_strategy="Use constant-time comparison algorithms such as hmac.compare_digest() or crypto.timingSafeEqual().",
            safe_code_pattern="is_valid = hmac.compare_digest(user_token, expected_token)",
            unsafe_code_pattern="is_valid = (user_token == expected_token)",
            cvss_score=5.9,
        ),
        CWERuleDefinition(
            cwe_id="CWE-611",
            owasp_category="A05:2021-Security Misconfiguration",
            name="Improper Restriction of XML External Entity Reference ('XXE')",
            description="The product processes an XML document that can contain XML entities with URIs that resolve to documents outside the intended sphere of control.",
            impact="Disclosure of internal files, server-side request forgery (SSRF), denial of service (Billion Laughs attack).",
            affected_languages=["Python", "Java", "PHP", "C#"],
            detection_heuristic="Use of standard xml.etree or lxml parsers without disabling entity resolution (resolve_entities=False).",
            remediation_strategy="Use defusedxml package in Python or explicitly disable DTD processing and external entities in parser settings.",
            safe_code_pattern="from defusedxml.ElementTree import parse\ntree = parse(xml_file)",
            unsafe_code_pattern="import xml.etree.ElementTree as ET\ntree = ET.parse(xml_file)",
            cvss_score=8.2,
        ),
        CWERuleDefinition(
            cwe_id="CWE-918",
            owasp_category="A10:2021-Server-Side Request Forgery",
            name="Server-Side Request Forgery (SSRF)",
            description="The web server receives a user-supplied URL and makes an outbound HTTP request without validating destination IP against cloud metadata or private subnets.",
            impact="Extraction of AWS/GCP/Azure IAM instance metadata (169.254.169.254), internal port scanning, access to internal services.",
            affected_languages=["Python", "Node.js", "Go", "Java"],
            detection_heuristic="requests.get/post, httpx, or axios consuming unvalidated user-supplied URLs.",
            remediation_strategy="Parse URL host, resolve DNS, and block private RFC 1918 IPs (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.169.254).",
            safe_code_pattern="if is_safe_public_ip(url):\n    requests.get(url, timeout=5)",
            unsafe_code_pattern="requests.get(request.args.get('target_url'))",
            cvss_score=8.6,
        ),
        CWERuleDefinition(
            cwe_id="CWE-601",
            owasp_category="A01:2021-Broken Access Control",
            name="URL Redirection to Untrusted Site ('Open Redirect')",
            description="A web application accepts a user-controlled input that specifies a link to an external site, and uses that link in a Redirect response.",
            impact="Facilitates phishing campaigns appearing under trusted domain authority, credential harvesting.",
            affected_languages=["Python", "JavaScript", "TypeScript"],
            detection_heuristic="Direct redirect(next_url) or res.redirect(url) without domain whitelist validation.",
            remediation_strategy="Validate target against strict allowlist of relative paths (starting with single '/') or trusted domains.",
            safe_code_pattern="if url_is_relative(target):\n    return redirect(target)",
            unsafe_code_pattern="return redirect(request.args.get('next'))",
            cvss_score=6.1,
        ),
        CWERuleDefinition(
            cwe_id="CWE-434",
            owasp_category="A04:2021-Insecure Design",
            name="Unrestricted Upload of File with Dangerous Type",
            description="The software allows the attacker to upload or transfer files of dangerous types that can be directly executed within the server environment.",
            impact="Remote code execution via uploaded .php, .jsp, or executable scripts.",
            affected_languages=["Python", "Node.js", "PHP"],
            detection_heuristic="File upload handler trusting client-provided Content-Type or filename extension without mime inspection.",
            remediation_strategy="Validate file magic numbers using python-magic; randomize filename; store outside web root.",
            safe_code_pattern="safe_name = f'{uuid.uuid4().hex}.jpg'\nsave_file(safe_name)",
            unsafe_code_pattern="upload_file.save(upload_file.filename)",
            cvss_score=9.8,
        ),
        CWERuleDefinition(
            cwe_id="CWE-352",
            owasp_category="A01:2021-Broken Access Control",
            name="Cross-Site Request Forgery (CSRF)",
            description="The web application does not, or can not, verify whether a well-formed request was intentionally sent by the user who submitted the request.",
            impact="Unauthorized transactions, email changes, password resets executed on behalf of authenticated victims.",
            affected_languages=["All Web Frameworks"],
            detection_heuristic="State-changing POST/PUT/DELETE routes exempt from CSRF protection or lacking SameSite=Lax cookie attribute.",
            remediation_strategy="Use CSRF tokens with double-submit cookie pattern and set SameSite=Lax or Strict on session cookies.",
            safe_code_pattern="response.set_cookie('session', sid, samesite='lax', secure=True, httponly=True)",
            unsafe_code_pattern="response.set_cookie('session', sid) # missing samesite/secure/httponly",
            cvss_score=8.1,
        ),
        CWERuleDefinition(
            cwe_id="CWE-94",
            owasp_category="A03:2021-Injection",
            name="Improper Control of Generation of Code ('Code Injection')",
            description="The product constructs all or part of a code segment using externally-influenced input from an upstream component.",
            impact="Arbitrary code execution on application runtime.",
            affected_languages=["Python", "JavaScript", "PHP", "Ruby"],
            detection_heuristic="Calls to eval(), exec(), Function(), or compile() with user variables.",
            remediation_strategy="Avoid dynamic code generation; use lookup tables, strategy patterns, or safe AST interpreters.",
            safe_code_pattern="result = OPERATIONS[op_name](a, b)",
            unsafe_code_pattern="result = eval(f'{a} {op_name} {b}')",
            cvss_score=9.8,
        ),
        CWERuleDefinition(
            cwe_id="CWE-1333",
            owasp_category="A03:2021-Injection",
            name="Inefficient Regular Expression Complexity ('ReDoS')",
            description="The product uses a regular expression that can take polynomial or exponential time relative to input length on non-matching strings.",
            impact="CPU denial of service (thread exhaustion, 100% CPU lockup) on malformed inputs.",
            affected_languages=["Python", "JavaScript", "Go", "Java"],
            detection_heuristic="Nested quantifiers in regular expressions: (a+)+, ([a-zA-Z]+)*, (.*)*.",
            remediation_strategy="Eliminate nested repetitions; use atomic grouping, lookaheads, or re2 linear-time engine.",
            safe_code_pattern="re.compile(r'^[a-zA-Z0-9_-]{1,64}$') # linear time",
            unsafe_code_pattern="re.compile(r'^([a-zA-Z0-9]+)+$') # catastrophic backtracking",
            cvss_score=7.5,
        ),
        CWERuleDefinition(
            cwe_id="CWE-295",
            owasp_category="A02:2021-Cryptographic Failures",
            name="Improper Certificate Validation (SSL/TLS Verification Disabled)",
            description="The software does not validate, or incorrectly validates, a certificate provided by a remote peer during TLS handshake.",
            impact="Man-in-the-middle (MITM) eavesdropping and plaintext credential interception on public networks.",
            affected_languages=["Python", "Node.js", "Go"],
            detection_heuristic="requests.get/post with verify=False, or NODE_TLS_REJECT_UNAUTHORIZED='0'.",
            remediation_strategy="Always enable verify=True (default); supply enterprise CA bundle via REQUESTS_CA_BUNDLE if private PKI.",
            safe_code_pattern="requests.get(url, verify=True)",
            unsafe_code_pattern="requests.get(url, verify=False) # disables SSL verification",
            cvss_score=7.5,
        ),
        CWERuleDefinition(
            cwe_id="CWE-942",
            owasp_category="A05:2021-Security Misconfiguration",
            name="Permissive Cross-Origin Resource Sharing (CORS) Policy",
            description="The web application sets Access-Control-Allow-Origin: * alongside Access-Control-Allow-Credentials: true or echoes Origin header.",
            impact="Cross-origin extraction of sensitive user data from authenticated sessions.",
            affected_languages=["Python", "Node.js", "Go", "Java"],
            detection_heuristic="CORS middleware configured with allow_origins=['*'] and allow_credentials=True.",
            remediation_strategy="Explicitly whitelist authorized frontend origins; never allow wildcard origin with credentials.",
            safe_code_pattern="CORS(app, origins=['https://app.example.com'], supports_credentials=True)",
            unsafe_code_pattern="CORS(app, origins='*', supports_credentials=True)",
            cvss_score=6.5,
        ),
        CWERuleDefinition(
            cwe_id="CWE-1004",
            owasp_category="A05:2021-Security Misconfiguration",
            name="Sensitive Cookie Without 'HttpOnly' Flag",
            description="The software sets a cookie containing sensitive session tokens without the HttpOnly flag, allowing JavaScript access.",
            impact="Session hijacking via Cross-Site Scripting (XSS).",
            affected_languages=["All Web Frameworks"],
            detection_heuristic="set_cookie calls without httponly=True.",
            remediation_strategy="Always specify httponly=True for authentication cookies.",
            safe_code_pattern="response.set_cookie('token', jwt_token, httponly=True, secure=True)",
            unsafe_code_pattern="response.set_cookie('token', jwt_token) # readable by document.cookie",
            cvss_score=5.3,
        ),
        CWERuleDefinition(
            cwe_id="CWE-287",
            owasp_category="A07:2021-Identification and Authentication Failures",
            name="Improper Authentication Mechanism",
            description="The software improperly verifies the identity of an actor requesting access to restricted administrative functionality.",
            impact="Unauthorized user impersonation, account takeover, arbitrary privilege escalation.",
            affected_languages=["All Languages"],
            detection_heuristic="Direct invocation of privileged operations without checking session token or HMAC signature.",
            remediation_strategy="Implement multi-factor authentication (MFA) and server-side cryptographically signed token verification.",
            safe_code_pattern="@require_authenticated_user\ndef get_admin_dashboard(): pass",
            unsafe_code_pattern="def get_admin_dashboard(): # missing authentication check\n    return render_admin()",
            cvss_score=9.1,
        ),
        CWERuleDefinition(
            cwe_id="CWE-862",
            owasp_category="A01:2021-Broken Access Control",
            name="Missing Authorization (Insecure Direct Object Reference - IDOR)",
            description="The product does not perform an authorization check when an actor attempts to access a resource using a user-controlled identifier.",
            impact="Horizontal and vertical privilege escalation, unauthorized data tampering and exfiltration.",
            affected_languages=["All Web Frameworks"],
            detection_heuristic="Direct database query using path parameter entity_id without verifying ownership against request.user.id.",
            remediation_strategy="Enforce object-level access control on every record lookup: SELECT * WHERE id = :id AND owner_id = :current_user.",
            safe_code_pattern="record = db.query(Document).filter_by(id=doc_id, owner_id=user.id).first_or_404()",
            unsafe_code_pattern="record = db.query(Document).filter_by(id=doc_id).first() # IDOR vulnerability",
            cvss_score=8.6,
        ),
        CWERuleDefinition(
            cwe_id="CWE-611",
            owasp_category="A05:2021-Security Misconfiguration",
            name="Improper Restriction of XML External Entity Reference (XXE)",
            description="The software processes an XML document that can contain XML entities with URIs that resolve to documents outside of the intended sphere of control.",
            impact="Arbitrary local file disclosure (/etc/passwd), server-side request forgery (SSRF), Denial of Service.",
            affected_languages=["Python", "Java", "Node.js", "C#"],
            detection_heuristic="xml.etree.ElementTree or lxml.etree.fromstring with resolve_entities=True or external DTDs enabled.",
            remediation_strategy="Disable external DTD processing, disallow entity resolution, or use defusedxml package.",
            safe_code_pattern="from defusedxml.ElementTree import parse; tree = parse(xml_file)",
            unsafe_code_pattern="import xml.etree.ElementTree as ET; tree = ET.parse(xml_file) # vulnerable to XXE",
            cvss_score=8.2,
        ),
        CWERuleDefinition(
            cwe_id="CWE-400",
            owasp_category="A05:2021-Security Misconfiguration",
            name="Uncontrolled Resource Consumption (Denial of Service)",
            description="The software does not properly restrict the size or amount of resources that can be requested or influenced by an untrusted actor.",
            impact="Application crash, out of memory (OOM) kill, compute starvation for all legitimate users.",
            affected_languages=["All Languages"],
            detection_heuristic="Unbounded file uploads, infinite loops over client-provided lengths, or memory buffering without limits.",
            remediation_strategy="Enforce maximum payload size limits (e.g. MAX_CONTENT_LENGTH = 16 * 1024 * 1024) and streaming chunks.",
            safe_code_pattern="app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB limit",
            unsafe_code_pattern="data = request.raw.read() # unbounded read into RAM",
            cvss_score=7.5,
        ),
        CWERuleDefinition(
            cwe_id="CWE-319",
            owasp_category="A02:2021-Cryptographic Failures",
            name="Cleartext Transmission of Sensitive Information",
            description="The software transmits sensitive data (credentials, PII, API tokens) in cleartext over an unencrypted channel (HTTP instead of HTTPS).",
            impact="Network sniffing, credential theft on local area or public Wi-Fi networks.",
            affected_languages=["All Languages"],
            detection_heuristic="URLs starting with http:// in production API endpoints or redirect targets.",
            remediation_strategy="Enforce HTTPS everywhere with HTTP Strict Transport Security (HSTS) headers.",
            safe_code_pattern="API_ENDPOINT = 'https://api.service.com/v1'",
            unsafe_code_pattern="API_ENDPOINT = 'http://api.service.com/v1' # unencrypted transport",
            cvss_score=7.5,
        ),
        CWERuleDefinition(
            cwe_id="CWE-347",
            owasp_category="A02:2021-Cryptographic Failures",
            name="Improper Verification of Cryptographic Signature",
            description="The software does not verify, or improperly verifies, the cryptographic signature of received tokens, updates, or webhooks.",
            impact="Signature forgery, arbitrary payload execution, unauthorized webhook processing.",
            affected_languages=["Python", "Node.js", "Go"],
            detection_heuristic="jwt.decode with verify_signature=False or algorithms=['none'].",
            remediation_strategy="Always verify digital signatures using asymmetric public keys (RS256, Ed25519) and reject 'none' algorithm.",
            safe_code_pattern="payload = jwt.decode(token, public_key, algorithms=['RS256'])",
            unsafe_code_pattern="payload = jwt.decode(token, options={'verify_signature': False}) # signature bypassed",
            cvss_score=8.5,
        ),
    ]

    _BY_CWE: Dict[str, CWERuleDefinition] = {r.cwe_id: r for r in VULNERABILITIES}

    @classmethod
    def get_by_cwe(cls, cwe_id: str) -> Optional[CWERuleDefinition]:
        return cls._BY_CWE.get(cwe_id.upper())

    @classmethod
    def list_by_owasp(cls, owasp_cat: str) -> List[CWERuleDefinition]:
        cat_lower = owasp_cat.lower()
        return [r for r in cls.VULNERABILITIES if cat_lower in r.owasp_category.lower()]

    @classmethod
    def search_rules(cls, query: str) -> List[CWERuleDefinition]:
        q = query.lower()
        return [
            r for r in cls.VULNERABILITIES
            if q in r.cwe_id.lower() or q in r.name.lower() or q in r.description.lower()
        ]

    @classmethod
    def export_catalog_json(cls) -> str:
        return json.dumps([r.to_dict() for r in cls.VULNERABILITIES], indent=2)
