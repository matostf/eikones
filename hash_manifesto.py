#!/usr/bin/env python3
"""Adiciona pHash + dHash a cada entrada do MANIFESTO.json.

Idempotente: pula entradas que já têm `phash`. Roda depois de baixar imagens
novas para garantir que o manifesto sempre tenha os hashes prontos para
uso em dedup downstream.

Reusa `app.reverse.hasher` do `~/Projetos/acervo-historia`.

Uso:
    python3 hash_manifesto.py              # processa tudo que falta
    python3 hash_manifesto.py --redo SLUG  # recalcula hash de um slug específico
    python3 hash_manifesto.py --dry        # só mostra o que faria
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Find sibling project `acervo-historia` to reuse its hasher.
ROOT = Path(__file__).resolve().parent
ACERVO_HISTORIA = ROOT.parent / "acervo-historia"
if not ACERVO_HISTORIA.exists():
    print(f"ERRO: esperava encontrar ../acervo-historia/ ao lado deste projeto", file=sys.stderr)
    sys.exit(2)
sys.path.insert(0, str(ACERVO_HISTORIA))

from app.reverse.hasher import hash_from_path  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    dry = "--dry" in args
    redo: list[str] = []
    if "--redo" in args:
        idx = args.index("--redo")
        redo = args[idx + 1 :]

    manifest_path = ROOT / "MANIFESTO.json"
    if not manifest_path.exists():
        print(f"ERRO: MANIFESTO.json não encontrado em {manifest_path}", file=sys.stderr)
        return 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, list):
        print("ERRO: MANIFESTO.json deveria ser uma lista", file=sys.stderr)
        return 2

    updated = 0
    skipped = 0
    missing = 0

    for entry in manifest:
        slug = entry.get("slug", "?")
        arquivo = entry.get("arquivo")
        if not arquivo:
            print(f"  - {slug}: sem campo 'arquivo'")
            missing += 1
            continue
        # If --redo filter is set, only process matching slugs.
        if redo and slug not in redo:
            continue
        # Skip already-hashed unless --redo.
        if entry.get("phash") and entry.get("dhash") and not redo:
            skipped += 1
            continue

        path = ROOT / arquivo
        if not path.exists():
            print(f"  ! {slug}: arquivo não existe ({arquivo})")
            missing += 1
            continue

        try:
            h = hash_from_path(str(path))
        except Exception as e:  # noqa: BLE001
            print(f"  ! {slug}: erro hash — {e}")
            missing += 1
            continue

        entry["phash"] = h.phash
        entry["dhash"] = h.dhash
        updated += 1
        marker = "(dry)" if dry else "ok"
        print(f"  {marker} {slug}: phash={h.phash} dhash={h.dhash}")

    print()
    print(f"Atualizadas: {updated}  ·  Já tinha hash: {skipped}  ·  Pulou (sem arquivo/erro): {missing}")

    if dry:
        print("(dry-run; não gravou)")
        return 0

    if updated > 0:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Gravou {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
