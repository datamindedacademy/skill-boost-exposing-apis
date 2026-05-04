#!/usr/bin/env python3
"""
Capture the current /openapi.json into the Ex5 sparse-spec snapshot.
Run this from the *pre-Ex3* state.
"""

from __future__ import annotations

import json
from pathlib import Path

from checkup_api.main import app

OUTPUT = (
    Path(__file__).resolve().parent.parent
    / "exercises"
    / "05_agent"
    / "openapi_sparse.json"
)


def main():
    spec = app.openapi()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(spec, indent=2) + "\n")


if __name__ == "__main__":
    main()
