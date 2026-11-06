import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
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

        conexao.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS livros_catalogo_id ON livros (catalogo_id)"
        )


def assinatura():
    return URLSafeTimedSerializer(current_app.secret_key, salt="catalogo-de-livros")


def buscar_livros(termo, campo):
    parametros = urlencode(
        {
            campo: termo,
            "fields": "key,title,author_name,cover_i,first_publish_year",
            "limit": 20,
        }
    )
    consulta = Request(
        f"https://openlibrary.org/search.json?{parametros}",
        headers={"Accept": "application/json"},
    )

    with urlopen(consulta, timeout=8) as resposta:
        documentos = json.load(resposta)["docs"]

    livros = []
    for item in documentos:
        chave = item.get("key", "").rsplit("/", 1)[-1]
        titulo = item.get("title", "").strip()
        if not re.fullmatch(r"OL\d+W", chave) or not titulo:
            continue

        autores = item.get("author_name") or []
        autor = ", ".join(autores) or "Autor desconhecido"
        capa_id = item.get("cover_i")
        if not isinstance(capa_id, int) or capa_id <= 0:
            capa_id = None

        dados = {
            "catalogo_id": chave,
            "titulo": titulo[:150],
            "autor": autor[:120],
            "capa_id": capa_id,
        }
        livros.append(
            {
                **dados,
                "ano": item.get("first_publish_year"),
                "selecao": assinatura().dumps(dados),
            }
        )

    return livros


def criar_catalogo(banco):
    catalogo = Blueprint("catalogo", __name__)

    @catalogo.get("/catalogo")
    def pesquisar():
        termo = request.args.get("q", "").strip()[:150]
        campo = request.args.get("campo", "title")
        if campo not in ("title", "author"):
            campo = "title"

        livros = []
        erro = None
        if termo:
            try:
                livros = buscar_livros(termo, campo)
            except (OSError, ValueError, KeyError):
                erro = "O catálogo não respondeu agora. Tente buscar novamente em instantes."

        return render_template(
            "catalogo.html",
            livros=livros,
            termo=termo,
            campo=campo,
            categorias=CATEGORIAS,
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
                INSERT INTO livros (catalogo_id, titulo, autor, capa_id, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (catalogo_id) DO UPDATE SET
                    status = excluded.status,
                    capa_id = COALESCE(excluded.capa_id, livros.capa_id)
                """,
                (dados["catalogo_id"], dados["titulo"], dados["autor"], dados["capa_id"], status),
            )

        flash(f"Livro salvo em «{status}».", "sucesso")
        return redirect(url_for("inicio"), code=303)

    return catalogo