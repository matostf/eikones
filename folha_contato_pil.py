#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Folha de contato A4 (PDF multipágina) do acervo, via Pillow — robusto, sem navegador.

A4 a 150 dpi = 1240x1754 px. Margens 16mm (horiz) x 18mm (vert). Grade de 4 colunas,
agrupada por período, com legenda (nº + título + autor). Páginas raster a 150 dpi,
salvas como PDF no tamanho físico A4.
"""
import json, os, collections
from PIL import Image, ImageDraw, ImageFont, ImageOps

DEST = os.path.dirname(os.path.abspath(__file__))
DPI = 150
MM = DPI / 25.4
W, H = int(210 * MM), int(297 * MM)          # 1240 x 1754
MX, MY = int(16 * MM), int(18 * MM)          # margens
CW = W - 2 * MX                              # largura útil
COLS = 4
GAP = int(5 * MM)
CELL_W = (CW - (COLS - 1) * GAP) // COLS
THUMB_H = int(34 * MM)
CAP_H = int(11 * MM)
ROW_H = THUMB_H + CAP_H + int(2 * MM)
HEAD_H = int(13 * MM)
TILE = (242, 239, 230)
BORDER = (225, 218, 201)
INK = (29, 29, 31)
GREY = (138, 138, 138)

FD = "/usr/share/fonts/truetype/dejavu/"
def f(name, size): return ImageFont.truetype(FD + name, size)
F_TITLE = f("DejaVuSerif-Bold.ttf", 40)
F_SUB   = f("DejaVuSans.ttf", 17)
F_HEAD  = f("DejaVuSerif-Bold.ttf", 25)
F_CONT  = f("DejaVuSans.ttf", 14)
F_NUM   = f("DejaVuSans-Bold.ttf", 14)
F_TIT   = f("DejaVuSans.ttf", 13)
F_AUT   = f("DejaVuSans.ttf", 11)

PER = {
    "00": ("Pré-História",    (138, 109, 59)),
    "01": ("Oriente Próximo", (181, 101, 29)),
    "02": ("Grécia",          (45, 106, 142)),
    "03": ("Roma",            (140, 47, 47)),
    "04": ("Idade Média",     (90, 74, 122)),
    "05": ("Idade Moderna",   (47, 110, 79)),
    "06": ("Brasil",          (29, 122, 74)),
}

man = json.load(open(os.path.join(DEST, "MANIFESTO.json"), encoding="utf-8"))
man.sort(key=lambda m: (m["periodo_num"], m["slug"]))
grupos = collections.OrderedDict()
for m in man:
    grupos.setdefault(m["periodo_num"], []).append(m)

# medidor de texto
_meas = ImageDraw.Draw(Image.new("RGB", (1, 1)))
def tlen(s, font): return _meas.textlength(s, font=font)

def wrap(s, font, maxw, max_lines):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tlen(t, font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines:  # garante ellipsis se sobrou texto
        last = lines[-1]
        joined = " ".join(lines)
        if joined != s.strip():
            while tlen(last + "…", font) > maxw and last:
                last = last[:-1]
            lines[-1] = last + "…"
    return lines

def trunc(s, font, maxw):
    if tlen(s, font) <= maxw:
        return s
    while s and tlen(s + "…", font) > maxw:
        s = s[:-1]
    return s + "…"

pages = []
def new_page():
    img = Image.new("RGB", (W, H), "white")
    pages.append(img)
    return img, ImageDraw.Draw(img)

img, d = new_page()
# capa (topo da pág. 1)
d.text((W // 2, MY + 6), "Acervo Didático de História", font=F_TITLE, fill=INK, anchor="ma")
sub = f"{len(man)} obras em alta resolução · Wikimedia Commons · da Pré-História à Idade Moderna, com História do Brasil"
d.text((W // 2, MY + 58), sub, font=F_SUB, fill=(90, 90, 90), anchor="ma")
d.line((MX, MY + 92, W - MX, MY + 92), fill=INK, width=2)
y = MY + 112

n = 0
for pnum, itens in grupos.items():
    nome, cor = PER.get(pnum, (pnum, (60, 60, 60)))
    # cabeçalho do período (não quebrar logo antes de uma linha)
    if y + HEAD_H + ROW_H > H - MY:
        img, d = new_page(); y = MY
    d.rectangle((MX, y + 4, MX + 6, y + HEAD_H - 4), fill=cor)
    d.text((MX + 16, y + HEAD_H // 2), nome.upper(), font=F_HEAD, fill=cor, anchor="lm")
    nx = MX + 22 + tlen(nome.upper(), F_HEAD)
    d.text((nx, y + HEAD_H // 2 + 4), f"{len(itens)} imagens", font=F_CONT, fill=GREY, anchor="lm")
    y += HEAD_H

    col = 0
    for m in itens:
        n += 1
        if col == 0 and y + ROW_H > H - MY:
            img, d = new_page(); y = MY
        cx = MX + col * (CELL_W + GAP)
        # tile + thumb
        d.rectangle((cx, y, cx + CELL_W, y + THUMB_H), fill=TILE, outline=BORDER, width=1)
        try:
            im = Image.open(os.path.join(DEST, m["arquivo"]))
            im = ImageOps.exif_transpose(im).convert("RGB")
            im = ImageOps.contain(im, (CELL_W - 6, THUMB_H - 6))
            img.paste(im, (cx + (CELL_W - im.width) // 2, y + (THUMB_H - im.height) // 2))
        except Exception as e:
            d.text((cx + CELL_W // 2, y + THUMB_H // 2), "?", font=F_HEAD, fill=GREY, anchor="mm")
        # legenda
        ty = y + THUMB_H + int(1.6 * MM)
        num = f"{n:03d} "
        d.text((cx, ty), num, font=F_NUM, fill=cor)
        noff = tlen(num, F_NUM)
        lines = wrap(m["titulo"], F_TIT, CELL_W - noff, 2)
        for i, ln in enumerate(lines):
            d.text((cx + (noff if i == 0 else 0), ty + i * 15), ln, font=F_TIT, fill=(34, 34, 34))
        aut = (m.get("autor") or "").strip()
        if aut:
            d.text((cx, ty + len(lines) * 15 + 1), trunc(aut, F_AUT, CELL_W), font=F_AUT, fill=GREY)

        col += 1
        if col == COLS:
            col = 0
            y += ROW_H
    if col != 0:
        y += ROW_H

out = os.path.join(DEST, "FOLHA-DE-CONTATO.pdf")
pages[0].save(out, "PDF", save_all=True, append_images=pages[1:], resolution=float(DPI))
print(f"{len(pages)} páginas A4, {n} miniaturas -> FOLHA-DE-CONTATO.pdf ({os.path.getsize(out)//1024} KB)")
