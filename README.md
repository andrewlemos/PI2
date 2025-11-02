# Paraná Produtos de Limpeza

Loja online de produtos de limpeza construída com Django, Bootstrap 5 e Django Allauth para autenticação.  
Inclui carrinho persistente, cupons de desconto, controle de estoque, frete grátis, endereço completo no admin e pagamento via Mercado Pago.

---

## Tecnologias Utilizadas

- Backend: Python 3.11+, Django 5, SQLite (desenvolvimento)  
- Frontend: Bootstrap 5.3, Font Awesome 6, HTML5, CSS3, JavaScript (ES6), jQuery  
- Autenticação: Django Allauth + Login com Google  
- Pagamentos: Mercado Pago (Checkout Pro)  
- Armazenamento: media/produtos/ (imagens), localStorage (carrinho)

---

## Estrutura do Projeto

app/  
- admin.py → Painel admin com endereço completo  
- models.py → Produto, Pedido, Cupom, ItemPedido  
- views.py → APIs, checkout, pagamento  
- urls.py
- adapters.py
- middleware.py
- signals.py 
- migrations/

ecommerce/  
- settings.py → Configurações + .env  
- urls.py
- wsgi.py

static/  
- css/style.css  
- js/carrinho.js → Carrinho + cupom + estoque  
- img/

templates/  
- base.html  
- index.html  
- checkout.html  
- produto.html
- compra_confirmada.html
- compra_errada.html
- detalhe_pedido.html
- meus_pedidos.html
- acconunt/

media/produtos/ → Upload de imagens  
db.sqlite3  
manage.py  
requirements.txt

---

## Instalação

1. Clone o repositório  
   git clone https://github.com/seu-usuario/parana-produtos-limpeza.git  
   cd parana-produtos-limpeza

2. Crie e ative o ambiente virtual  
   python -m venv venv  
   source venv/bin/activate  (Linux/macOS)  
   venv\Scripts\activate     (Windows)

3. Instale as dependências  
   pip install -r requirements.txt

4. Configure o .env  
   cp .env.example .env

5. Aplique as migrações  
   python manage.py makemigrations  
   python manage.py migrate

6. Crie um superusuário  
   python manage.py createsuperuser

---

## Configuração de Mídia

No arquivo ecommerce/settings.py:  
MEDIA_URL = '/media/'  
MEDIA_ROOT = BASE_DIR / 'media'

No arquivo ecommerce/urls.py:  
Adicione no final, dentro do if settings.DEBUG:  
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

---

## Executando

python manage.py runserver

Site: http://127.0.0.1:8000  
Admin: http://127.0.0.1:8000/admin

---

## Funcionalidades

- Página inicial com hero e destaques  
- Produtos com desconto e badges  
- Carrinho persistente (localStorage)  
- Checkout com formulário de entrega  
- Cupons (fixo/percentual) com validade e limite  
- Estoque com reserva e liberação automática  
- Frete grátis acima de R$ 100  
- Mercado Pago integrado  
- Admin com endereço completo visível  
- Ações em massa (pago, enviado, entregue)  
- Notificações toast e layout responsivo

---

## Painel Admin – Destaques

Pedidos  
- Lista: ID, Cliente, Status, Valor, Endereço completo  
- Detalhes: Resumo visual com 2 colunas (Dados pessoais × Endereço)  
- Campos editáveis + JSON bruto

Cupons  
- Ação: "Limpar usos"  
- Filtros por validade e tipo

---

## Modelos no Admin

Produto: Nome, Preço, Desconto, Estoque, Imagem  
Pedido: Usuário, Status, Valor, Endereço, Cupom  
ItemPedido: Produto, Quantidade, Subtotal  
Cupom: Código, Tipo, Valor, Validade, Limite  
CupomUso: Cupom, Pedido, Data

---

## Produção

DEBUG=False  
ALLOWED_HOSTS=seudominio.com  
MP_ACCESS_TOKEN=SEU_TOKEN_REAL

- Use PostgreSQL  
- Sirva mídia/estáticos com Nginx  
- Use Gunicorn  
- Configure SMTP real


---

## Imagens

<img width="1115" height="599" alt="Tela Inicial do Ecommerce" src="https://github.com/user-attachments/assets/49f35929-60ff-4a7e-9693-a942b8b8cb1b" />

<br><br>

<img width="1115" height="599" alt="Pagamento pelo Mercado Pago" src="https://github.com/user-attachments/assets/9ba696fb-8886-4e7a-9129-0d1769e547d7" />

<br><br>

<img width="1115" height="599" alt="Tela de acompanhamento de pedidos do Cliente" src="https://github.com/user-attachments/assets/44d2fbe3-5df4-4e14-a88a-d00ef1a5022e" />

<br><br>

<img width="1115" height="599" alt="Controle de Pedidos" src="https://github.com/user-attachments/assets/b86e94bd-ac11-49c0-a1ba-dc24e6fe5d69" />

<br><br>

<img width="1115" height="599" alt="Controle de Produtos" src="https://github.com/user-attachments/assets/3631bed5-181d-4a2e-9f79-3386e82555e7" />

<br><br>

<img width="1115" height="599" alt="Cadastro de Produtos no Gerenciador do Admin" src="https://github.com/user-attachments/assets/01849fbd-0fef-4c7d-833d-11012a1bc08e" />

<br><br>

<img width="1115" height="599" alt="Tela de Cadastro" src="https://github.com/user-attachments/assets/e86cb98d-8f7e-4592-9b06-721f408154cd" />

<br><br>

<img width="1115" height="599" alt="Página de Detalhes dos Produtos" src="https://github.com/user-attachments/assets/0a89f265-fe79-4eab-9083-539a0a0dd55e" />

<br><br>

<img width="1017" height="882" alt="Cupom cliente" src="https://github.com/user-attachments/assets/3e58aa89-efd8-4097-a979-fbf7ef3734ad" />

<br><br>

<img width="1115" height="599" alt="Cupom empresa" src="https://github.com/user-attachments/assets/5bdd65a2-8f19-4f18-b976-fabc4f0d820d" />

<br><br>

<img width="1115" height="599" alt="Login com Google OAuth" src="https://github.com/user-attachments/assets/5180f584-6025-431e-9f68-db6a7ede4e3c" />

<br><br>

<img width="1115" height="599" alt="Redirecionamento do Login do Google" src="https://github.com/user-attachments/assets/8bd06316-78b7-4e49-9c12-38d4e863dbda" />

---

## Autor

Andrew Lemos  
Desenvolvedor Fullstack  
andrewfmlemos@gmail.com  
github.com/andrewlemos
