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
| Google OAuth (Authlib) | Login com conta Google |
| Azure App Service | Hospedagem da aplicação |
| GitHub Actions | Deploy automático |
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

**5. Configure as chaves do Google**

Crie um arquivo `.env` na pasta principal:

```dotenv
GOOGLE_BOOKS_KEY=SUA_CHAVE_AQUI
GOOGLE_CLIENT_ID=SEU_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=SEU_CLIENT_SECRET
```

As chaves são obtidas no Google Cloud Console. Para o login com Google funcionar localmente, cadastre `http://127.0.0.1:5001/login/google/callback` nas **URIs de redirecionamento autorizados** do cliente OAuth. Não compartilhe esse arquivo nem publique suas chaves no GitHub.

**6. Execute o Booklog**

```bash
python app.py
```

**7. Acesse no navegador**

```text
http://127.0.0.1:5001
```

## ☁️ Deploy na Azure

O Booklog está publicado no **Azure App Service** (Linux, Python 3.12), usando a assinatura **Azure for Students**.

🔗 **Acesse:** https://booklog-agdccqfghbbzgmg9.brazilsouth-01.azurewebsites.net

### Como o deploy funciona

O deploy é automático pelo **GitHub Actions** (`.github/workflows/deploy-booklog-mvp_booklog.yml`):

1. Um `git push` no branch `deploy/booklog-mvp` inicia o workflow.
2. O job **build** instala as dependências do `requirements.txt` para checar se está tudo certo.
3. O job **deploy** faz login na Azure e publica o código no Web App `booklog`.
4. A Azure (Oryx) instala as dependências e inicia o app com o **Gunicorn**.

O workflow também pode ser executado manualmente pela aba **Actions** do GitHub (`workflow_dispatch`).

### Variáveis de ambiente na Azure

O `.env` não vai para o GitHub, então as chaves ficam em **App Service → Configurações → Variáveis de ambiente**:

| Variável | Para que serve |
|---|---|
| `GOOGLE_BOOKS_KEY` | Pesquisa na Google Books API |
| `GOOGLE_CLIENT_ID` | ID do cliente OAuth do Google |
| `GOOGLE_CLIENT_SECRET` | Chave secreta do cliente OAuth |

Depois de alterar uma variável, reinicie o app na Azure.

### Login com Google em produção

No **Google Cloud Console → APIs e serviços → Credenciais**, o cliente OAuth (tipo **Aplicativo da Web**) precisa ter:

- **Origens JavaScript autorizadas:**
  `https://booklog-agdccqfghbbzgmg9.brazilsouth-01.azurewebsites.net`
- **URIs de redirecionamento autorizados:**
  `https://booklog-agdccqfghbbzgmg9.brazilsouth-01.azurewebsites.net/login/google/callback`

O app usa o `ProxyFix` do Werkzeug para reconhecer o HTTPS repassado pelo proxy da Azure. Assim, o endereço de retorno é gerado com `https://`.

> ⚠️ **Erro `redirect_uri_mismatch`?** O endereço cadastrado no Google precisa ser **idêntico** ao enviado pelo app, sem `/` no final e com `https`. **Copie e cole** o endereço em vez de digitar, porque uma única letra trocada já causa o erro. Para ver o endereço que o app envia, clique em "detalhes do erro" na tela do Google. Mudanças no Google Cloud podem levar alguns minutos para valer.

## 📁 Estrutura do projeto

```text
Book_log/
├── app.py
├── catalogo.py
├── usuarios.py
├── frases.py
├── google_login.py
├── requirements.txt
├── .github/workflows/
│   └── deploy-booklog-mvp_booklog.yml
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