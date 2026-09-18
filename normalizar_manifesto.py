#!/usr/bin/env python3
"""Normalise author/credit fields in MANIFESTO.json and MANIFESTO.csv.

`baixar.py` copies the `Artist` and `Credit` fields verbatim from the Wikimedia
Commons `extmetadata` API. Two things need a second pass:

1. Commons templates such as {{unknown|author}} render their label twice in
   the API output ("Unknown author Unknown author"). Collapse the repetition.
2. A handful of files carry an empty `Artist` or `Credit` on Commons. For
   those, the curator records the attribution by hand in OVERRIDES below,
   with the reasoning, so that no row in the manifest is left blank.

Run after `baixar.py`:

    python3 normalizar_manifesto.py
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSON = ROOT / "MANIFESTO.json"
CSV = ROOT / "MANIFESTO.csv"

# arquivo -> {campo: valor}. Only fields that are empty or unusable on Commons.
OVERRIDES: dict[str, dict[str, str]] = {
    # Commons: Artist empty, Credit "Wilfredor", licence CC0 (photograph).
    "03-roma_loba-capitolina.jpg": {
        "autor": "Anonymous (bronze, Etruscan or medieval); photograph by Wilfredor",
        "credito": "Wilfredor, CC0, via Wikimedia Commons",
    },
    # Commons: Artist empty; 15th-century manuscript miniature, public domain.
    "04-idade-media_joana-darc.jpg": {
        "autor": "Anonymous (15th-century miniature)",
    },
    # Commons: Artist and Credit both empty; 11th-century embroidery, public domain.
    "04-idade-media_tapecaria-de-bayeux.png": {
        "autor": "Anonymous (11th-century embroidery, Bayeux Tapestry)",
        "credito": "Public domain, via Wikimedia Commons",
    },
    # Commons: Credit empty; painting of 1801 by de Loutherbourg (d. 1812).
    "05-idade-moderna_coalbrookdale-a-noite.jpg": {
        "credito": "Public domain, via Wikimedia Commons",
    },
    # Commons: "Unknown author ... The original uploader was Jack1956 at English Wikipedia."
    "07-contemporanea_cartaz-votes-for-women.jpg": {
        "autor": "Unknown author (uploaded to en.wikipedia by Jack1956)",
    },
}

_DUP = re.compile(r"\b(Unknown (?:author|artist|source|photographer))\s*\1\b", re.IGNORECASE)


def normalise_text(value: str) -> str:
    value = (value or "").strip()
    value = _DUP.sub(r"\1", value)
    return re.sub(r"\s{2,}", " ", value)


def apply(entry: dict) -> dict:
    for field in ("autor", "credito"):
        entry[field] = normalise_text(entry.get(field, ""))
    for field, value in OVERRIDES.get(entry["arquivo"], {}).items():
        if not entry.get(field) or field == "autor" and entry[field].lower().startswith("unknown"):
            entry[field] = value
    return entry


def main() -> None:
    entries = [apply(e) for e in json.loads(JSON.read_text(encoding="utf-8"))]
    JSON.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with CSV.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames
        rows = [apply(r) for r in reader]
    with CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    empty = [e["arquivo"] for e in entries if not e["autor"] or not e["credito"] or not e["licenca"]]
    print(f"{len(entries)} entries; empty autor/credito/licenca: {len(empty)}")
    for a in empty:
        print("  ", a)


if __name__ == "__main__":
    main()
