#!/usr/bin/env python3
"""Banana Claude -- CSV Batch Workflow

Parse a CSV file of image generation requests and output a structured plan.
Claude then executes each row via MCP.

Usage:
    batch.py --csv path/to/file.csv

CSV columns:
    prompt (required), ratio, resolution, model, preset (all optional)

Example CSV:
    prompt,ratio,resolution
    "coffee shop hero image",16:9,2K
    "team photo placeholder",1:1,1K
    "product shot on marble",4:3,2K
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

# Ensure sibling modules import regardless of the caller's cwd.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pricing import lookup_cost  # noqa: E402

DEFAULT_MODEL = "gemini-3.1-flash-image-preview"
DEFAULT_RESOLUTION = "2K"  # Match generate.py and the skill's documented default
DEFAULT_RATIO = "1:1"

# Per-model resolution support (see references/gemini-models.md). 512/2K/4K are
# Nano Banana 2 (3.1) only; gemini-2.5-flash-image tops out at 1K.
MODEL_RESOLUTIONS = {
    "gemini-3.1-flash-image-preview": {"512", "1K", "2K", "4K"},
    "gemini-2.5-flash-image": {"1K"},
}


def default_resolution_for(model):
    """Default resolution for a model -- 2K where supported, else its best tier."""
    allowed = MODEL_RESOLUTIONS.get(model)
    if allowed is None or DEFAULT_RESOLUTION in allowed:
        return DEFAULT_RESOLUTION
    for tier in ("4K", "2K", "1K", "512"):
        if tier in allowed:
            return tier
    return DEFAULT_RESOLUTION


def estimate_cost(model, resolution):
    """Estimate cost for a single image (full price, no batch discount)."""
    return lookup_cost(model, resolution)


def main():
    parser = argparse.ArgumentParser(description="Parse CSV batch and output generation plan")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    args = parser.parse_args()

    csv_path = Path(args.csv).resolve()
    if not csv_path.exists():
        print(json.dumps({"error": True, "message": f"CSV not found: {csv_path}"}))
        sys.exit(1)

    rows = []
    errors = []

    try:
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or "prompt" not in reader.fieldnames:
                print(json.dumps({"error": True, "message": "CSV must have a 'prompt' column header"}))
                sys.exit(1)
            for i, row in enumerate(reader, start=2):  # Line 2+ (1 is header)
                prompt = row.get("prompt", "").strip()
                if not prompt:
                    errors.append(f"Row {i}: missing prompt")
                    continue

                model = row.get("model", "").strip() or DEFAULT_MODEL
                resolution = row.get("resolution", "").strip() or default_resolution_for(model)
                allowed = MODEL_RESOLUTIONS.get(model)
                if allowed is not None and resolution not in allowed:
                    errors.append(f"Row {i}: resolution '{resolution}' not supported by model '{model}' (supported: {sorted(allowed)})")
                    continue

                rows.append({
                    "row": i,
                    "prompt": prompt,
                    "ratio": row.get("ratio", "").strip() or DEFAULT_RATIO,
                    "resolution": resolution,
                    "model": model,
                    "preset": row.get("preset", "").strip() or None,
                })
    except (csv.Error, UnicodeDecodeError) as e:
        print(json.dumps({"error": True, "message": f"Failed to parse CSV: {e}"}))
        sys.exit(1)

    if errors:
        print("Validation errors:")
        for e in errors:
            print(f"  - {e}")
        if not rows:
            sys.exit(1)
        print()

    # Cost estimate
    total_cost = sum(estimate_cost(r["model"], r["resolution"]) for r in rows)

    # Output structured JSON for Claude to consume
    print(json.dumps({"rows": rows, "total_count": len(rows),
                       "estimated_cost": round(total_cost, 3),
                       "errors": errors}, indent=2))


if __name__ == "__main__":
    main()
