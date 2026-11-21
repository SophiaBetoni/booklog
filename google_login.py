
"""Autenticacao Google do Booklog."""

import os
import secrets

from authlib.integrations.base_client import OAuthError
from authlib.integrations.flask_client import OAuth
from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    session,
    url_for,
)
from werkzeug.security import generate_password_hash


oauth = OAuth()


def configurar_google(app):
    """Configura o Google OAuth."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Configure GOOGLE_CLIENT_ID e "
            "GOOGLE_CLIENT_SECRET no arquivo .env."
        )

    oauth.init_app(app)

    oauth.register(
        name="google",
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url=(
            "https://accounts.google.com/"
            ".well-known/openid-configuration"
        ),
        client_kwargs={
            "scope": "openid email profile"
        },
    )


def preparar_banco_google(conexao):
    """Adiciona o identificador Google sem apagar contas."""
    colunas = {
        coluna["name"]
        for coluna in conexao.execute(
            "PRAGMA table_info(usuarios)"
        )
    }

    with conexao:
        if "google_sub" not in colunas:
            conexao.execute(
                "ALTER TABLE usuarios ADD COLUMN google_sub TEXT"
            )

        conexao.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            usuarios_google_sub_unico
            ON usuarios(google_sub)
            WHERE google_sub IS NOT NULL
            """
        )


def criar_google_login(banco):
    google_login = Blueprint("google_login", __name__)

    @google_login.get("/login/google")
    def iniciar():
        if g.usuario is not None:
            return redirect(url_for("inicio"))

        callback = url_for(
            "google_login.retorno",
            _external=True,
        )

        return oauth.google.authorize_redirect(callback)

    @google_login.get("/login/google/callback")
    def retorno():
        try:
            token = oauth.google.authorize_access_token()
            dados = token.get("userinfo")

            if not dados or not dados.get("sub"):
                raise ValueError(
                    "O Google nao retornou a identidade."
                )

        except (OAuthError, ValueError) as erro:
            current_app.logger.warning(
                "Falha no login Google: %s", erro
            )
            flash(
                "Nao foi possivel entrar com Google.",
                "erro",
            )
            return redirect(url_for("usuarios.login"))

        google_sub = dados["sub"]
        conexao = banco()

        with conexao:
            conexao.execute("BEGIN IMMEDIATE")

            conta = conexao.execute(
                """
                SELECT id FROM usuarios
                WHERE google_sub = ?
                """,
                (google_sub,),
            ).fetchone()

            if conta:
                usuario_id = conta["id"]

            else:
                nome = (
                    dados.get("name") or "Leitor Booklog"
                ).strip()[:80]

                while True:
                    usuario = "google_" + secrets.token_hex(6)

                    existe = conexao.execute(
                        """
                        SELECT 1 FROM usuarios
                        WHERE usuario = ?
                        """,
                        (usuario,),
                    ).fetchone()

                    if not existe:
                        break

                senha_aleatoria = secrets.token_urlsafe(48)

                primeira_conta = (
                    conexao.execute(
                        "SELECT COUNT(*) FROM usuarios"
                    ).fetchone()[0] == 0
                )

                usuario_id = conexao.execute(
                    """
                    INSERT INTO usuarios
                    (usuario, nome, senha_hash, google_sub)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        usuario,
                        nome,
                        generate_password_hash(senha_aleatoria),
                        google_sub,
                    ),
                ).lastrowid

                if primeira_conta:
                    for tabela in ("livros", "listas"):
                        conexao.execute(
                            f"""
                            UPDATE {tabela}
                            SET usuario_id = ?
                            WHERE usuario_id IS NULL
                            """,
                            (usuario_id,),
                        )

        session.clear()
        session["usuario_id"] = usuario_id
        session.permanent = True

        flash(
            "Login com Google realizado com sucesso!",
            "sucesso",
        )

        return redirect(url_for("inicio"))

    return google_login
