# Acervo Didático de História

Coleção de obras de arte e imagens históricas em alta qualidade, baixadas do
**Wikimedia Commons**, para uso em sala de aula no Ensino Médio — da Pré-História
à Idade Moderna, com uma seção de História do Brasil.

Todas as imagens são de **domínio público** ou de **licença livre** (arte anterior
ao séc. XX, em sua maioria). A atribuição completa de cada peça (autor, data,
licença e página de origem no Commons) está no **`MANIFESTO.csv`** / **`MANIFESTO.json`**.

> 📄 **`FOLHA-DE-CONTATO.pdf`** — índice visual em A4 (8 páginas) com as 145 miniaturas
> numeradas e legendadas, agrupadas por período. Bom para escolher rápido o que usar.

## Como está organizado

**145 imagens** no total. Pasta única (sem subpastas): o **prefixo do nome do
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
