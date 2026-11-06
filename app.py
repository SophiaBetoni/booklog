import secrets
import sqlite3
import unicodedata
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, url_for

from catalogo import atualizar_banco, criar_catalogo

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024

PASTA = Path(__file__).resolve().parent
BANCO = PASTA / "estante.db"
CHAVE_LOCAL = PASTA / ".chave-local"

STATUS = ("Quero ler", "Lendo", "Lido")
ABAS = ("estante", "resenhas", "listas")

# Mantém a chave entre reinicializações. O arquivo fica fora do Git.
try:
    with CHAVE_LOCAL.open("xb") as arquivo:
        arquivo.write(secrets.token_bytes(32))
except FileExistsError:
    pass

app.secret_key = CHAVE_LOCAL.read_bytes()


def banco():
    if "banco" not in g:
        g.banco = sqlite3.connect(BANCO)
        g.banco.row_factory = sqlite3.Row
        g.banco.execute("PRAGMA foreign_keys = ON")
    return g.banco


@app.teardown_appcontext
def fechar_banco(_erro):
    conexao = g.pop("banco", None)
    if conexao is not None:
        conexao.close()


def criar_tabelas():
    banco().executescript(
        """
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('Quero ler', 'Lendo', 'Lido')),
            nota INTEGER NOT NULL DEFAULT 0 CHECK (nota BETWEEN 0 AND 5),
            resenha TEXT NOT NULL DEFAULT '',
            favorito INTEGER NOT NULL DEFAULT 0 CHECK (favorito IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS listas (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS lista_livros (
            lista_id INTEGER NOT NULL REFERENCES listas(id) ON DELETE CASCADE,
            livro_id INTEGER NOT NULL REFERENCES livros(id) ON DELETE CASCADE,
            PRIMARY KEY (lista_id, livro_id)
        );
        """
    )


def normalizar(texto):
    caracteres = unicodedata.normalize("NFD", texto.casefold())
    return "".join(
        caractere for caractere in caracteres
        if not unicodedata.combining(caractere)
    )


def voltar(aba="estante"):
    return redirect(url_for("inicio", aba=aba), code=303)


@app.get("/")
def inicio():
    aba = request.args.get("aba", "estante")
    if aba not in ABAS:
        abort(404)

    conexao = banco()
    livros = conexao.execute("SELECT * FROM livros ORDER BY id DESC").fetchall()
    listas = conexao.execute("SELECT * FROM listas ORDER BY id DESC").fetchall()

    busca = request.args.get("q", "").strip()[:150]
    termo = normalizar(busca)
    livros_filtrados = [
        livro for livro in livros
        if termo in normalizar(f"{livro['titulo']} {livro['autor']}")
    ]

    membros = {lista["id"]: set() for lista in listas}
    for item in conexao.execute("SELECT lista_id, livro_id FROM lista_livros"):
        if item["lista_id"] in membros:
            membros[item["lista_id"]].add(item["livro_id"])

    return render_template(
        "index.html",
        aba=aba,
        busca=busca,
        livros=livros,
        livros_filtrados=livros_filtrados,
        favoritos=[livro for livro in livros if livro["favorito"]],
        resenhas=[livro for livro in livros if livro["nota"] or livro["resenha"]],
        listas=listas,
        membros=membros,
        categorias=STATUS,
    )


@app.post("/livros/<int:livro_id>")
def salvar_livro(livro_id):
    aba = "resenhas" if request.form.get("aba") == "resenhas" else "estante"
    status = request.form.get("status", "")
    nota = request.form.get("nota", type=int)
    resenha = request.form.get("resenha", "").strip()
    favorito = int("favorito" in request.form)

    if status not in STATUS or nota not in range(6) or len(resenha) > 4000:
        flash("Confira o status, a nota e o tamanho da resenha.", "erro")
        return voltar(aba)

    conexao = banco()
    with conexao:
        # Reserva a escrita antes de conferir o limite de favoritos.
        conexao.execute("BEGIN IMMEDIATE")

        existe = conexao.execute(
            "SELECT 1 FROM livros WHERE id = ?",
            (livro_id,),
        ).fetchone()
        if existe is None:
            abort(404)

        if favorito:
            outros_favoritos = conexao.execute(
                "SELECT COUNT(*) FROM livros WHERE favorito = 1 AND id != ?",
                (livro_id,),
            ).fetchone()[0]

            if outros_favoritos >= 3:
                flash(
                    "Seu Top 3 está cheio. Desmarque um favorito para incluir outro.",
                    "erro",
                )
                return voltar(aba)

        conexao.execute(
            """
            UPDATE livros
            SET status = ?, nota = ?, resenha = ?, favorito = ?
            WHERE id = ?
            """,
            (status, nota, resenha, favorito, livro_id),
        )

    flash("Livro atualizado!", "sucesso")
    return voltar(aba)


@app.post("/livros/<int:livro_id>/excluir")
def excluir_livro(livro_id):
    conexao = banco()
    with conexao:
        conexao.execute("DELETE FROM livros WHERE id = ?", (livro_id,))

    flash("Livro removido da estante.", "sucesso")
    aba = "resenhas" if request.form.get("aba") == "resenhas" else "estante"
    return voltar(aba)


@app.post("/listas")
@app.post("/listas/<int:lista_id>")
def salvar_lista(lista_id=None):
    nome = request.form.get("nome", "").strip()
    if not 1 <= len(nome) <= 100:
        flash("Digite um nome de até 100 caracteres.", "erro")
        return voltar("listas")

    livros_selecionados = set(request.form.getlist("livros", type=int))
    conexao = banco()

    with conexao:
        if lista_id is None:
            resultado = conexao.execute(
                "INSERT INTO listas (nome) VALUES (?)",
                (nome,),
            )
            lista_id = resultado.lastrowid
        else:
            resultado = conexao.execute(
                "UPDATE listas SET nome = ? WHERE id = ?",
                (nome, lista_id),
            )
            if resultado.rowcount == 0:
                abort(404)

            conexao.execute(
                "DELETE FROM lista_livros WHERE lista_id = ?",
                (lista_id,),
            )

        conexao.executemany(
            """
            INSERT INTO lista_livros (lista_id, livro_id)
            SELECT ?, id FROM livros WHERE id = ?
            """,
            ((lista_id, livro_id) for livro_id in livros_selecionados),
        )

    flash("Lista salva!", "sucesso")
    return voltar("listas")


@app.post("/listas/<int:lista_id>/excluir")
def excluir_lista(lista_id):
    conexao = banco()
    with conexao:
        conexao.execute("DELETE FROM listas WHERE id = ?", (lista_id,))

    flash("Lista excluída. Os livros continuam na estante.", "sucesso")
    return voltar("listas")


app.register_blueprint(criar_catalogo(banco))

with app.app_context():
    criar_tabelas()
    atualizar_banco(banco())


if __name__ == "__main__":
    app.run(port=5001)