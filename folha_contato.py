#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera folha-contato.html (mosaico A4 de miniaturas) a partir do MANIFESTO.json."""
import json, html, os, collections

DEST = os.path.dirname(os.path.abspath(__file__))
man = json.load(open(os.path.join(DEST, "MANIFESTO.json"), encoding="utf-8"))
man.sort(key=lambda m: (m["periodo_num"], m["slug"]))

PER = {
    "00": ("Pré-História", "#8a6d3b"),
    "01": ("Oriente Próximo", "#b5651d"),
    "02": ("Grécia", "#2d6a8e"),
    "03": ("Roma", "#8c2f2f"),
    "04": ("Idade Média", "#5a4a7a"),
    "05": ("Idade Moderna", "#2f6e4f"),
    "06": ("Brasil", "#1d7a4a"),
}

grupos = collections.OrderedDict()
for m in man:
    grupos.setdefault(m["periodo_num"], []).append(m)

css = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html, body { margin: 0; padding: 0; }
body { font-family: 'DejaVu Sans', Arial, sans-serif; color: #1d1d1f; }
.capa { text-align: center; padding: 4mm 0 7mm; border-bottom: 2px solid #1d1d1f; margin-bottom: 6mm; }
.capa h1 { font-family: Georgia, 'DejaVu Serif', serif; font-size: 22pt; margin: 0 0 2mm; letter-spacing: .3px; }
.capa .sub { font-size: 9.5pt; color: #555; }
.periodo { break-inside: avoid; margin-bottom: 4mm; }
.periodo-h { display: flex; align-items: baseline; gap: 3mm; padding: 1.6mm 0 1.6mm 3mm;
  border-left: 4px solid var(--c); margin: 5mm 0 3mm; break-after: avoid; }
.periodo-h .nome { font-family: Georgia, 'DejaVu Serif', serif; font-size: 13pt; font-weight: bold;
  color: var(--c); text-transform: uppercase; letter-spacing: .6px; }
.periodo-h .cont { font-size: 8pt; color: #888; }
.grid { display: flex; flex-wrap: wrap; gap: 4.5mm; }
.cell { width: 39mm; break-inside: avoid; }
.thumb { width: 39mm; height: 39mm; background: #f2efe6; border: 1px solid #e1dac9;
  display: flex; align-items: center; justify-content: center; overflow: hidden; }
.thumb img { max-width: 100%; max-height: 100%; object-fit: contain; display: block; }
.cap { margin-top: 1.4mm; font-size: 6.8pt; line-height: 1.18; }
.cap .num { font-weight: bold; color: var(--c); }
.cap .tit { color: #222; }
.cap .aut { display: block; color: #8a8a8a; font-size: 6pt; margin-top: .3mm; }
"""

parts = [
    "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>",
    f"<style>{css}</style></head><body>",
    "<div class='capa'><h1>Acervo Didático de História</h1>",
    f"<div class='sub'>{len(man)} obras em alta resolução · Wikimedia Commons · "
    "da Pré-História à Idade Moderna, com História do Brasil</div></div>",
]

n = 0
for pnum, itens in grupos.items():
    nome, cor = PER.get(pnum, (pnum, "#444"))
    parts.append(f"<section class='periodo' style='--c:{cor}'>")
    parts.append(
        f"<div class='periodo-h'><span class='nome'>{html.escape(nome)}</span>"
        f"<span class='cont'>{len(itens)} imagens</span></div>"
    )
    parts.append("<div class='grid'>")
    for m in itens:
        n += 1
        arq = html.escape(m["arquivo"])
        tit = html.escape(m["titulo"])
        aut = html.escape((m.get("autor") or "").strip())
        aut_html = f"<span class='aut'>{aut[:48]}</span>" if aut else ""
        parts.append(
            f"<div class='cell'><div class='thumb'><img src='{arq}' loading='eager'></div>"
            f"<div class='cap'><span class='num'>{n:03d}</span> "
            f"<span class='tit'>{tit}</span>{aut_html}</div></div>"
        )
    parts.append("</div></section>")

parts.append("</body></html>")
open(os.path.join(DEST, "folha-contato.html"), "w", encoding="utf-8").write("".join(parts))
print(f"folha-contato.html gerado com {n} miniaturas em {len(grupos)} períodos.")
