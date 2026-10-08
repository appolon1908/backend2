#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".codestra", "migrations", "__pycache__"}
WRITE_MARKERS = ("requests.post(", "requests.put(", "requests.patch(", "requests.delete(")
violations = []

for path in ROOT.rglob("*.py"):
    if path.resolve() == Path(__file__).resolve():
        continue
    if any(part in SKIP_PARTS for part in path.parts):
        continue
    if path.name.startswith("test") or "tests" in path.parts:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "ODOO_BASE_URL" in text and any(marker in text for marker in WRITE_MARKERS):
        violations.append(path.relative_to(ROOT).as_posix())

if violations:
    raise SystemExit("Direct Odoo writes are forbidden; route writes through Middleware: " + ", ".join(sorted(violations)))

print("DIRECT_ODOO_WRITE_GUARD=PASS")
