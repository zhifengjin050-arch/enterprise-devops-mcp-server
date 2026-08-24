#!/usr/bin/env python3
"""Render README / screenshot PNGs from docs/screenshots/html."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "docs" / "screenshots" / "html"
IMAGES = ROOT / "docs" / "images"
SHOTS = ROOT / "docs" / "screenshots"

MAP = [
    ("architecture.html", IMAGES / "architecture.png", {"width": 1440, "height": 900}),
    ("mcp-tools.html", IMAGES / "mcp-tools.png", {"width": 1440, "height": 900}),
    ("cursor-claude-mcp.html", IMAGES / "cursor-claude-mcp.png", {"width": 1440, "height": 900}),
    ("health.html", SHOTS / "02-server-health-check.png", {"width": 1440, "height": 900}),
    ("docker.html", SHOTS / "03-docker-inspection.png", {"width": 1440, "height": 900}),
    ("ssh-filter.html", SHOTS / "05-ssh-dangerous-command-filter.png", {"width": 1440, "height": 900}),
    ("mcp-tools.html", SHOTS / "01-mcp-connection-tools.png", {"width": 1440, "height": 900}),
    ("k8s.html", SHOTS / "04-k8s-pod-status.png", {"width": 1440, "height": 900}),
    ("disk.html", SHOTS / "06-disk-cleanup-automation.png", {"width": 1440, "height": 900}),
]


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("pip install playwright && python -m playwright install chromium")
        return 1
    IMAGES.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, dest, vp in MAP:
            src = HTML / name
            page = browser.new_page(viewport=vp, device_scale_factor=2)
            page.goto(src.as_uri(), wait_until="load")
            dest.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(dest), full_page=False)
            print("wrote", dest.relative_to(ROOT))
            page.close()
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
