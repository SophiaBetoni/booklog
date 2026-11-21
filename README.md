# Entre Páginas

Diário de leitura responsivo feito com Python, Flask, SQLite, HTML e CSS.

## Funcionalidades

- Contas de usuário com cadastro, login e logout (senhas guardadas com hash).
- Perfil público em `/u/<usuario>` com bio, números da estante, Top 3 e resenhas.
- Cada pessoa tem a própria estante, resenhas e listas.
- Cadastro, edição e exclusão de livros.
- Estante dividida em Quero ler, Lendo e Lido.
- Busca por título ou autor.
- Notas de 1 a 5 e resenhas.
- Top 3 de livros favoritos.
- Listas personalizadas.
- Menu inferior em telas pequenas.

## Como rodar no Windows

Abra a pasta do projeto no VS Code e execute no PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Abra [http://127.0.0.1:5001](http://127.0.0.1:5001) no navegador.
O SQLite cria o arquivo `estante.db` na primeira execução.

## Como demonstrar

1. Crie uma conta em Criar conta.
2. Adicione um livro e escolha o status Lido.
3. Dê uma nota, escreva uma resenha e marque o livro como favorito.
4. Abra Resenhas para conferir a avaliação.
5. Crie uma lista e selecione o livro.
6. Clique no seu @usuário no topo para ver seu perfil público.
7. Reduza a largura da janela para conferir o menu inferior.

Ao criar a primeira conta, ela recebe os livros e listas que já estavam no banco.
A publicação do código no GitHub permite que outras pessoas baixem e executem o projeto.