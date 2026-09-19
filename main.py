#!/usr/bin/env python3
"""INWX DNS TUI Client
Author:  Pascal Bouquet <pascal@ptbos.de>
License: GNU General Public License v3.0 (GPL-3.0)
Year:    2026
"""

import sys
from tui_app import InwxTUIApp

def main():
    app = InwxTUIApp()
    try:
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
