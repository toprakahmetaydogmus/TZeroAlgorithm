#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-Zero Post-Clone Welcome & GitHub Star Prompt.

Run automatically or manually after cloning:
    python scripts/welcome.py
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tzero.tzero_welcome import main

if __name__ == "__main__":
    main()
