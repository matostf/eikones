#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Acervo Didático de História — coletor de obras em alta qualidade do Wikimedia Commons.

Estratégia de resolução por obra (em ordem de prioridade):
  1) commons (override): nome exato do arquivo "File:..." no Commons.
  2) wiki: artigo da Wikipédia -> imagem principal (pageimages). Resolve para a obra canônica.
  3) query: busca no Commons (namespace 6 = arquivos) e pega o melhor resultado de imagem.

Depois de resolver o nome do arquivo, consulta a API do Commons para obter o thumbnail a
~2000px (iiurlwidth) + metadados (autor, licença, crédito, descrição, data, página de origem),
baixa a imagem e grava o manifesto (CSV + JSON).

Uso:
  python3 baixar.py            # baixa tudo que ainda não existe
  python3 baixar.py --redo slug1 slug2   # re-resolve/rebaixa só esses slugs
  python3 baixar.py --dry      # só resolve e imprime, não baixa
  python3 baixar.py --check-dedup        # avisa se baixar duplicata (pHash)
  python3 baixar.py --strict-dedup       # implica --check-dedup; aborta na duplicata
"""

import json
import os
import re
import sys
import time
import html
import csv
import urllib.parse
import urllib.request

DEST = os.path.dirname(os.path.abspath(__file__))
UA = "AcervoDidaticoHistoria/1.0 (https://github.com/matostf; matostf@gmail.com) python-urllib"
THUMB_W = 2000          # largura alvo do thumbnail
TIMEOUT = 40
PAUSE = 0.15            # cortesia entre requisições

PERIODOS = {
    "00": "pre-historia",
    "01": "oriente-proximo",
    "02": "grecia",
    "03": "roma",
    "04": "idade-media",
    "05": "idade-moderna",
    "06": "brasil",
    "07": "contemporanea",
}

# ---------------------------------------------------------------------------
# LISTA MESTRA
# Cada item: dict com
#   p     = prefixo do período ("00".."06")
#   slug  = identificador curto (vira parte do nome do arquivo)
#   label = rótulo PT-BR (vai no manifesto)
#   wiki  = "lang:Título do artigo" (resolvedor principal)
#   commons (opcional) = "Nome do arquivo.jpg" (override; sem o prefixo File:)
#   q     (opcional)   = termo de busca no Commons (fallback). Default = título do wiki.
# ---------------------------------------------------------------------------
def I(p, slug, label, wiki=None, commons=None, q=None):
    return {"p": p, "slug": slug, "label": label, "wiki": wiki, "commons": commons, "q": q}

ITENS = [
    # ========================= 00 PRÉ-HISTÓRIA =========================
    I("00", "lascaux-touros",        "Pinturas rupestres de Lascaux (Salão dos Touros)", "en:Lascaux",
      q="Lascaux cave"),
    I("00", "altamira-bisao",        "Bisão da Caverna de Altamira",                     "en:Cave of Altamira"),
    I("00", "chauvet-cavalos",       "Cavalos da Caverna de Chauvet",                    "en:Chauvet Cave"),
    I("00", "cueva-de-las-manos",    "Cueva de las Manos (Argentina)",                   "en:Cueva de las Manos"),
    I("00", "venus-de-willendorf",   "Vênus de Willendorf",                              "en:Venus of Willendorf"),
    I("00", "venus-de-laussel",      "Vênus de Laussel",                                 "en:Venus of Laussel"),
    I("00", "homem-leao",            "Homem-Leão de Hohlenstein-Stadel",                 "en:Lion-man"),
    I("00", "stonehenge",            "Stonehenge",                                       "en:Stonehenge"),
    I("00", "gobekli-tepe",          "Göbekli Tepe",                                     "en:Göbekli Tepe"),
    I("00", "newgrange",             "Newgrange",                                        "en:Newgrange"),
    I("00", "bhimbetka",             "Abrigos rupestres de Bhimbetka",                   "en:Bhimbetka rock shelters"),
    I("00", "laas-geel",             "Arte rupestre de Laas Geel (Chifre da África)",    None,
      q="Laas Geel"),
    I("00", "serra-da-capivara",     "Pinturas rupestres da Serra da Capivara",          "pt:Parque Nacional da Serra da Capivara",
      q="Serra da Capivara rock painting"),

    # ===================== 01 ORIENTE PRÓXIMO ========================
    # Mesopotâmia
    I("01", "estandarte-de-ur",      "Estandarte de Ur",                                 "en:Standard of Ur"),
    I("01", "codigo-de-hamurabi",    "Estela do Código de Hamurabi",                     "en:Code of Hammurabi"),
    I("01", "portao-de-ishtar",      "Portão de Ishtar",                                 "en:Ishtar Gate"),
    I("01", "ziggurat-de-ur",        "Zigurate de Ur",                                   "en:Ziggurat of Ur"),
    I("01", "lamassu",               "Lamassu (touro alado assírio)",                    "en:Lamassu"),
    I("01", "estela-dos-abutres",    "Estela dos Abutres",                               None,
      q="Stele Vultures detail"),
    I("01", "estela-naram-sin",      "Estela da Vitória de Naram-Sin",                   "en:Victory Stele of Naram-Sin"),
    I("01", "gudea",                 "Estátua de Gudea de Lagash",                       "en:Gudea"),
    I("01", "rainha-da-noite",       "Relevo Burney (Rainha da Noite)",                  "en:Burney Relief"),
    I("01", "cacada-leoes-assurbanipal", "Caçada aos Leões de Assurbanípal",             "en:Lion Hunt of Ashurbanipal"),
    I("01", "tabua-do-diluvio",      "Tábua do Dilúvio (Épico de Gilgamesh)",            "en:Flood tablet"),
    # Egito
    I("01", "paleta-de-narmer",      "Paleta de Narmer",                                 "en:Narmer Palette"),
    I("01", "piramides-de-gize",     "Pirâmides de Gizé",                                "en:Giza pyramid complex"),
    I("01", "esfinge-de-gize",       "Grande Esfinge de Gizé",                           "en:Great Sphinx of Giza"),
    I("01", "busto-de-nefertiti",    "Busto de Nefertiti",                               "en:Nefertiti Bust"),
    I("01", "mascara-de-tutancamon", "Máscara de Tutancâmon",                            "en:Mask of Tutankhamun"),
    I("01", "escriba-sentado",       "Escriba Sentado",                                  "en:Seated Scribe"),
    I("01", "papiro-de-ani",         "Papiro de Ani (Livro dos Mortos)",                 "en:Papyrus of Ani",
      q="Book of the Dead Hunefer weighing of the heart"),
    I("01", "abu-simbel",            "Templos de Abu Simbel",                            "en:Abu Simbel"),
    I("01", "pedra-de-roseta",       "Pedra de Roseta",                                  "en:Rosetta Stone"),
    I("01", "afresco-de-nebamum",    "Pintura da tumba de Nebamum (caça nos pântanos)",  None,
      q="Nebamun fowling marshes"),
    # Pérsia
    I("01", "persepolis",            "Relevos de Persépolis (Apadana)",                  "en:Persepolis"),
    I("01", "cilindro-de-ciro",      "Cilindro de Ciro",                                 "en:Cyrus Cylinder"),
    # Hebreus / Fenícios
    I("01", "relevo-de-laquis",      "Relevo do Cerco de Laquis",                        "en:Lachish relief"),
    I("01", "sarcofago-de-ahiram",   "Sarcófago de Ahiram (alfabeto fenício)",           "en:Ahiram sarcophagus"),

    # ========================= 02 GRÉCIA ==============================
    I("02", "afresco-touros-cnossos","Afresco da Tauromaquia (Cnossos, minoico)",        "en:Bull-Leaping Fresco"),
    I("02", "mascara-de-agamenon",   "Máscara de Agamêmnon (micênica)",                  "en:Mask of Agamemnon"),
    I("02", "dama-de-auxerre",       "Dama de Auxerre",                                  "en:Lady of Auxerre"),
    I("02", "kouros-de-anavysos",    "Kouros de Anavysos (Kroisos)",                     None,
      q="Kroisos Kouros"),
    I("02", "kore-com-peplo",        "Kore com Peplo",                                   "en:Peplos Kore"),
    I("02", "vaso-francois",         "Vaso François",                                    None,
      q="Cratere François"),
    I("02", "anfora-de-exequias",    "Ânfora de Exéquias (Aquiles e Ájax jogando dados)",None,
      q="Exekias Achilles Ajax playing dice amphora Vatican"),
    I("02", "cratera-de-eufronios",  "Cratera de Eufrônios",                             "en:Euphronios Krater"),
    I("02", "menino-de-kritios",     "Menino de Kritios",                                None,
      q="Kritios Boy Acropolis Museum Athens marble"),
    I("02", "auriga-de-delfos",      "Auriga de Delfos",                                 "en:Charioteer of Delphi"),
    I("02", "discobolo",             "Discóbolo de Míron",                               "en:Discobolus"),
    I("02", "doriforo",              "Doríforo de Policleto",                            "en:Doryphoros"),
    I("02", "partenon",              "Partenon (Acrópole de Atenas)",                    "en:Parthenon",
      q="Parthenon Athens"),
    I("02", "friso-do-partenon",     "Friso do Partenon (Mármores de Elgin)",            None,
      q="Parthenon frieze horsemen"),
    I("02", "venus-de-milo",         "Vênus de Milo",                                    "en:Venus de Milo"),
    I("02", "vitoria-de-samotracia", "Vitória Alada de Samotrácia",                      "en:Winged Victory of Samothrace"),
    I("02", "laocoonte",             "Laocoonte e seus filhos",                          "en:Laocoön and His Sons"),
    I("02", "galata-moribundo",      "Gálata Moribundo",                                 "en:Dying Gaul"),
    I("02", "mosaico-de-alexandre",  "Mosaico de Alexandre (Batalha de Isso)",           "en:Alexander Mosaic"),

    # ========================= 03 ROMA ================================
    I("03", "loba-capitolina",       "Loba Capitolina",                                  "en:Capitoline Wolf"),
    I("03", "augusto-de-prima-porta","Augusto de Prima Porta",                           "en:Augustus of Prima Porta"),
    I("03", "ara-pacis",             "Ara Pacis Augustae",                               "en:Ara Pacis"),
    I("03", "coliseu",               "Coliseu",                                          "en:Colosseum"),
    I("03", "pantheon",              "Panteão de Roma",                                  "en:Pantheon, Rome"),
    I("03", "pont-du-gard",          "Pont du Gard (aqueduto romano)",                   "en:Pont du Gard"),
    I("03", "coluna-de-trajano",     "Coluna de Trajano",                                "en:Trajan's Column"),
    I("03", "arco-de-tito",          "Arco de Tito",                                     "en:Arch of Titus"),
    I("03", "arco-de-constantino",   "Arco de Constantino",                              "en:Arch of Constantine"),
    I("03", "marco-aurelio-equestre","Estátua equestre de Marco Aurélio",               "en:Equestrian Statue of Marcus Aurelius"),
    I("03", "tetrarcas",             "Retrato dos Quatro Tetrarcas",                     "en:Portrait of the Four Tetrarchs"),
    I("03", "coloso-de-constantino", "Cabeça do Colosso de Constantino",                 None,
      q="Colossus Constantine head Capitoline Museums marble"),
    I("03", "villa-dos-misterios",   "Afrescos da Villa dos Mistérios (Pompeia)",        None,
      q="Villa Misteri affreschi"),
    I("03", "retrato-de-faium",      "Retratos de Faium",                               "en:Fayum mummy portraits"),
    I("03", "maison-carree",         "Maison Carrée (Nîmes)",                            "en:Maison Carrée"),
    I("03", "casal-pompeia",         "Retrato de Terêncio Neo e sua esposa (Pompeia)",   "en:Portrait of Terentius Neo",
      q="Pompeii fresco baker Terentius Neo portrait"),

    # ====================== 04 IDADE MÉDIA ===========================
    # Bizâncio / cristianismo primitivo
    I("04", "hagia-sophia",          "Hagia Sophia (Constantinopla)",                    "en:Hagia Sophia"),
    I("04", "mosaico-justiniano",    "Mosaico de Justiniano (San Vitale, Ravena)",       None,
      commons="Mosaic of Justinianus I - Basilica San Vitale (Ravenna).jpg",
      q="Justinian court mosaic San Vitale Ravenna"),
    I("04", "mosaico-teodora",       "Mosaico da Imperatriz Teodora (San Vitale)",       "en:Theodora (wife of Justinian I)",
      q="Theodora mosaic San Vitale Ravenna"),
    I("04", "cristo-pantocrator",    "Cristo Pantocrator (mosaico da Deésis, Hagia Sophia)","en:Christ Pantocrator",
      q="Christ Pantocrator Saint Catherine Sinai icon"),
    # Mundo islâmico
    I("04", "domo-da-rocha",         "Domo da Rocha (Jerusalém)",                        "en:Dome of the Rock"),
    I("04", "mesquita-de-cordoba",   "Mesquita-Catedral de Córdoba",                     "en:Mosque–Cathedral of Córdoba"),
    I("04", "alhambra",              "Alhambra (Granada)",                               "en:Alhambra"),
    # Insular / Carolíngio / germânico
    I("04", "livro-de-kells",        "Livro de Kells",                                   "en:Book of Kells"),
    I("04", "evangelhos-lindisfarne","Evangelhos de Lindisfarne",                        "en:Lindisfarne Gospels"),
    I("04", "elmo-de-sutton-hoo",    "Elmo de Sutton Hoo",                               "en:Sutton Hoo helmet"),
    I("04", "navio-de-oseberg",      "Navio de Oseberg (viking)",                        "en:Oseberg Ship"),
    I("04", "capela-de-aachen",      "Capela Palatina de Aachen (interior octogonal)",   None,
      q="Aachen Palatine Chapel interior octagon Carolingian"),
    # Românico / Gótico
    I("04", "tapecaria-de-bayeux",   "Tapeçaria de Bayeux",                              "en:Bayeux Tapestry"),
    I("04", "catedral-de-chartres",  "Catedral de Chartres",                            "en:Chartres Cathedral"),
    I("04", "notre-dame-de-paris",   "Catedral de Notre-Dame de Paris",                  "en:Notre-Dame de Paris"),
    I("04", "sainte-chapelle",       "Sainte-Chapelle (vitrais)",                        "en:Sainte-Chapelle"),
    I("04", "mont-saint-michel",     "Mont-Saint-Michel",                               "en:Mont-Saint-Michel"),
    I("04", "krak-des-chevaliers",   "Krak dos Cavaleiros (castelo cruzado)",            "en:Krak des Chevaliers"),
    # Pintura / manuscritos baixo-medievais
    I("04", "giotto-lamentacao",     "A Lamentação — Giotto (Capela Scrovegni)",         "en:Lamentation (Giotto)",
      q="Giotto Lamentation Scrovegni Chapel"),
    I("04", "duccio-maesta",         "Maestà — Duccio di Buoninsegna",                   "en:Maestà (Duccio)"),
    I("04", "tres-riches-heures",    "Très Riches Heures du Duc de Berry (calendário, fevereiro)",
      "en:Très Riches Heures du Duc de Berry",
      commons="Les Très Riches Heures du duc de Berry février.jpg",
      q="Très Riches Heures février calendar"),
    I("04", "danca-macabra",         "Dança Macabra (Danse Macabre)",                    "en:Danse Macabre",
      q="Danse Macabre medieval woodcut death"),
    I("04", "magna-carta",           "Magna Carta",                                      "en:Magna Carta"),
    I("04", "joana-darc",            "Joana d'Arc (miniatura, séc. XV)",                 "en:Joan of Arc",
      q="Joan of Arc miniature 1450 Archives Nationales"),

    # ===================== 05 IDADE MODERNA ==========================
    # Renascimento
    I("05", "cupula-de-florenca",    "Cúpula de Brunelleschi (Catedral de Florença)",    "en:Florence Cathedral"),
    I("05", "nascimento-de-venus",   "O Nascimento de Vênus — Botticelli",               "en:The Birth of Venus"),
    I("05", "primavera-botticelli",  "A Primavera — Botticelli",                         "en:Primavera (Botticelli)"),
    I("05", "homem-vitruviano",      "Homem Vitruviano — Leonardo da Vinci",             "en:Vitruvian Man"),
    I("05", "mona-lisa",             "Mona Lisa — Leonardo da Vinci",                    "en:Mona Lisa"),
    I("05", "ultima-ceia",           "A Última Ceia — Leonardo da Vinci",                "en:The Last Supper (Leonardo)"),
    I("05", "david-de-michelangelo", "David — Michelangelo",                             "en:David (Michelangelo)"),
    I("05", "criacao-de-adao",       "A Criação de Adão — Michelangelo (Capela Sistina)","en:The Creation of Adam"),
    I("05", "escola-de-atenas",      "A Escola de Atenas — Rafael",                      "en:The School of Athens"),
    I("05", "retrato-arnolfini",     "O Casal Arnolfini — Jan van Eyck",                 "en:Arnolfini Portrait"),
    I("05", "durer-autorretrato",    "Autorretrato (1500) — Albrecht Dürer",             "en:Self-Portrait (Dürer, Munich)"),
    I("05", "torre-de-babel-bruegel","A Torre de Babel — Bruegel, o Velho",              "en:The Tower of Babel (Bruegel)"),
    # Reforma / imprensa
    I("05", "lutero-cranach",        "Retrato de Martinho Lutero — Cranach, o Velho",    "en:Martin Luther",
      q="Martin Luther portrait Lucas Cranach 1528"),
    I("05", "biblia-de-gutenberg",   "Bíblia de Gutenberg",                              "en:Gutenberg Bible"),
    I("05", "noite-de-sao-bartolomeu","O Massacre da Noite de São Bartolomeu — Dubois",  "en:St. Bartholomew's Day massacre",
      q="François Dubois St Bartholomew's Day massacre painting"),
    # Grandes Navegações (cartografia)
    I("05", "planisferio-cantino",   "Planisfério de Cantino",                          "en:Cantino planisphere"),
    I("05", "mapa-waldseemuller",    "Mapa de Waldseemüller (1507)",                     "en:Waldseemüller map"),
    # Revolução científica / Barroco
    I("05", "galileu-galilei",       "Retrato de Galileu Galilei — Sustermans",          "en:Galileo Galilei",
      q="Galileo Galilei portrait Justus Sustermans"),
    I("05", "caravaggio-sao-mateus", "A Vocação de São Mateus — Caravaggio",             "en:The Calling of Saint Matthew"),
    I("05", "ronda-noturna",         "A Ronda Noturna — Rembrandt",                      "en:The Night Watch"),
    I("05", "moca-com-brinco-perola","Moça com Brinco de Pérola — Vermeer",              "en:Girl with a Pearl Earring"),
    I("05", "las-meninas",           "As Meninas — Velázquez",                           "en:Las Meninas"),
    # Absolutismo
    I("05", "luis-xiv-rigaud",       "Retrato de Luís XIV — Hyacinthe Rigaud",           "en:Portrait of Louis XIV (Rigaud)",
      q="Louis XIV Rigaud 1701 portrait Louvre"),
    I("05", "palacio-de-versalhes",  "Palácio de Versalhes",                            "en:Palace of Versailles"),
    # Iluminismo / Revoluções / Industrial
    I("05", "experimento-bomba-de-ar","Experiência com um Pássaro na Bomba de Ar — Wright","en:An Experiment on a Bird in the Air Pump"),
    I("05", "juramento-dos-horacios","O Juramento dos Horácios — Jacques-Louis David",   "en:Oath of the Horatii"),
    I("05", "morte-de-marat",        "A Morte de Marat — Jacques-Louis David",           "en:The Death of Marat"),
    I("05", "tomada-da-bastilha",    "A Tomada da Bastilha",                             "en:Storming of the Bastille",
      q="Storming of the Bastille painting Houël"),
    I("05", "liberdade-guiando-o-povo","A Liberdade Guiando o Povo — Delacroix",         "en:Liberty Leading the People"),
    I("05", "napoleao-cruzando-os-alpes","Napoleão Cruzando os Alpes — David",           "en:Napoleon Crossing the Alps"),
    I("05", "tres-de-maio-goya",     "O Três de Maio de 1808 — Goya",                    "en:The Third of May 1808"),
    I("05", "coalbrookdale-a-noite", "Coalbrookdale à Noite — Loutherbourg (Rev. Industrial)","en:Coalbrookdale by Night"),

    # ========================= 06 BRASIL ==============================
    I("06", "primeira-missa",        "A Primeira Missa no Brasil — Vítor Meirelles",     "pt:Primeira Missa no Brasil",
      q="Primeira Missa no Brasil Meirelles 1860 pintura"),
    I("06", "desembarque-de-cabral", "Desembarque de Cabral em Porto Seguro — Oscar Pereira da Silva",None,
      q="Desembarque Cabral Oscar Pereira Silva"),
    I("06", "moema-meirelles",       "Moema — Vítor Meirelles",                          "pt:Moema (pintura)"),
    I("06", "batalha-dos-guararapes","Batalha dos Guararapes — Vítor Meirelles",         "pt:Batalha dos Guararapes (pintura)"),
    I("06", "debret-jantar",         "Cena de escravidão urbana — Jean-Baptiste Debret",  None,
      q="Debret escravos Brasil"),
    I("06", "rugendas-escravidao",   "Navio negreiro (porão) — Johann Moritz Rugendas",   None,
      q="Rugendas navio negreiro porão escravos"),
    I("06", "independencia-ou-morte","Independência ou Morte (O Grito do Ipiranga) — Pedro Américo","pt:Independência ou Morte (pintura)"),
    I("06", "batalha-do-avai",       "Batalha do Avaí — Pedro Américo",                  None,
      commons="Batalha do Avaí.jpg",
      q="Pedro Américo Batalha Avaí Google Art"),
    I("06", "partida-da-moncao",     "Partida da Monção — Almeida Júnior",               "pt:Partida da Monção"),
    I("06", "caipira-picando-fumo",  "Caipira Picando Fumo — Almeida Júnior",            "pt:Caipira Picando Fumo"),
    I("06", "redencao-de-cam",       "A Redenção de Cam — Modesto Brocos",               "pt:A Redenção de Cam"),
    I("06", "proclamacao-da-republica","Proclamação da República — Benedito Calixto",    None,
      q="Proclamação da República Benedito Calixto 1893"),
    I("06", "alegoria-da-republica", "Estudo para a Proclamação da República — Henrique Bernardelli", None,
      q="Bernardelli República"),
    I("06", "marc-ferrez-rio",       "Rio de Janeiro no séc. XIX — fotografia de Marc Ferrez","pt:Marc Ferrez (fotógrafo)",
      q="Marc Ferrez Rio de Janeiro photograph 19th century"),
    I("06", "dom-pedro-ii",          "Retrato de Dom Pedro II",                          "pt:Pedro II do Brasil",
      q="Pedro II Brazil portrait photograph"),
    I("06", "tiradentes-pedro-americo","Tiradentes Esquartejado — Pedro Américo",        "pt:Tiradentes Esquartejado"),

    # ====================== 07 CONTEMPORÂNEA =========================
    # ----- A. Restauração e Romantismo (1815-1848)
    I("07", "congresso-de-viena",    "O Congresso de Viena — Isabey",                    "de:Wiener Kongress",
      q="Isabey Kongress 1815"),
    I("07", "caminhante-mar-de-nevoa","Caminhante sobre o Mar de Névoa — Caspar David Friedrich",
      "en:Wanderer above the Sea of Fog"),
    I("07", "balsa-da-medusa",       "A Balsa da Medusa — Théodore Géricault",           "en:The Raft of the Medusa"),
    I("07", "massacre-de-quios",     "O Massacre de Quios — Delacroix",                  "en:The Massacre at Chios"),
    I("07", "republica-universal-sorrieu","República Universal Democrática e Social — Sorrieu (1848)", None,
      q="Sorrieu République universelle démocratique sociale 1848"),
    I("07", "proclamacao-imperio-alemao","Proclamação do Império Alemão em Versalhes — Anton von Werner",
      "en:Proclamation of the German Empire",
      q="Anton von Werner Kaiserproklamation Versailles 1885"),

    # ----- B. Realismo, 1ª Rev. Industrial (1850-1880)
    I("07", "britadores-de-pedra",   "Os Britadores de Pedras — Gustave Courbet",        "en:The Stone Breakers"),
    I("07", "enterro-em-ornans",     "Um Enterro em Ornans — Gustave Courbet",           "en:A Burial at Ornans"),
    I("07", "respigadoras",          "As Respigadoras — Jean-François Millet",           "en:The Gleaners"),
    I("07", "vagao-terceira-classe", "O Vagão de Terceira Classe — Honoré Daumier",      "en:The Third-Class Carriage"),
    I("07", "forja-menzel",          "A Forja (Eisenwalzwerk) — Adolph von Menzel (1875)", None,
      q="Menzel Eisenwalzwerk 1875"),
    I("07", "iron-and-coal",         "Iron and Coal — William Bell Scott (Newcastle, 1861)",
      "en:Iron and Coal",
      q="William Bell Scott Iron Coal"),
    I("07", "crystal-palace-1851",   "Crystal Palace — Grande Exposição de Londres (1851)","en:Great Exhibition",
      q="Great Exhibition 1851 Crystal Palace Hyde Park Dickinson lithograph"),

    # ----- C. Belle Époque, Impressionismo, Pós-Impressionismo (1870-1910)
    I("07", "impressao-nascer-do-sol","Impressão, Nascer do Sol — Claude Monet",          "en:Impression, Sunrise"),
    I("07", "bal-moulin-galette",    "Baile no Moulin de la Galette — Pierre-Auguste Renoir",
      "en:Bal du moulin de la Galette"),
    I("07", "moulin-rouge-cartaz",   "Cartaz do Moulin Rouge (La Goulue) — Toulouse-Lautrec (1891)",
      None,
      commons="Lautrec moulin rouge, la goulue (poster) 1891.jpg",
      q="Lautrec Moulin Rouge La Goulue 1891 lithograph poster"),
    I("07", "noite-estrelada",       "A Noite Estrelada — Vincent van Gogh",             "en:The Starry Night"),
    I("07", "comedores-de-batatas",  "Os Comedores de Batatas — Vincent van Gogh",       "en:The Potato Eaters"),
    I("07", "grandes-banhistas",     "Os Grandes Banhistas — Paul Cézanne",              "en:The Large Bathers (Cézanne)",
      q="Cézanne Large Bathers Philadelphia"),
    I("07", "torre-eiffel-1889",     "Torre Eiffel na inauguração (1889)",               "en:Eiffel Tower",
      q="Eiffel Tower 1889 construction"),
    I("07", "estatua-da-liberdade-1886","Estátua da Liberdade (Nova York, 1886)",        "en:Statue of Liberty",
      q="Statue of Liberty 1886 unveiling"),

    # ----- D. Imperialismo e 2ª Rev. Industrial (1870-1914)
    I("07", "rhodes-colossus",       "O Colosso Rhodes — caricatura (Punch, 1892)",      None,
      commons="Punch Rhodes Colossus.png",
      q="Rhodes Colossus Punch 1892"),
    I("07", "conferencia-de-berlim-1884","Conferência de Berlim (1884-85) — gravura",     "en:Berlin Conference",
      q="Kongokonferenz 1884 Berlin Bismarck Africa engraving"),
    I("07", "white-mans-burden-judge","O Fardo do Homem Branco — Victor Gillam (Judge, 1899)",
      "en:The White Man's Burden",
      q="White Man's Burden cartoon"),
    I("07", "boxer-rebellion-aliados","Tropas das Oito Nações na Rebelião dos Boxers (1900)",
      None,
      q="Eight Nation Alliance soldiers Boxer Rebellion 1900 group photograph"),
    I("07", "cecil-rhodes-retrato",  "Retrato de Cecil Rhodes",                          "en:Cecil Rhodes",
      q="Cecil Rhodes portrait photograph"),
    I("07", "henri-rousseau-o-sonho","O Sonho — Henri Rousseau (1910)",                  "en:The Dream (Rousseau painting)"),

    # ----- E. 1ª Guerra Mundial (1914-1918)
    I("07", "gassed-sargent",        "Gassed (Gaseado) — John Singer Sargent (1919)",    "en:Gassed (painting)"),
    I("07", "we-are-making-a-new-world","Estamos Construindo um Mundo Novo — Paul Nash (1918)", None,
      q="Paul Nash We Are Making a New World 1918"),
    I("07", "paths-of-glory-nevinson","Caminhos da Glória — C.R.W. Nevinson (1917)",      None,
      q="Nevinson Paths of Glory 1917 Imperial War Museum"),
    I("07", "trincheiras-somme-foto","Soldados britânicos nas trincheiras do Somme (1916)", None,
      q="Battle of the Somme trench July 1916 official photograph"),
    I("07", "kitchener-wants-you",   "Lord Kitchener Quer Você — cartaz de Alfred Leete (1914)",
      "en:Lord Kitchener Wants You",
      q="Kitchener Wants You poster 1914"),

    # ----- F. Revolução Russa (1917)
    I("07", "lenin-discursando-1920","Lenin discursa em Sverdlov Square (1920)",         "en:Vladimir Lenin",
      q="Lenin speech Sverdlov Square 1920"),
    I("07", "bolchevique-kustodiev", "O Bolchevique — Boris Kustodiev (1920)",           None,
      q="Kustodiev Bolshevik 1920 Tretyakov"),
    I("07", "cartaz-moor-voluntario","Você se alistou como voluntário? — Dmitry Moor (1920)", None,
      q="Moor Did You Volunteer poster 1920"),
    I("07", "czar-nicolau-ii-familia","Família imperial Romanov (1913)",                  "en:Nicholas II of Russia",
      q="Romanov family portrait 1913 Nicholas II Alexandra children"),

    # ----- G. Vanguardas (1893-1930)
    I("07", "o-grito",               "O Grito — Edvard Munch (1893)",                    "en:The Scream"),
    I("07", "composicao-mondrian",   "Composição com Vermelho, Azul e Amarelo — Piet Mondrian",
      "en:Composition with Red, Blue and Yellow"),
    I("07", "composicao-viii-kandinsky","Composição VIII — Wassily Kandinsky (1923)",     None,
      q="Kandinsky Composition VIII 1923 Guggenheim"),
    I("07", "cidade-que-se-ergue-boccioni","A Cidade que se Ergue — Umberto Boccioni (1910)","en:The City Rises"),
    I("07", "suprematismo-malevich", "Composição suprematista — Kazimir Malevich (1916)","en:Suprematism",
      q="Malevich Suprematism Composition 1916"),

    # ----- H. Entreguerras: crise e fascismos (1919-1939)
    I("07", "multidao-wall-street-1929","Multidão em Wall Street após o Crash (1929)",    None,
      q="Wall Street crash October 1929 crowd photograph"),
    I("07", "migrant-mother",        "Migrant Mother — Dorothea Lange (1936)",           "en:Migrant Mother"),
    I("07", "mussolini-marcha-sobre-roma","Marcha sobre Roma — Mussolini e camisas-negras (1922)",
      "en:March on Rome",
      q="Mussolini March on Rome 1922 blackshirts"),
    I("07", "hitler-nuremberg-1934", "Comício do Partido Nazista em Nuremberg (1934)",   None,
      q="Bundesarchiv Reichsparteitag Nuremberg 1934"),
    I("07", "arbeit-macht-frei",     "Portão Arbeit macht frei — Auschwitz I",           None,
      q="Auschwitz Arbeit macht frei gate entrance"),
    I("07", "ruinas-guernica-bombardeio","Ruínas de Guernica após o bombardeio (1937)",   "en:Bombing of Guernica",
      q="Bombing of Guernica 1937 ruins Bundesarchiv"),

    # ----- I. 2ª Guerra Mundial (1939-1945)
    I("07", "invasao-polonia-1939",  "Tanques alemães invadem a Polônia (1939)",         None,
      q="Bundesarchiv Polen invasion September 1939 Panzer"),
    I("07", "iwo-jima-rosenthal",    "Hasteamento da bandeira em Iwo Jima — Joe Rosenthal (1945)",
      "en:Raising the Flag on Iwo Jima"),
    I("07", "cogumelo-nagasaki",     "Cogumelo atômico sobre Nagasaki (1945)",           None,
      q="Atomic cloud Nagasaki B-29 1945"),
    I("07", "bandeira-sobre-reichstag","Bandeira sobre o Reichstag — Yevgeny Khaldei (1945)",
      "en:Raising a Flag over the Reichstag"),
    I("07", "libertacao-buchenwald", "Libertação de Buchenwald — fotografia do US Army (1945)", None,
      q="Buchenwald liberation April 1945 US Army"),

    # ----- J. Brasil — Abolição (1888)
    I("07", "lei-aurea-fac-simile",  "Lei Áurea — fac-símile (1888)",                    "pt:Lei Áurea",
      q="Lei Áurea manuscrito 1888"),
    I("07", "princesa-isabel-retrato","Retrato da Princesa Isabel",                       "pt:Isabel do Brasil",
      q="Princesa Isabel retrato 1888"),
    I("07", "joaquim-nabuco-retrato","Retrato de Joaquim Nabuco",                        "pt:Joaquim Nabuco",
      q="Joaquim Nabuco photograph abolicionista"),
    I("07", "jose-do-patrocinio-retrato","Retrato de José do Patrocínio",                 "pt:José do Patrocínio",
      q="José do Patrocínio photograph abolicionista"),

    # ----- K. Brasil — Cangaço (1920-1938)
    I("07", "lampiao-bando",         "Lampião e seu bando — foto de Benjamin Abrahão (1936)", "en:Lampião",
      q="Virgulino Ferreira cangaceiro retrato"),
    I("07", "lampiao-maria-bonita",  "Lampião e Maria Bonita — Benjamin Abrahão",        "pt:Maria Bonita",
      q="Maria Bonita Lampião casal cangaço"),

    # ----- L. Brasil — Era Vargas (1930-1954)
    I("07", "vargas-revolucao-1930", "Getúlio Vargas chega ao Rio (Revolução de 1930)",  "pt:Revolução de 1930",
      q="Vargas Revolução 1930 chegada Rio de Janeiro"),
    I("07", "coluna-prestes-foto",   "Coluna Prestes — fotografia (1925-27)",            "pt:Coluna Prestes",
      q="Coluna Prestes Luís Carlos Prestes 1925"),
    I("07", "vargas-retrato-presidencial","Getúlio Vargas — retrato presidencial (Era Vargas)","pt:Getúlio Vargas",
      q="Getúlio Vargas presidente Estado Novo"),
    I("07", "revolucao-constitucionalista-1932","Revolução Constitucionalista de 1932 — São Paulo","pt:Revolução Constitucionalista de 1932",
      q="Revolução Constitucionalista 1932 São Paulo soldados MMDC"),
    I("07", "prestes-pacaembu-1945",  "Luís Carlos Prestes anistiado — Pacaembu (1945)", "pt:Luís Carlos Prestes",
      q="Luís Carlos Prestes Pacaembu 1945 comício"),

    # ----- M. II Reich — Alemanha imperial (1871-1918)
    I("07", "kaiser-wilhelm-ii-retrato","Retrato do Kaiser Guilherme II",                 None,
      q="Kaiser Wilhelm II 1902 cropped portrait photograph"),
    I("07", "bismarck-retrato",      "Retrato de Otto von Bismarck",                     "en:Otto von Bismarck",
      q="Otto von Bismarck portrait photograph 1880"),

    # ----- N. Sufragistas (1900-1928)
    I("07", "pankhurst-discurso",    "Emmeline Pankhurst em discurso (Londres)",         "en:Emmeline Pankhurst",
      q="Emmeline Pankhurst speech arrest photograph"),
    I("07", "cartaz-votes-for-women","Cartaz Votes for Women — movimento sufragista",    None,
      q="Votes for Women suffragette poster Hilda Dallas"),
    I("07", "marcha-sufragio-1913-washington","Marcha pelo sufrágio em Washington (1913)", None,
      q="Suffrage parade Washington 1913 procession"),

    # ----- O. Sionismo (1897-1948)
    I("07", "theodor-herzl-retrato", "Retrato de Theodor Herzl",                         "en:Theodor Herzl",
      q="Theodor Herzl portrait photograph"),
    I("07", "primeiro-congresso-sionista-1897","1º Congresso Sionista em Basileia (1897)","en:First Zionist Congress",
      q="First Zionist Congress Basel 1897 delegates"),
]

# ---------------------------------------------------------------------------
# Infraestrutura HTTP
# ---------------------------------------------------------------------------
def http_json(base, params):
    url = base + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for tent in range(3):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if tent == 2:
                print(f"      ! erro HTTP: {e}")
                return None
            time.sleep(1.0 + tent)
    return None

def strip_html(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# ---------------------------------------------------------------------------
# Resolução do nome do arquivo no Commons
# ---------------------------------------------------------------------------
def resolve_via_wiki(spec):
    """spec = 'lang:Título' -> nome do arquivo (pageimage) ou None."""
    if not spec or ":" not in spec:
        return None
    lang, title = spec.split(":", 1)
    base = f"https://{lang}.wikipedia.org/w/api.php"
    data = http_json(base, {
        "action": "query", "titles": title, "prop": "pageimages",
        "piprop": "name|original", "format": "json", "formatversion": "2",
    })
    if not data:
        return None
    pages = data.get("query", {}).get("pages", [])
    if not pages:
        return None
    pg = pages[0]
    if pg.get("missing"):
        return None
    return pg.get("pageimage")

def resolve_via_search(query):
    """Busca no Commons (namespace 6) e devolve o melhor arquivo de imagem."""
    base = "https://commons.wikimedia.org/w/api.php"
    data = http_json(base, {
        "action": "query", "generator": "search",
        "gsrsearch": query, "gsrnamespace": "6", "gsrlimit": "12",
        "prop": "imageinfo", "iiprop": "url|size|mime", "iiurlwidth": str(THUMB_W),
        "format": "json", "formatversion": "2",
    })
    if not data:
        return None
    pages = data.get("query", {}).get("pages", [])
    # ordena pela posição do resultado de busca
    pages.sort(key=lambda p: p.get("index", 999))
    for pg in pages:
        ii = pg.get("imageinfo", [{}])[0]
        mime = ii.get("mime", "")
        w = ii.get("width", 0)
        if mime in ("image/jpeg", "image/png") and w >= 700:
            return pg.get("title", "").replace("File:", "")
    return None

def file_info(filename):
    """Consulta a API do Commons para thumb @THUMB_W + metadados."""
    base = "https://commons.wikimedia.org/w/api.php"
    data = http_json(base, {
        "action": "query", "titles": "File:" + filename,
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": str(THUMB_W),
        "format": "json", "formatversion": "2",
    })
    if not data:
        return None
    pages = data.get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
        return None
    ii = pages[0].get("imageinfo", [None])[0]
    if not ii:
        return None
    em = ii.get("extmetadata", {})
    def emv(k):
        return strip_html(em.get(k, {}).get("value", ""))
    return {
        "thumburl": ii.get("thumburl") or ii.get("url"),
        "thumbwidth": ii.get("thumbwidth", ii.get("width")),
        "thumbheight": ii.get("thumbheight", ii.get("height")),
        "fullwidth": ii.get("width"),
        "fullheight": ii.get("height"),
        "mime": ii.get("mime", ""),
        "descriptionurl": ii.get("descriptionurl", ""),
        "artist": emv("Artist"),
        "date": emv("DateTimeOriginal") or emv("DateTime"),
        "license": emv("LicenseShortName"),
        "license_url": em.get("LicenseUrl", {}).get("value", ""),
        "credit": emv("Credit"),
        "objectname": emv("ObjectName"),
        "description": emv("ImageDescription")[:400],
    }

def resolve(item):
    """Devolve (filename, via) ou (None, None)."""
    if item.get("commons"):
        fn = item["commons"]
        if file_info(fn):
            return fn, "override"
    fn = resolve_via_wiki(item.get("wiki"))
    if fn and file_info(fn):
        return fn, "wiki"
    q = item.get("q") or (item.get("wiki", "").split(":", 1)[-1] if item.get("wiki") else item["label"])
    fn = resolve_via_search(q)
    if fn and file_info(fn):
        return fn, "search"
    return None, None

# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
def ext_from_url(url):
    path = urllib.parse.urlparse(url).path.lower()
    for e in (".jpg", ".jpeg", ".png"):
        if path.endswith(e):
            return ".jpg" if e == ".jpeg" else e
    return ".jpg"

def download(url, dest_path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for tent in range(3):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                data = r.read()
            if len(data) < 3000:
                raise ValueError(f"arquivo muito pequeno ({len(data)} bytes)")
            with open(dest_path, "wb") as f:
                f.write(data)
            return len(data)
        except Exception as e:
            if tent == 2:
                print(f"      ! erro download: {e}")
                return 0
            time.sleep(1.0 + tent)
    return 0


# ---------------------------------------------------------------------------
# Dedup: integrações opcionais com `~/Projetos/acervo-historia/app/reverse`.
# Carregadas só se `--check-dedup` for passado, para não introduzir
# dependência obrigatória de Pillow/imagehash.
# ---------------------------------------------------------------------------
def _load_dedup_helpers():
    """Importa hasher do acervo-historia e devolve (hash_from_path, dedup_against)."""
    import sys as _sys
    from pathlib import Path as _Path

    sibling = _Path(__file__).resolve().parent.parent / "acervo-historia"
    if not sibling.exists():
        raise RuntimeError(
            "--check-dedup requer ../acervo-historia/ ao lado deste projeto"
        )
    _sys.path.insert(0, str(sibling))
    from app.reverse.dedup import dedup_against  # noqa: E402
    from app.reverse.hasher import hash_from_path  # noqa: E402

    return hash_from_path, dedup_against


def _load_existing_manifest():
    p = os.path.join(DEST, "MANIFESTO.json")
    if not os.path.exists(p):
        return []
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return [e for e in data if isinstance(e, dict) and e.get("phash")]
    except Exception:
        return []

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    dry = "--dry" in args
    check_dedup = "--check-dedup" in args
    strict_dedup = "--strict-dedup" in args  # implica check-dedup; aborta na duplicata
    if strict_dedup:
        check_dedup = True
    redo = []
    if "--redo" in args:
        idx = args.index("--redo")
        redo = args[idx + 1:]

    # Inicialização do dedup (lazy): carrega helpers só se foi pedido,
    # evita dependência obrigatória de Pillow/imagehash.
    hash_from_path = None
    dedup_against = None
    existing_for_dedup = []
    if check_dedup:
        try:
            hash_from_path, dedup_against = _load_dedup_helpers()
            existing_for_dedup = _load_existing_manifest()
            print(f"[dedup] manifesto base: {len(existing_for_dedup)} entradas com phash")
        except Exception as e:
            print(f"[dedup] ! desativado: {e}")
            check_dedup = False
            strict_dedup = False

    manifest = []
    falhas = []
    n_ok = 0
    n_dups = 0

    for it in ITENS:
        if redo and it["slug"] not in redo:
            continue
        periodo = PERIODOS[it["p"]]
        nome_base = f"{it['p']}-{periodo}_{it['slug']}"
        print(f"[{it['p']}] {it['slug']:32s} {it['label'][:50]}")

        fn, via = resolve(it)
        if not fn:
            print("      X NÃO RESOLVIDO")
            falhas.append({**it, "motivo": "nao-resolvido"})
            time.sleep(PAUSE)
            continue

        info = file_info(fn)
        if not info or not info.get("thumburl"):
            print("      X sem thumburl")
            falhas.append({**it, "motivo": "sem-thumburl", "arquivo": fn})
            time.sleep(PAUSE)
            continue

        ext = ext_from_url(info["thumburl"])
        nome_arq = nome_base + ext
        dest_path = os.path.join(DEST, nome_arq)
        print(f"      -> {fn}  [{via}]  {info['thumbwidth']}x{info['thumbheight']}")

        if dry:
            n_ok += 1
            time.sleep(PAUSE)
            continue

        size = download(info["thumburl"], dest_path)
        if not size:
            falhas.append({**it, "motivo": "download-falhou", "arquivo": fn})
            time.sleep(PAUSE)
            continue

        print(f"         {nome_arq}  ({size//1024} KB)")

        # Compute pHash/dHash da imagem baixada — sempre que hasher estiver disponível.
        phash = dhash = None
        if hash_from_path is not None:
            try:
                h = hash_from_path(dest_path)
                phash, dhash = h.phash, h.dhash
            except Exception as e:
                print(f"      (dedup: erro hashing — {e})")

        # Se check-dedup, comparar contra manifesto existente.
        if check_dedup and phash and existing_for_dedup:
            from app.reverse.hasher import ImageHashes as _IH  # noqa: E402

            cand = _IH(phash=phash, dhash=dhash or phash, width=info["thumbwidth"], height=info["thumbheight"])
            # Excluir auto-match (mesmo slug, caso de --redo).
            others = [e for e in existing_for_dedup if e.get("slug") != it["slug"]]
            verdict = dedup_against(cand, others)
            if verdict["is_duplicate"]:
                best = verdict["best_match"]
                label = (best.get("slug") or best.get("titulo") or "?") if best else "?"
                d = best.get("distance", "?") if best else "?"
                n_dups += 1
                print(f"      ⚠ DUPLICATA: similar a '{label}' (pHash dist={d})")
                if strict_dedup:
                    print(f"      → abortando entrada (modo --strict-dedup)")
                    try:
                        os.remove(dest_path)
                    except OSError:
                        pass
                    falhas.append({**it, "motivo": "duplicata-strict", "duplicata_de": label})
                    time.sleep(PAUSE)
                    continue

        entry = {
            "arquivo": nome_arq,
            "periodo_num": it["p"],
            "periodo": periodo,
            "slug": it["slug"],
            "titulo": it["label"],
            "autor": info["artist"],
            "data_obra": info["date"],
            "licenca": info["license"],
            "credito": info["credit"],
            "descricao": info["description"],
            "largura": info["thumbwidth"],
            "altura": info["thumbheight"],
            "original_wxh": f"{info['fullwidth']}x{info['fullheight']}",
            "arquivo_commons": fn,
            "pagina_commons": info["descriptionurl"],
            "resolvido_via": via,
        }
        if phash:
            entry["phash"] = phash
            entry["dhash"] = dhash
        manifest.append(entry)
        n_ok += 1
        time.sleep(PAUSE)

    # grava manifesto (merge com existente se for --redo)
    if not dry and manifest:
        json_path = os.path.join(DEST, "MANIFESTO.json")
        existing = []
        if redo and os.path.exists(json_path):
            with open(json_path, encoding="utf-8") as f:
                existing = json.load(f)
            by_slug = {m["slug"]: m for m in existing}
            for m in manifest:
                by_slug[m["slug"]] = m
            manifest_final = sorted(by_slug.values(), key=lambda m: (m["periodo_num"], m["slug"]))
        else:
            manifest_final = sorted(manifest, key=lambda m: (m["periodo_num"], m["slug"]))

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(manifest_final, f, ensure_ascii=False, indent=2)
        csv_path = os.path.join(DEST, "MANIFESTO.csv")
        cols = ["arquivo", "periodo_num", "periodo", "slug", "titulo", "autor",
                "data_obra", "licenca", "credito", "largura", "altura",
                "original_wxh", "arquivo_commons", "pagina_commons", "resolvido_via", "descricao"]
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for m in manifest_final:
                w.writerow(m)
        print(f"\nManifesto: {len(manifest_final)} itens -> MANIFESTO.json / MANIFESTO.csv")

    dups_msg = f"  duplicatas={n_dups}" if check_dedup else ""
    print(f"\n==== RESUMO ====  ok={n_ok}  falhas={len(falhas)}{dups_msg}")
    if falhas:
        print("Falhas:")
        for fl in falhas:
            print(f"  - [{fl['p']}] {fl['slug']}: {fl['motivo']}")
        with open(os.path.join(DEST, "_falhas.json"), "w", encoding="utf-8") as f:
            json.dump(falhas, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
