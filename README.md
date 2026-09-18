# Armarium

**A curated, fully attributed collection of 215 public-domain and Creative
Commons images for teaching history**, from prehistory to the 20th century
with a section on Brazil. Every file was sourced from Wikimedia Commons,
checked by eye against the intended work, and recorded in a manifest with
its author, date, licence, credit line and source page.

*Armarium* is the medieval library cupboard where a scriptorium kept its books. Formerly `acervo-didatico-historia`; the old GitHub URL redirects.

*Portuguese documentation follows the English summary below.*

## Licensing at a glance

| licence (as recorded on Commons) | files |
|---|--:|
| Public domain | 135 |
| CC0 | 13 |
| CC BY (2.0, 2.5, 3.0, 4.0) | 15 |
| CC BY-SA (2.0, 2.5, 3.0, 3.0 de, 3.0 fr, 4.0) | 52 |
| non-commercial, no-derivatives, "all rights reserved", unknown | **0** |

215 of 215 files have a licence, an author, a credit and a Commons source
page in the manifest. The code and the metadata are MIT; each image keeps its
own licence (see [`LICENSE`](LICENSE)).

## Provenance schema

`MANIFESTO.csv` and `MANIFESTO.json` carry the same 16 columns per file:

| column | meaning |
|---|---|
| `arquivo` | file name in this repository; the prefix `00`–`07` is the period |
| `titulo` | title of the work in Portuguese, as used in class |
| `autor`, `data_obra` | artist and date, from the Commons `Artist` / `DateTimeOriginal` fields |
| `licenca` | licence short name from Commons `LicenseShortName`, version and jurisdiction kept |
| `credito` | Commons `Credit` field (source / photographer), the basis of the attribution line |
| `arquivo_commons`, `pagina_commons` | canonical `File:` name and URL on Commons, for re-verification |
| `largura`, `altura`, `original_wxh` | downloaded size (about 2000 px on the long side) and the original's size |
| `resolvido_via` | how the file was located: `wiki` (lead image of the article, 153), `search` (Commons search, 58), `override` (fixed by hand, 4) |
| `phash`, `dhash` (JSON only) | perceptual hashes for duplicate detection across collections |
| `descricao` | one-line description for the contact sheet |

Example row (`MANIFESTO.json`):

```json
{"arquivo": "00-pre-historia_altamira-bisao.jpg",
 "titulo": "Bisão da Caverna de Altamira",
 "autor": "Museo de Altamira y D. Rodríguez",
 "licenca": "CC BY-SA 3.0",
 "credito": "National Museum and Research Center of Altamira",
 "pagina_commons": "https://commons.wikimedia.org/wiki/File:9_Bisonte_Magdaleniense_pol%C3%ADcromo.jpg",
 "resolvido_via": "wiki", "phash": "bd57d9921a5e2603", "dhash": "796a4e3f1b373333"}
```

## How the collection was verified

1. **Resolution.** `baixar.py` holds the curated list (period, slug, title,
   Wikipedia article or Commons search term) and resolves each entry through
   the MediaWiki API, reading licence and author from `extmetadata`.
2. **Human check.** Every downloaded file was opened and compared with the
   intended work; the classic failure (a portrait of the painter instead of
   the painting) was caught this way and fixed with `override` entries.
3. **Normalisation.** `normalizar_manifesto.py` collapses Commons template
   artefacts ("Unknown author Unknown author") and records, with reasoning,
   the five attributions Commons leaves blank.
4. **Deduplication.** `hash_manifesto.py` adds pHash/dHash so the same
   picture is not held twice under two names, here or in sibling collections.
5. **Contact sheet.** `FOLHA-DE-CONTATO.pdf` (12 A4 pages, 215 numbered
   thumbnails with captions) is the visual index.

Sourcing tool: [`venator`](https://github.com/matostf/venator) (the hunter) and the local image bank `thesaurus` (open-access
search across Wikimedia Commons, Smithsonian Open Access, Europeana, The
Met and others, with a fail-closed licence classifier).

Repository size is about 570 MB because the images are versioned at
teaching resolution; clone with `--depth 1` if you only need the current
set.

---

Coleção de obras de arte e imagens históricas em alta qualidade, baixadas do
**Wikimedia Commons**, para uso em sala de aula no Ensino Médio — da Pré-História
à Idade Contemporânea, com uma seção de História do Brasil.

Todas as imagens são de **domínio público** ou de **licença livre** (arte anterior
ao séc. XX, em sua maioria). A atribuição completa de cada peça (autor, data,
licença e página de origem no Commons) está no **`MANIFESTO.csv`** / **`MANIFESTO.json`**.

> 📄 **`FOLHA-DE-CONTATO.pdf`** — índice visual em A4 (12 páginas) com as 215 miniaturas
> numeradas e legendadas, agrupadas por período. Bom para escolher rápido o que usar.

## Como está organizado

**215 imagens** no total. Pasta única (sem subpastas): o **prefixo do nome do
arquivo** indica o período, então a ordenação alfabética já agrupa por época.

| Prefixo | Período | Nº | Conteúdo |
|---|---|--:|---|
| `00-pre-historia_…`    | Pré-História    | 13 | arte rupestre, Vênus paleolíticas, megálitos |
| `01-oriente-proximo_…` | Oriente Próximo | 25 | Mesopotâmia, Egito, Pérsia, hebreus, fenícios |
| `02-grecia_…`          | Grécia          | 19 | minoico/micênico, escultura, cerâmica, arquitetura |
| `03-roma_…`            | Roma            | 16 | escultura, arquitetura, afrescos |
| `04-idade-media_…`     | Idade Média     | 24 | Bizâncio, mundo islâmico, românico, gótico, manuscritos |
| `05-idade-moderna_…`   | Idade Moderna   | 32 | Renascimento, Reforma, Navegações, Absolutismo, Revoluções |
| `06-brasil_…`          | Brasil          | 16 | pintura acadêmica do séc. XIX e fotografia de época |
| `07-contemporanea_…`   | Idade Contemporânea | 70 | Romantismo, Impressionismo, vanguardas, fotografia histórica, Guerras Mundiais |

Exemplo: `02-grecia_kouros-de-anavysos.jpg`.

## O manifesto

`MANIFESTO.csv` (abre no LibreOffice/Excel) e `MANIFESTO.json` (mesmo conteúdo)
trazem, por imagem:

- `titulo` — o nome da obra (em PT-BR)
- `autor`, `data_obra` — autoria e data, conforme o Commons
- `licenca` — a licença declarada (ex.: *Public domain*, *CC BY-SA 4.0*)
- `credito` — crédito/atribuição sugerida
- `pagina_commons` — link para a página de origem (para checar licença e baixar o original)
- `largura`/`altura` — dimensão do arquivo baixado; `original_wxh` — dimensão do original no Commons
- `resolvido_via` — como o arquivo foi localizado (`wiki` = imagem principal do artigo; `search` = busca no Commons; `override` = arquivo fixado manualmente)

## Sobre a qualidade

As imagens foram baixadas em torno de **2000 px** no lado maior (versão "grande e
prática" renderizada pelo Commons), boa para projetar e montar slides. Quando o
original é menor que isso, foi baixado no maior tamanho disponível. Para a
resolução máxima de uma peça específica, use o link em `pagina_commons` e baixe o
arquivo original.

Cada imagem passou por uma **conferência visual** (um revisor abriu e olhou cada
arquivo) para garantir que retrata mesmo a obra pretendida — e não, por exemplo, o
retrato do artista no lugar do quadro.

## Como recriar / atualizar

O script `baixar.py` contém a lista curada e refaz tudo:

```bash
python3 baixar.py            # baixa o que falta + grava o manifesto
python3 baixar.py --dry      # só resolve e mostra, sem baixar
python3 baixar.py --redo <slug> [<slug> …]   # re-resolve/rebaixa itens específicos
```

## Atribuição e uso

Uso didático. Ao reutilizar publicamente uma imagem (apostila, post, site),
verifique a licença em `MANIFESTO.csv` e dê o crédito indicado — a maioria é
domínio público, mas algumas fotografias modernas de monumentos são *CC BY-SA* e
exigem atribuição.
