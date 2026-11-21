# ✦ Booklog 📚

**Um lugar para todas as suas histórias. ♡**

O **Booklog** é uma aplicação web desenvolvida para quem ama livros e deseja organizar suas leituras em um espaço pessoal, intuitivo e acolhedor.

Inspirado na ideia de um diário literário, o Booklog permite acompanhar suas leituras, registrar avaliações, organizar listas e guardar suas histórias favoritas.

> Cada livro, uma história. Cada leitura, uma memória.

---

## 🌷 Funcionalidades

- 📖 **Minha estante:** organize seus livros em *Quero ler*, *Lendo* e *Lido*.
- ⭐ **Avaliações:** atribua notas de 0 a 5 estrelas e escreva resenhas.
- 💗 **Top 3 favoritos:** escolha seus três livros preferidos.
- 🔎 **Busca de livros:** pesquise por título ou autor.
- 🎀 **Listas personalizadas:** crie e organize suas próprias coleções.
- 👤 **Perfis:** crie uma conta, faça login e personalize seu perfil.
- ✨ **Página inicial:** descubra citações literárias selecionadas, exibidas aleatoriamente.
- 📱 **Design responsivo:** navegue pelo computador ou celular.

## 🛠️ Tecnologias utilizadas

| Tecnologia | Utilização |
|---|---|
| Python | Backend |
| Flask | Aplicação web e rotas |
| SQLite | Banco de dados |
| HTML5 | Estrutura das páginas |
| CSS3 | Estilização e responsividade |
| Jinja2 | Templates dinâmicos |
| Google Books API | Pesquisa de livros e capas |
| Open Library API | Fonte alternativa para o catálogo |
| Git e GitHub | Versionamento |

## 💻 Como executar o projeto

**1. Clone o repositório**

```bash
git clone URL_DO_SEU_REPOSITORIO
cd Book_log
```

**2. Crie um ambiente virtual**

```bash
python -m venv .venv
```

**3. Ative o ambiente virtual**

No Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

**4. Instale as dependências**

```bash
pip install -r requirements.txt
```

**5. Configure a Google Books API**

Crie um arquivo `.env` na pasta principal:

```dotenv
GOOGLE_BOOKS_KEY=SUA_CHAVE_AQUI
```

A chave deve ser obtida no Google Cloud Console. Não compartilhe esse arquivo nem publique sua chave no GitHub.

**6. Execute o Booklog**

```bash
python app.py
```

**7. Acesse no navegador**

```text
http://127.0.0.1:5001
```

## 📁 Estrutura do projeto

```text
Book_log/
├── app.py
├── catalogo.py
├── usuarios.py
├── frases.py
├── requirements.txt
├── templates/
│   ├── inicio.html
│   ├── index.html
│   ├── catalogo.html
│   ├── cadastro.html
│   ├── login.html
│   └── ...
├── static/
│   ├── inicio.css
│   └── style.css
└── README.md
```


## 💌 Sobre o projeto

O Booklog é um projeto pessoal desenvolvido para unir duas paixões: **tecnologia e literatura**.

A proposta é transformar o acompanhamento de leituras em uma experiência agradável, personalizada e visualmente encantadora.

---

**Feito com Python, livros e muito carinho. ♡**

*✦ Booklog — porque algumas histórias merecem ficar com a gente para sempre.*