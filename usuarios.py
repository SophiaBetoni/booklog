
"""Booklog — cadastro, login, logout e perfis de usuário."""

import re
import secrets
from hmac import compare_digest

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


FORMATO_USUARIO = re.compile(r"[a-z0-9_]{3,20}")

# Páginas acessíveis sem autenticação.
ROTAS_PUBLICAS = {
    "boas_vindas",
    "usuarios.login",
    "usuarios.cadastro",
    "usuarios.perfil",
    "static",
}


def criar_tabela_usuarios(conexao):
    """Cria a tabela de usuários sem apagar contas existentes."""
    conexao.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            usuario TEXT NOT NULL UNIQUE COLLATE NOCASE,
            nome TEXT NOT NULL,
            senha_hash TEXT NOT NULL,
            bio TEXT NOT NULL DEFAULT '',
            criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


def migrar_para_usuarios(conexao):
    """Associa livros e listas aos usuários existentes."""
    with conexao:
        conexao.execute("BEGIN IMMEDIATE")

        for tabela in ("livros", "listas"):
            colunas = {
                coluna["name"]
                for coluna in conexao.execute(
                    f"PRAGMA table_info({tabela})"
                )
            }

            if "usuario_id" not in colunas:
                conexao.execute(
                    f"ALTER TABLE {tabela} "
                    "ADD COLUMN usuario_id INTEGER "
                    "REFERENCES usuarios(id) ON DELETE CASCADE"
                )

        conexao.execute(
            "DROP INDEX IF EXISTS livros_catalogo_id"
        )

        conexao.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            livros_usuario_catalogo
            ON livros (usuario_id, catalogo_id)
            """
        )


def token_csrf():
    """Cria um token de proteção para formulários."""
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)

    return session["csrf"]


def destino_seguro(destino):
    """Permite redirecionamentos apenas para caminhos internos."""
    if (
        destino
        and destino.startswith("/")
        and not destino.startswith("//")
        and "\\" not in destino
    ):
        return destino

    return url_for("inicio")


def criar_usuarios(banco):
    usuarios = Blueprint("usuarios", __name__)

    @usuarios.before_app_request
    def carregar_usuario():
        """Carrega a conta e protege páginas privadas."""
        usuario_id = session.get("usuario_id")
        g.usuario = None

        if usuario_id is not None:
            g.usuario = banco().execute(
                "SELECT * FROM usuarios WHERE id = ?",
                (usuario_id,),
            ).fetchone()

            if g.usuario is None:
                session.clear()

        # Proteção CSRF dos formulários.
        if request.method == "POST":
            enviado = request.form.get("csrf", "")

            if not compare_digest(
                enviado,
                session.get("csrf", "")
            ):
                abort(400)

        # Usuários não autenticados.
        if (
            g.usuario is None
            and request.endpoint not in ROTAS_PUBLICAS
        ):
            # A estante redireciona para a página inicial.
            if (
                request.endpoint == "inicio"
                and request.method == "GET"
            ):
                return redirect(url_for("boas_vindas"))

            # Outras páginas privadas exigem login.
            if request.method == "GET":
                return redirect(
                    url_for(
                        "usuarios.login",
                        proximo=request.full_path
                    )
                )

            return redirect(
                url_for("usuarios.login"),
                code=303
            )

    @usuarios.app_context_processor
    def variaveis_globais():
        return {
            "usuario_atual": g.get("usuario"),
            "csrf_token": token_csrf,
        }

    def entrar(usuario_id):
        """Inicia uma sessão autenticada."""
        session.clear()
        session["usuario_id"] = usuario_id
        session.permanent = True

    # ==========================================
    # CADASTRO
    # ==========================================

    @usuarios.route("/cadastro", methods=("GET", "POST"))
    def cadastro():
        if g.usuario is not None:
            return redirect(url_for("inicio"))

        dados = {
            "nome": "",
            "usuario": "",
        }

        if request.method == "POST":
            nome = request.form.get("nome", "").strip()
            usuario = request.form.get(
                "usuario", ""
            ).strip().lower()

            senha = request.form.get("senha", "")
            confirmacao = request.form.get(
                "confirmacao", ""
            )

            dados = {
                "nome": nome,
                "usuario": usuario,
            }

            erro = None

            if not 1 <= len(nome) <= 80:
                erro = "Digite seu nome (até 80 caracteres)."

            elif not FORMATO_USUARIO.fullmatch(usuario):
                erro = (
                    "O nome de usuário deve ter de 3 a 20 "
                    "letras minúsculas, números ou _."
                )

            elif not 8 <= len(senha) <= 128:
                erro = (
                    "A senha deve ter pelo menos 8 caracteres."
                )

            elif senha != confirmacao:
                erro = "As senhas não são iguais."

            if erro is None:
                conexao = banco()

                with conexao:
                    conexao.execute("BEGIN IMMEDIATE")

                    ja_existe = conexao.execute(
                        "SELECT 1 FROM usuarios WHERE usuario = ?",
                        (usuario,),
                    ).fetchone()

                    if ja_existe:
                        erro = (
                            "Esse nome de usuário já está em uso."
                        )

                    else:
                        primeira_conta = (
                            conexao.execute(
                                "SELECT COUNT(*) FROM usuarios"
                            ).fetchone()[0] == 0
                        )

                        novo_id = conexao.execute(
                            """
                            INSERT INTO usuarios
                            (usuario, nome, senha_hash)
                            VALUES (?, ?, ?)
                            """,
                            (
                                usuario,
                                nome,
                                generate_password_hash(senha),
                            ),
                        ).lastrowid

                        # Preserva livros anteriores ao login.
                        if primeira_conta:
                            for tabela in ("livros", "listas"):
                                conexao.execute(
                                    f"UPDATE {tabela} "
                                    "SET usuario_id = ? "
                                    "WHERE usuario_id IS NULL",
                                    (novo_id,),
                                )

                if erro is None:
                    entrar(novo_id)

                    flash(
                        f"Bem-vindo(a), {nome}! "
                        "Sua conta foi criada.",
                        "sucesso",
                    )

                    return redirect(
                        url_for("inicio"),
                        code=303
                    )

            flash(erro, "erro")

        return render_template(
            "cadastro.html",
            dados=dados
        )

    # ==========================================
    # LOGIN
    # ==========================================

    @usuarios.route("/login", methods=("GET", "POST"))
    def login():
        proximo = request.values.get("proximo", "")

        if g.usuario is not None:
            return redirect(destino_seguro(proximo))

        usuario = ""

        if request.method == "POST":
            usuario = request.form.get(
                "usuario", ""
            ).strip().lower()

            senha = request.form.get("senha", "")

            conta = banco().execute(
                """
                SELECT id, senha_hash
                FROM usuarios
                WHERE usuario = ?
                """,
                (usuario,),
            ).fetchone()

            if conta and check_password_hash(
                conta["senha_hash"], senha
            ):
                entrar(conta["id"])

                return redirect(
                    destino_seguro(proximo),
                    code=303
                )

            flash(
                "Usuário ou senha incorretos.",
                "erro"
            )

        return render_template(
            "login.html",
            usuario=usuario,
            proximo=proximo
        )

    # ==========================================
    # LOGOUT
    # ==========================================

    @usuarios.post("/logout")
    def logout():
        session.clear()

        flash(
            "Você saiu da sua conta.",
            "sucesso"
        )

        return redirect(
            url_for("boas_vindas"),
            code=303
        )

    # ==========================================
    # PERFIL PÚBLICO
    # ==========================================

    @usuarios.get("/u/<usuario>")
    def perfil(usuario):
        conexao = banco()

        dono = conexao.execute(
            "SELECT * FROM usuarios WHERE usuario = ?",
            (usuario,),
        ).fetchone()

        if dono is None:
            abort(404)

        livros = conexao.execute(
            """
            SELECT * FROM livros
            WHERE usuario_id = ?
            ORDER BY id DESC
            """,
            (dono["id"],),
        ).fetchall()

        contagem = {
            status: 0
            for status in (
                "Quero ler",
                "Lendo",
                "Lido"
            )
        }

        for livro in livros:
            contagem[livro["status"]] += 1

        return render_template(
            "perfil.html",
            dono=dono,
            contagem=contagem,
            favoritos=[
                livro for livro in livros
                if livro["favorito"]
            ],
            lendo=[
                livro for livro in livros
                if livro["status"] == "Lendo"
            ],
            resenhas=[
                livro for livro in livros
                if livro["resenha"]
            ][:6],
            proprio=(
                g.usuario is not None
                and g.usuario["id"] == dono["id"]
            ),
        )

    # ==========================================
    # EDITAR PERFIL
    # ==========================================

    @usuarios.route(
        "/perfil/editar",
        methods=("GET", "POST")
    )
    def editar_perfil():
        if request.method == "POST":
            nome = request.form.get(
                "nome", ""
            ).strip()

            bio = request.form.get(
                "bio", ""
            ).strip()

            if (
                not 1 <= len(nome) <= 80
                or len(bio) > 300
            ):
                flash(
                    "Confira o nome (até 80) "
                    "e a bio (até 300 caracteres).",
                    "erro",
                )

            else:
                conexao = banco()

                with conexao:
                    conexao.execute(
                        """
                        UPDATE usuarios
                        SET nome = ?, bio = ?
                        WHERE id = ?
                        """,
                        (
                            nome,
                            bio,
                            g.usuario["id"],
                        ),
                    )

                flash(
                    "Perfil atualizado!",
                    "sucesso"
                )

                return redirect(
                    url_for(
                        "usuarios.perfil",
                        usuario=g.usuario["usuario"]
                    ),
                    code=303
                )

        return render_template("editar_perfil.html")

    return usuarios
