"""
T-Zero Reddit Automation & Fast-Publisher
100% Guvenli: Kalici Chrome Profili (Anti-Bot Bypass) & Google SSO Destekli.
"""

import sys
import os
import time
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE_DIR = Path(__file__).resolve().parent / ".reddit_profile"

TEMPLATES = {
    "LocalLLaMA": {
        "title": "T-Zero: Cut LLM context bloat by up to 95% with local AST pruning (Open-Source, 0 external APIs)",
        "body": """Hey r/LocalLLaMA,

When feeding full repositories or large codebases into local LLMs (Llama 3, Qwen 2.5, DeepSeek) or coding agents, 50k+ tokens are wasted on boilerplate function bodies and imports, destroying the context window and burning VRAM/tokens.

I built **T-Zero** (tzero-mcp) — a 100% offline, enterprise AST context pruning engine & 37-tool MCP server.

**How it works:**
- Slices target codebases into hierarchical AST interface signatures (preserves types, function signatures, classes, docstrings; strips heavy internal bodies).
- Multi-tier context generation (T-1 to T-4) achieving up to 95% context reduction.
- Built-in BM25 hybrid semantic search without needing external cloud embedding APIs.
- 100% Zero-Leak OS Keyring security (secrets and credentials are never injected into LLM context).

- **GitHub:** https://github.com/toprakahmetaydogmus/TZeroAlgorithm
- **PyPI:** `pip install tzero-mcp`

Would love your thoughts, feedback, and benchmarks!"""
    },
    "ClaudeAI": {
        "title": "Built a 37-tool MCP Server that cuts Claude's context usage by up to 95% with AST Skeletons",
        "body": """Hey r/ClaudeAI,

Working with Claude 3.5 Sonnet on large projects often hits the 200k context limit fast, leading to high API costs or degraded attention quality.

I created **T-Zero**, an open-source Model Context Protocol (MCP) server designed specifically for AI coding agents.

**Highlights:**
- **AST Pruning:** Slices full codebases into interface skeletons, reducing raw code tokens by 80-95% while keeping all critical architecture context.
- **37 Native MCP Tools:** Includes dynamic skeletonizing, blast-radius impact analysis, dead-code detection, and PBFT consensus for swarms.
- **Works with Claude Desktop & Cursor:** One-line install via `pip install tzero-mcp` or Smithery registry.
- **100% Zero-Leak:** Blocks sensitive API keys or environment variables from leaking into prompt context.

- **GitHub:** https://github.com/toprakahmetaydogmus/TZeroAlgorithm
- **PyPI:** `pip install tzero-mcp`

Check it out and let me know if it helps with your Claude coding workflows!"""
    },
    "Cursor": {
        "title": "T-Zero: AST Context Engine & .cursorrules Generator to stop wasting tokens in Cursor",
        "body": """Hey r/Cursor,

Cursor is amazing, but referencing entire files (@Files / codebase index) can quickly burn through fast requests and fill context with non-essential boilerplate.

I built **T-Zero** (tzero-mcp), an open-source AST context engine & MCP server:

- **Smart AST Skeletons:** Preserves full class & function signatures with types while stripping inner code blocks.
- **Instant .cursorrules Generator:** Analyzes repository architecture and exports optimized agent rules.
- **Zero Hallucination Guard:** Validates AST imports before generating code suggestions.
- **95% Token Reduction:** Feed large codebases without hitting token degradation.

- **GitHub:** https://github.com/toprakahmetaydogmus/TZeroAlgorithm
- **PyPI:** `pip install tzero-mcp`

Give it a try and feel free to star the repo if you like it!"""
    },
    "Python": {
        "title": "T-Zero: Enterprise AST Codebase Context Engine & Token Pruner for AI Agents",
        "body": """Hey r/Python,

I've been working on **T-Zero** (tzero-mcp), an open-source Python tool that parses codebases using `ast` and converts them into ultra-compact context trees for LLMs, achieving up to 95% token savings.

Features:
- Pure Python & Polyglot AST analysis (preserves types, classes, docstrings).
- 37-tool autonomous Model Context Protocol (MCP) server.
- Zero-leak security scanner for API keys.
- Completely local and offline — 0 external API dependencies.

- **GitHub:** https://github.com/toprakahmetaydogmus/TZeroAlgorithm
- **PyPI:** `pip install tzero-mcp`

Any feedback or stars on the project are greatly appreciated!"""
    }
}


def find_opera_path():
    """Finds installed Opera or Opera GX executable on Windows."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
    
    candidates = [
        Path(local_app_data) / "Programs" / "Opera" / "opera.exe",
        Path(local_app_data) / "Programs" / "Opera GX" / "opera.exe",
        Path(local_app_data) / "Programs" / "Opera" / "launcher.exe",
        Path(local_app_data) / "Programs" / "Opera GX" / "launcher.exe",
        Path(program_files) / "Opera" / "launcher.exe",
        Path(program_files) / "Opera GX" / "launcher.exe",
        Path(program_files_x86) / "Opera" / "launcher.exe",
        Path(program_files_x86) / "Opera GX" / "launcher.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def launch_browser(playwright, headless=False):
    """Bypasses Google & Reddit automation detection using Opera persistent profile and stealth flags."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    
    args = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-infobars",
        "--start-maximized"
    ]
    
    opera_exe = find_opera_path()
    if opera_exe:
        print(f"🔴 Opera algılandı: {opera_exe}")
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            executable_path=opera_exe,
            headless=headless,
            args=args,
            no_viewport=True
        )
    else:
        print("⚠️ Opera bulunamadı, sistem Chromium motoru açılıyor...")
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            channel="chrome",
            args=args,
            no_viewport=True
        )
    
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    return context


def login_flow():
    """Opens Reddit in Opera for 1-click Google login."""
    print("=" * 60)
    print("🚀 REDDIT GOOGLE GİRİŞ MODU (OPERA) BAŞLATILIYOR")
    print("=" * 60)
    print("Opera açılıyor...")
    print("1. Açılan pencerede 'Continue with Google' (Google ile Devam Et) butonuna basın.")
    print("2. Google hesabınızı seçip giriş yapın.")
    print("3. Giriş yaptıktan sonra terminale dönüp ENTER'a basın.")
    print("=" * 60)
    
    with sync_playwright() as p:
        context = launch_browser(p, headless=False)

            
        page = context.new_page()
        page.goto("https://www.reddit.com/login", wait_until="domcontentloaded")
        
        input("\n👉 Google ile giriş yaptıktan sonra buraya gelip ENTER tuşuna basın... ")
        
        print("\n✅ Oturum ve çerezler kaydedildi!")
        print(f"📁 Profil konumu: {PROFILE_DIR}")
        context.close()


def post_flow(subreddit: str, auto_submit: bool = False):
    """Automatically navigates to subreddit submit page and fills content safely."""
    if subreddit not in TEMPLATES:
        print(f"⚠️ Bilinmeyen subreddit '{subreddit}'. Mevcut olanlar: {list(TEMPLATES.keys())}")
        return
        
    post_data = TEMPLATES[subreddit]
    print("=" * 60)
    print(f"📝 REDDIT OTO-POST: r/{subreddit}")
    print("=" * 60)
    print(f"Başlık: {post_data['title']}")
    print("-" * 60)
    
    with sync_playwright() as p:
        context = launch_browser(p, headless=False)
        page = context.new_page()
        submit_url = f"https://www.reddit.com/r/{subreddit}/submit"
        print(f"🌐 Sayfaya gidiliyor: {submit_url}")
        page.goto(submit_url, wait_until="domcontentloaded")
        time.sleep(3)
        
        # Check if login is required
        if "login" in page.url:
            print("❌ Oturum bulunamadı! Lütfen önce 'python reddit_poster.py --login' çalıştırın.")
            context.close()
            return
            
        print("✍️ Başlık ve içerik otomatik dolduruluyor...")
        
        # Try filling title
        try:
            title_input = page.locator('textarea[name="title"], input[name="title"], faceplate-textarea-input[name="title"] textarea, [placeholder*="Title"]').first
            title_input.wait_for(timeout=7000)
            title_input.click()
            title_input.fill(post_data["title"])
            print("  ✓ Başlık yazıldı.")
        except Exception as e:
            print(f"  ⚠️ Başlık alanı otomatik bulunamadı ({e}), lütfen açılan tarayıcıda manuel yapıştırın.")

        time.sleep(1)

        # Try filling text body
        try:
            # Switch to markdown mode if button exists
            md_button = page.locator('button:has-text("Markdown"), button[aria-label*="Markdown"]').first
            if md_button.is_visible():
                md_button.click()
                time.sleep(0.5)
                
            body_input = page.locator('textarea[name="body"], div[role="textbox"], textarea[placeholder*="Text"]').first
            body_input.wait_for(timeout=5000)
            body_input.click()
            body_input.fill(post_data["body"])
            print("  ✓ Gövde metni yazıldı.")
        except Exception as e:
            print(f"  ⚠️ Metin alanı doldurulurken: {e}. Metin panoya kopyalanabilir.")

        print("\n" + "=" * 60)
        if auto_submit:
            print("🚀 'auto-submit' devrede: 5 saniye içinde 'Post' butonuna basılıyor...")
            time.sleep(5)
            try:
                post_btn = page.locator('button:has-text("Post"), button[type="submit"]:has-text("Post")').first
                post_btn.click()
                print("✅ 'Post' tıklandı!")
                time.sleep(5)
            except Exception as e:
                print(f"⚠️ Post butonu tıklanamadı: {e}")
        else:
            print("🛡️ EN GÜVENLİ MOD AKTİF:")
            print("1. Açık olan tarayıcı penceresinde içeriği gözden geçirin.")
            print("2. Eğer subreddit kuralı gereği 'Flair' (etiket) istiyorsa bir etiket seçin.")
            print("3. 'Post' butonuna basarak paylaşımı tamamlayın!")
            print("4. İşiniz bitince bu terminalde ENTER'a basarak tarayıcıyı kapatabilirsiniz.")
            input("\n👉 Paylaşımı yaptıktan sonra kapatmak için ENTER'a basın... ")
            
        context.close()


def main():
    parser = argparse.ArgumentParser(description="T-Zero Reddit Safe Auto-Poster")
    parser.add_argument("--login", action="store_true", help="Google ile tek seferlik oturum aç")
    parser.add_argument("--post", action="store_true", help="Belirtilen subreddit'e post hazırla")
    parser.add_argument("--sub", type=str, default="LocalLLaMA", choices=["LocalLLaMA", "ClaudeAI", "Cursor", "Python"], help="Hedef subreddit")
    parser.add_argument("--auto-submit", action="store_true", help="Post butonuna da otomatik bas (Varsayılan: Güvenli onay modu)")
    
    args = parser.parse_args()
    
    if args.login:
        login_flow()
    elif args.post:
        post_flow(args.sub, auto_submit=args.auto_submit)
    else:
        parser.print_help()
        print("\n💡 Hızlı Kullanım:")
        print("  1. Adım: python reddit_poster.py --login      (Google ile 1 kere oturum açın)")
        print("  2. Adım: python reddit_poster.py --post --sub LocalLLaMA")
        print("  Diğerleri: --sub ClaudeAI | --sub Cursor | --sub Python")


if __name__ == "__main__":
    main()
