# 🧼 Paraná Produtos de Limpeza

Loja online de **produtos de limpeza** construída com **Django**, **Bootstrap 5** e **Django Allauth** para autenticação. Possui frontend moderno, carrinho de compras, página de checkout, galeria de produtos e upload de imagens pelo admin.

---

## 🌐 Tecnologias Utilizadas

- **Backend:** Python 3.x, Django 4.x, SQLite  
- **Autenticação:** Django Allauth  
- **Frontend:** Bootstrap 5.3, Font Awesome 6, HTML5, CSS3, JS, jQuery  
- **Gerenciamento de arquivos:** Upload de imagens via admin, armazenadas em `media/produtos/`

---

## 📁 Estrutura do Projeto

app/ – App principal  
- admin.py  
- apps.py  
- models.py  
- urls.py  
- views.py  
- migrations/

ecommerce/ – Configurações do Django  
- settings.py  
- urls.py  
- wsgi.py

media/produtos/ – Imagens dos produtos (upload via admin)

static/ – Arquivos estáticos  
- css/style.css  
- js/carrinho.js  
- js/main.js

templates/ – Templates HTML  
- base.html  
- index.html  
- checkout.html  
- produto.html

db.sqlite3 – Banco de dados SQLite  
manage.py – Gerenciador do Django  
requirements.txt – Dependências do projeto

---

## ⚙️ Instalação

Clone o repositório:

git clone https://github.com/seu-usuario/parana-produtos-limpeza.git  
cd andrewlemos

Crie e ative um ambiente virtual:

# Linux / macOS
python -m venv venv  
source venv/bin/activate

# Windows
python -m venv venv  
venv\Scripts\activate.bat

Instale as dependências:

pip install -r requirements.txt

Aplique as migrações:

python manage.py makemigrations  
python manage.py migrate

Crie um superusuário para acessar o admin:

python manage.py createsuperuser

---

## 🖼️ Configuração de Mídia

Para que as imagens adicionadas no admin apareçam no site, adicione no **settings.py**:

MEDIA_URL = '/media/'  
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

No **urls.py** do projeto (`ecommerce/urls.py`):

from django.conf import settings  
from django.conf.urls.static import static  

urlpatterns = [  
    path('admin/', admin.site.urls),  
    path('accounts/', include('allauth.urls')),  
    path('', include('app.urls')),  
]  

if settings.DEBUG:  
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

---

## 🚀 Executando o Projeto

python manage.py runserver

- Site: http://127.0.0.1:8000  
- Admin: http://127.0.0.1:8000/admin

---

## 📦 Funcionalidades

- Página inicial com **hero section** e categorias em destaque  
- **Listagem de produtos** com cards modernos e badges de desconto  
- **Carrinho de compras** persistente via `sessionStorage`  
- **Página de detalhes do produto** com galeria de imagens  
- **Checkout** com resumo do pedido  
- **Autenticação** via Django Allauth  
- **Upload de imagens** pelo admin (`media/produtos/`)  
- **Notificações toast** para feedback de ações  
- Layout responsivo para desktop e mobile

---

## 📝 Modelos no Admin

Modelo principal: Produto  

Campo | Tipo | Observação  
--- | --- | ---  
nome | CharField | Nome do produto  
descricao | TextField | Descrição completa  
preco | DecimalField | Preço atual  
preco_original | DecimalField (opcional) | Preço antigo, se houver desconto  
desconto | IntegerField (opcional) | % de desconto  
imagem | ImageField | Upload para `media/produtos/`

---

## 🔒 Produção

- DEBUG=False e configurar ALLOWED_HOSTS  
- Servir arquivos estáticos e mídia via servidor (ex.: Nginx)  
- Configurar gateway de pagamento real (ex.: Mercado Pago)  
- Configurar SMTP real para envio de emails

---

## 👨‍💻 Autor

Andrew Lemos – Desenvolvedor Fullstack  
📧 Contato: andrewfmlemos@gmail.com
