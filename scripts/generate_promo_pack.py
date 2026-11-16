# -*- coding: utf-8 -*-
"""Siber Akademi — T-Zero Zero-Cost Organic Promotion & Launch Toolkit Wrapper.

Usage:
    python scripts/generate_promo_pack.py
    python scripts/generate_promo_pack.py --check
    python scripts/generate_promo_pack.py --print hn
    python scripts/generate_promo_pack.py --print reddit
    python scripts/generate_promo_pack.py --print twitter
"""

import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tzero.tzero_promo import main

if __name__ == "__main__":
    sys.exit(main())
