# Entre Páginas

Diário de leitura responsivo feito com Python, Flask, SQLite, HTML e CSS.

## Funcionalidades

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

Abra [http://127.0.0.1:5000](http://127.0.0.1:5000) no navegador.
O SQLite cria o arquivo `estante.db` na primeira execução.

## Como demonstrar

1. Adicione um livro e escolha o status Lido.
2. Dê uma nota, escreva uma resenha e marque o livro como favorito.
3. Abra Resenhas para conferir a avaliação.
4. Crie uma lista e selecione o livro.
5. Reduza a largura da janela para conferir o menu inferior.

Este MVP usa uma única estante local. A publicação do código no GitHub
permite que outras pessoas baixem e executem o projeto.