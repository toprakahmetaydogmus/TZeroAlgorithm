#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T-Zero V3 Benchmark & Live Laboratory Server
Hosts the benchmark dashboard locally on http://127.0.0.1:8080 and opens browser.
"""

import os
import sys
import webbrowser
import http.server
import socketserver
from pathlib import Path

# Safe utf-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PORT = 8080
SITE_DIR = Path(__file__).resolve().parent

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE_DIR), **kwargs)

def start_server():
    os.chdir(SITE_DIR)
    url = f"http://127.0.0.1:{PORT}"
    
    print("=" * 60)
    print("SIBER AKADEMI - T-ZERO BENCHMARK & ANALYTICS LABORATORY")
    print(f"Server URL: {url}")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("127.0.0.1", PORT), CustomHandler) as httpd:
            try:
                webbrowser.open(url)
            except Exception:
                pass
            httpd.serve_forever()
    except OSError as e:
        if "address already in use" in str(e).lower() or getattr(e, "errno", None) in (98, 10048):
            alt_port = 8085
            url = f"http://127.0.0.1:{alt_port}"
            print(f"Port {PORT} in use, trying {alt_port}...")
            with socketserver.TCPServer(("127.0.0.1", alt_port), CustomHandler) as httpd:
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
                httpd.serve_forever()
        else:
            raise e

if __name__ == "__main__":
    start_server()
