import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for
from itsdangerous import BadData, URLSafeTimedSerializer

CATEGORIAS = ("Quero ler", "Lendo", "Lido")


def atualizar_banco(conexao):
    """Adiciona as colunas do catálogo também aos bancos já existentes."""
    with conexao:
        conexao.execute("BEGIN IMMEDIATE")
        colunas = {coluna["name"] for coluna in conexao.execute("PRAGMA table_info(livros)")}

        if "catalogo_id" not in colunas:
            conexao.execute("ALTER TABLE livros ADD COLUMN catalogo_id TEXT")

        if "capa_id" not in colunas:
            conexao.execute("ALTER TABLE livros ADD COLUMN capa_id INTEGER")

        if "capa_url" not in colunas:
            conexao.execute("ALTER TABLE livros ADD COLUMN capa_url TEXT")


def assinatura():
    return URLSafeTimedSerializer(current_app.secret_key, salt="catalogo-de-livros")


def chave_google():
    """Lê a chave da variável de ambiente ou do arquivo .env (que fica fora do Git)."""
    chave = os.environ.get("GOOGLE_BOOKS_KEY")
    if chave:
        return chave.strip()

    arquivo = Path(__file__).resolve().parent / ".env"
    if arquivo.exists():
        # "utf-8-sig" ignora o caractere invisível que o Bloco de Notas às vezes coloca no início.
        for linha in arquivo.read_text(encoding="utf-8-sig").splitlines():
            nome, _, valor = linha.partition("=")
            if nome.strip() == "GOOGLE_BOOKS_KEY":
                return valor.strip().strip("\"'")
    return None


def baixar_json(endereco):
    consulta = Request(endereco, headers={"Accept": "application/json"})
    with urlopen(consulta, timeout=8) as resposta:
        return json.load(resposta)


def preparar(dados, ano):
    return {
        **dados,
        "ano": ano,
        "selecao": assinatura().dumps(dados),
    }


def buscar_google(termo, campo):
    filtro = "intitle" if campo == "title" else "inauthor"
    parametros = {
        "q": f"{filtro}:{termo}",
        "printType": "books",
        "maxResults": 20,
        "fields": "items(id,volumeInfo(title,subtitle,authors,publishedDate,imageLinks))",
    }
    chave = chave_google()
    if chave:
        parametros["key"] = chave
    else:
        current_app.logger.warning(
            "Nenhuma chave do Google encontrada. Confira o arquivo .env ao lado do app.py."
        )

    volumes = baixar_json(
        f"https://www.googleapis.com/books/v1/volumes?{urlencode(parametros)}"
    ).get("items", [])

    livros = []
    for item in volumes:
        volume_id = item.get("id", "")
        info = item.get("volumeInfo", {})
        titulo = info.get("title", "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{4,30}", volume_id) or not titulo:
            continue

        subtitulo = info.get("subtitle", "").strip()
        if subtitulo:
            titulo = f"{titulo}: {subtitulo}"

        autor = ", ".join(info.get("authors") or []) or "Autor desconhecido"
        capa = None
        if info.get("imageLinks"):
            capa = (
                f"https://books.google.com/books/content?id={volume_id}"
                "&printsec=frontcover&img=1&zoom=1&source=gbs_api"
            )
        ano = info.get("publishedDate", "")[:4]

        livros.append(
            preparar(
                {
                    "catalogo_id": f"gb:{volume_id}",
                    "titulo": titulo[:150],
                    "autor": autor[:120],
                    "capa_url": capa,
                },
                ano if ano.isdigit() else None,
            )
        )
    return livros


def buscar_open_library(termo, campo):
    parametros = urlencode(
        {
            campo: termo,
            "fields": "key,title,author_name,cover_i,first_publish_year",
            "limit": 20,
        }
    )
    documentos = baixar_json(f"https://openlibrary.org/search.json?{parametros}")["docs"]

    livros = []
    for item in documentos:
        chave = item.get("key", "").rsplit("/", 1)[-1]
        titulo = item.get("title", "").strip()
        if not re.fullmatch(r"OL\d+W", chave) or not titulo:
            continue

        autor = ", ".join(item.get("author_name") or []) or "Autor desconhecido"
        capa_id = item.get("cover_i")
        capa = None
        if isinstance(capa_id, int) and capa_id > 0:
            capa = f"https://covers.openlibrary.org/b/id/{capa_id}-M.jpg?default=false"

        livros.append(
            preparar(
                {
                    "catalogo_id": chave,
                    "titulo": titulo[:150],
                    "autor": autor[:120],
                    "capa_url": capa,
                },
                item.get("first_publish_year"),
            )
        )
    return livros


def buscar_livros(termo, campo):
    """Tenta o Google Books e, se ele falhar, usa a Open Library."""
    try:
        livros, fonte = buscar_google(termo, campo), "Google Books"
    except HTTPError as erro:
        detalhe = erro.read().decode("utf-8", "replace")[:300]
        current_app.logger.warning("Google Books respondeu %s: %s", erro.code, detalhe)
        livros, fonte = buscar_open_library(termo, campo), "Open Library"
    except (OSError, ValueError, KeyError) as erro:
        current_app.logger.warning("Google Books falhou: %r", erro)
        livros, fonte = buscar_open_library(termo, campo), "Open Library"

    # Livros com capa aparecem primeiro.
    livros.sort(key=lambda livro: livro["capa_url"] is None)
    return livros, fonte


def criar_catalogo(banco):
    catalogo = Blueprint("catalogo", __name__)

    @catalogo.get("/catalogo")
    def pesquisar():
        termo = request.args.get("q", "").strip()[:150]
        campo = request.args.get("campo", "title")
        if campo not in ("title", "author"):
            campo = "title"

        livros = []
        fonte = None
        erro = None
        if termo:
            try:
                livros, fonte = buscar_livros(termo, campo)
            except (OSError, ValueError, KeyError) as falha:
                current_app.logger.warning("Open Library também falhou: %r", falha)
                erro = "O catálogo não respondeu agora. Tente buscar novamente em instantes."

        return render_template(
            "catalogo.html",
            livros=livros,
            termo=termo,
            campo=campo,
            categorias=CATEGORIAS,
            fonte=fonte,
            erro=erro,
        )

    @catalogo.post("/catalogo/adicionar")
    def adicionar():
        status = request.form.get("status")
        try:
            dados = assinatura().loads(request.form.get("livro", ""), max_age=3600)
        except BadData:
            flash("Essa seleção expirou. Busque o livro novamente.", "erro")
            return redirect(url_for("catalogo.pesquisar"), code=303)

        if status not in CATEGORIAS:
            flash("Escolha um status de leitura válido.", "erro")
            return redirect(url_for("catalogo.pesquisar"), code=303)

        conexao = banco()
        with conexao:
            conexao.execute(
                """
                INSERT INTO livros (usuario_id, catalogo_id, titulo, autor, capa_url, status)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (usuario_id, catalogo_id) DO UPDATE SET
                    status = excluded.status,
                    capa_url = COALESCE(excluded.capa_url, livros.capa_url)
                """,
                (
                    g.usuario["id"],
                    dados["catalogo_id"],
                    dados["titulo"],
                    dados["autor"],
                    dados["capa_url"],
                    status,
                ),
            )

        flash(f"Livro salvo em «{status}».", "sucesso")
        return redirect(url_for("inicio"), code=303)

    return catalogo