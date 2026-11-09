import json
import os
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from itsdangerous import BadData, URLSafeTimedSerializer

CATEGORIAS = ("Quero ler", "Lendo", "Lido")
CAMPOS = {"title": "intitle", "author": "inauthor"}


def atualizar_banco(conexao):
    with conexao:
        conexao.execute("BEGIN IMMEDIATE")
        colunas = {
            coluna["name"]
            for coluna in conexao.execute("PRAGMA table_info(livros)")
        }

        for nome, tipo in (
            ("catalogo_id", "TEXT"),
            ("capa_id", "INTEGER"),
            ("capa_url", "TEXT"),
        ):
            if nome not in colunas:
                conexao.execute(f"ALTER TABLE livros ADD COLUMN {nome} {tipo}")

        conexao.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS livros_catalogo_id "
            "ON livros (catalogo_id)"
        )


def assinatura():
    return URLSafeTimedSerializer(
        current_app.secret_key,
        salt="booklog-google-books",
    )


def obter_capa(info):
    imagens = info.get("imageLinks") or {}

    for campo in ("thumbnail", "smallThumbnail"):
        endereco = imagens.get(campo)
        if not endereco:
            continue

        partes = urlsplit(endereco)
        host = partes.hostname or ""
        if partes.scheme in ("http", "https") and (
            host == "books.google.com"
            or host.endswith(".googleusercontent.com")
        ):
            return urlunsplit(partes._replace(scheme="https"))

    return None


def buscar_livros(termo, campo, chave, somente_capa):
    prefixo = CAMPOS[campo]
    termo = termo.replace('"', " ").strip()
    if not termo:
        return []

    parametros = urlencode(
        {
            "q": f'{prefixo}:"{termo}"',
            "printType": "books",
            "maxResults": 30,
            "fields": (
                "items(id,volumeInfo("
                "title,authors,publishedDate,imageLinks))"
            ),
            "key": chave,
        }
    )
    consulta = Request(
        f"https://www.googleapis.com/books/v1/volumes?{parametros}",
        headers={"Accept": "application/json"},
    )

    with urlopen(consulta, timeout=10) as resposta:
        itens = json.load(resposta).get("items", [])

    livros = []
    for item in itens:
        info = item.get("volumeInfo") or {}
        volume_id = item.get("id")
        titulo = (info.get("title") or "").strip()
        capa_url = obter_capa(info)

        if not volume_id or not titulo or (somente_capa and not capa_url):
            continue

        autor = ", ".join(info.get("authors") or []) or "Autor desconhecido"
        dados = {
            "catalogo_id": f"google:{volume_id}",
            "titulo": titulo[:150],
            "autor": autor[:120],
            "capa_url": capa_url,
        }
        livros.append(
            {
                **dados,
                "ano": (info.get("publishedDate") or "")[:4],
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
        if campo not in CAMPOS:
            campo = "title"

        somente_capa = request.args.get("somente_capa") == "1"
        livros = []
        erro = None

        if termo:
            chave = os.environ.get("GOOGLE_BOOKS_API_KEY", "").strip()
            if not chave:
                erro = "Configure GOOGLE_BOOKS_API_KEY no terminal e reinicie o Flask."
            else:
                try:
                    livros = buscar_livros(termo, campo, chave, somente_capa)
                except HTTPError as resposta:
                    if resposta.code in (400, 403):
                        erro = (
                            "O Google Books recusou a consulta. Confira a chave, "
                            "as restrições dela e se a Books API está ativada."
                        )
                    elif resposta.code == 429:
                        erro = "O Google Books atingiu o limite de consultas. Tente mais tarde."
                    else:
                        erro = f"O Google Books retornou um erro (HTTP {resposta.code})."
                except (OSError, ValueError):
                    erro = "Não foi possível consultar o Google Books agora. Tente novamente."

        return render_template(
            "catalogo.html",
            livros=livros,
            termo=termo,
            campo=campo,
            somente_capa=somente_capa,
            categorias=CATEGORIAS,
            erro=erro,
        )

    @catalogo.post("/catalogo/adicionar")
    def adicionar():
        status = request.form.get("status")
        if status not in CATEGORIAS:
            flash("Escolha um status de leitura válido.", "erro")
            return redirect(url_for("catalogo.pesquisar"), code=303)

        try:
            dados = assinatura().loads(
                request.form.get("livro", ""),
                max_age=3600,
            )
        except BadData:
            flash("Essa seleção expirou. Busque o livro novamente.", "erro")
            return redirect(url_for("catalogo.pesquisar"), code=303)

        conexao = banco()
        with conexao:
            conexao.execute(
                """
                INSERT INTO livros (catalogo_id, titulo, autor, capa_url, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (catalogo_id) DO UPDATE SET
                    status = excluded.status,
                    capa_url = COALESCE(excluded.capa_url, livros.capa_url)
                """,
                (
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