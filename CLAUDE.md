# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Leia o `README.md` primeiro** — a organização por período e os campos do manifesto. Aqui ficam a
> fronteira com os projetos vizinhos, o contrato que sai daqui e as regras de licença.

## A fronteira: este repo **cura + publica**

Três projetos parecidos, papéis diferentes — confundi-los é o erro mais fácil de cometer:

| Projeto | Papel |
|---|---|
| `venator` | **garimpa** — descobre imagem nova em acervos de museu |
| **este** | **cura + publica** — coleção **fixa**, escolhida à mão, verificada uma a uma |
| `thesaurus` | **guarda + vê** — banco local que **ingere** daqui |

**A regra de ouro: aqui nada é automático.** A coleção é fixa e curada; cada peça foi verificada
individualmente (assunto, autor, licença). Uma tarefa de "buscar imagens novas" pertence ao
`venator` ou à skill `reverse-search` — o que chega aqui já passou por decisão humana.

## O `MANIFESTO.json` é contrato, não arquivo interno

**215 entradas** (208 `.jpg` + 7 `.png`), com estes campos:

```
arquivo · periodo_num · periodo · slug · titulo · autor · data_obra
licenca · credito · descricao · largura · altura · original_wxh · arquivo_commons
```

**Dois repositórios consomem isto:**

- `thesaurus` → `python -m cli.banco ingest didatico` lê o manifesto e copia os JPGs full-res.
- `scriptorium` → `config.ACERVO_MANIFESTO` aponta para cá; o **license gate** dele lê `licenca` e
  `credito` e **aborta o build** se vierem vazios.

Renomear ou remover campo quebra os dois **em silêncio** — o JSON continua válido, só falta o que
importa. `MANIFESTO.csv` tem o mesmo conteúdo e precisa mudar junto.

## Licença: a razão de o projeto existir

Toda peça é **domínio público ou licença livre**, com atribuição completa (autor, data, licença,
página de origem no Commons). Esse acervo alimenta material **vendido** (apostilas da História HUB,
decks) — publicar uma imagem sem licença comercial é passivo real, e o `scriptorium` conta com este
manifesto para barrar isso.

**Nenhuma imagem entra sem os campos de licença preenchidos.** Não completar com "provavelmente
domínio público": ou se confirma na página do Commons, ou não entra.

⚠️ **URLs do Commons morrem.** O commit `6a87f0c` re-sourceou 3 obras cujas páginas do Louvre/Joconde
foram apagadas. Ao mexer no acervo, `scripts`/`auditar` de URL não é zelo — é manutenção previsível.

## Nomear é organizar

Pasta **única**, sem subpastas. O **prefixo do arquivo é o período**, então a ordenação alfabética já
agrupa por época: `02-grecia_kouros-de-anavysos.jpg`.

Prefixos: `00-pre-historia` · `01-oriente-proximo` · `02-grecia` · `03-roma` · `04-idade-media` ·
`05-idade-moderna` · `06-brasil` · `07-contemporanea`.

Nome fora do padrão não quebra o código — quebra a **navegação**, que é o produto. E o `slug` do
manifesto tem de casar com o nome do arquivo.

## Imagens SÃO versionadas aqui (ao contrário do `thesaurus`)

As 215 estão no git. É a diferença de papel: aqui a coleção **é** o repositório; no `thesaurus`,
`data/` é git-ignored porque lá o acervo é derivado e reconstruível por ingestão.

Consequência prática: o repo é pesado e todo `git add` de imagem é permanente no histórico. Conferir
licença **antes** de commitar — remover depois não apaga do histórico.

## Ferramentas

```bash
python3 baixar.py             # baixa do Commons
python3 hash_manifesto.py     # pHash — dedup contra o que já existe
python3 folha_contato_pil.py  # FOLHA-DE-CONTATO.pdf (A4, 12 páginas, 215 miniaturas)
```

A folha de contato é gerada por **Pillow**, não por Chrome headless — o headless é instável neste
ambiente para PDF de imagem (já paginou 1 slide só). Conferir a paginação (nº de páginas esperado)
antes de dar por pronto.

A skill **`acervo-imagens`** (`~/.claude/skills/acervo-imagens/`) automatiza o fluxo de curadoria
com verificação uma a uma — use-a em vez de improvisar um script novo.
