
"""Frases literárias da página inicial do Booklog."""

import random

FRASES = [
    {
        "texto": "Eles não vão usar nossas lágrimas para entretenimento",
        "livro": "Amanhecer na Colheita",
        "autor": "Suzanne Collins",
    },
    {
        "texto": "Ela descobriu que os livros são uma maneira de se viver milhares de vidas diferentes - ou de encontrar forças para viver uma muito longa",
        "livro": "A Vida Invisível de Addie LaRue",
        "autor": "V. E. Schwab",
    },
    {
        "texto": "Cresci no meio de livros, fazendo amigos invisíveis em páginas que se desfaziam em pó e cujo cheiro ainda conservo nas mãos",
        "livro": "A Sombra do Vento",
        "autor": "Carlos Ruiz Zafón",
    },
    {
        "texto": "Mas enquanto eu tiver a mim não estarei só",
        "livro": "Água Viva",
        "autor": "Clarice Lispector",
    },
    {
        "texto": "Na ausência de relacionamentos humanos, formei laços com personagens no papel",
        "livro": "Estilhaça-me",
        "autor": "Tahereh Mafi",
    },
    {
        "texto": "Há lugares incríveis mesmo em dias sombrios",
        "livro": "Por Lugares Incríveis",
        "autor": "Jennifer Niven",
    },
    {
        "texto": "As pessoas são solitárias porque constroem muros ao invés de pontes",
        "livro": "O Pequeno Príncipe",
        "autor": "Antoine de Saint-Exupéry",
    },
    {
        "texto": "Ler nos dá um lugar para ir quando precisamos ficar onde estamos",
        "livro": "A Biblioteca da Meia-Noite",
        "autor": "Matt Haig",
    },
    {
        "texto": "Esses prazeres violentos têm fins violentos.",
        "livro": "Romeu e Julieta",
        "autor": "William Shakespeare",
    },
    {
        "texto": "O mundo será salvo e refeito pelos sonhadores", 
        "livro": "Império de Tempestades",
        "autor": "Sarah J. Maas",
    },
]


def sortear_frase():
    """Seleciona uma frase preenchida aleatoriamente."""
    disponiveis = [
        frase for frase in FRASES
        if frase["texto"].strip()
    ]

    if not disponiveis:
        return {
            "texto": "Toda história começa com uma página.",
            "livro": "Booklog",
            "autor": "",
        }

    return random.choice(disponiveis)
