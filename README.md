# 📚 Booklog

O **Booklog** é um diário de leitura para organizar os livros que você quer ler, está lendo ou já terminou. Pesquise um título ou autor no catálogo, escolha um livro e adicione-o à sua estante.

## O que você pode fazer

| Recurso | Como funciona |
| --- | --- |
| 🔎 Catálogo | Busque por título ou autor na Open Library e veja a capa quando estiver disponível. |
| 📖 Estante | Organize seus livros em **Quero ler**, **Lendo** e **Lido**. |
| ⭐ Avaliações | Dê notas de 1 a 5 estrelas e escreva resenhas. |
| 📋 Listas | Crie coleções personalizadas com os livros da sua estante. |
| 💜 Top 3 | Destaque até três livros favoritos. |

A interface tem tema escuro e se adapta a telas de computador e celular.

## Como executar no Windows

Abra a pasta do projeto no VS Code. No terminal PowerShell, crie o ambiente virtual e instale as dependências:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Depois, inicie o servidor:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --port 5001
```

Com o terminal aberto, acesse **[http://127.0.0.1:5001](http://127.0.0.1:5001)** no navegador.

## Como testar

1. Abra **Buscar no catálogo** e pesquise o livro que deseja.
2. Escolha um resultado, selecione **Lendo** e clique em **Salvar na estante**.
3. Na estante, abra **Editar leitura** para mudar o status, dar uma nota ou escrever uma resenha.

O catálogo e as capas precisam de internet. Os livros salvos, as resenhas e as listas ficam no banco SQLite local `estante.db`, criado na primeira execução.

## Tecnologias

**Python e Flask** no servidor, **SQLite** para armazenar os dados, **HTML com Jinja e CSS** na interface e **Open Library** para a busca e as capas.