# 🧼 Paraná Produtos de Limpeza - E-commerce Completo

Sistema de e-commerce profissional para produtos de limpeza, desenvolvido com **Django** e tecnologias modernas.  
Possui integração completa com **Mercado Pago**, gestão de estoque em tempo real, painel administrativo avançado e experiência de usuário otimizada.

---

## 🚀 Funcionalidades Principais

### 🛒 Sistema de Vendas
- Carrinho inteligente com verificação de estoque em tempo real  
- Checkout completo com múltiplas etapas  
- Integração Mercado Pago para pagamentos seguros  
- Gestão de pedidos com fluxo de status completo  
- Cálculo automático de frete (grátis acima de R$ 100)  

### 📦 Gestão de Produtos
- Catálogo dinâmico com categorias organizadas  
- Sistema de descontos e promoções  
- Controle de estoque com reserva automática  
- Upload de imagens via painel administrativo  
- Busca inteligente com autocomplete  

### 👤 Sistema de Usuários
- Autenticação social via **Django Allauth**  
- Histórico de pedidos personalizado  
- Área do cliente com dados de entrega  
- Sistema de favoritos  

### 🎯 Recursos Técnicos Avançados
- Webhooks para notificações do Mercado Pago  
- APIs RESTful para integrações  
- Design responsivo com **Bootstrap 5.3**  
- Otimização SEO com meta tags dinâmicas  
- Acessibilidade (**WCAG**) implementada  

---

## 🛠 Stack Tecnológica

### Backend & Database
- Python 3.13 + Django 5.2.6  
- SQLite3 (desenvolvimento) / PostgreSQL (produção)  
- Django Allauth para autenticação  
- Mercado Pago SDK para pagamentos  

### Frontend & UI/UX
- Bootstrap 5.3.2 + Design System customizado  
- Font Awesome 6.4.0 para ícones  
- JavaScript ES6+ com classes modernas  
- CSS3 com variáveis e animações  

### APIs & Integrações
- Mercado Pago API - Processamento de pagamentos  
- ViaCEP API - Preenchimento automático de endereços  
- Web Share API - Compartilhamento nativo  
- Clipboard API - Cópia de links  

---

## 📁 Estrutura do Projeto

```text
parana-produtos-limpeza/
├── app/                          # Aplicação principal
│   ├── models.py                 # Modelos: Produto, Pedido, ItemPedido
│   ├── views.py                  # Views + APIs + Webhooks
│   ├── admin.py                  # Painel admin customizado
│   ├── urls.py                   # Rotas da aplicação
│   └── migrations/
├── ecommerce/                    # Configurações do projeto
│   ├── settings.py               # Configurações + variáveis de ambiente
│   ├── urls.py                   # Rotas globais
│   └── wsgi.py
├── static/                       # Arquivos estáticos
│   ├── css/
│   │   └── style.css             # Estilos customizados
│   ├── js/
│   │   ├── carrinho.js           # Gerenciador do carrinho
│   │   ├── main.js               # Funcionalidades globais
│   │   └── produto.js            # Página de produto
│   └── img/                      # Imagens estáticas
├── templates/                    # Sistema de templates
│   ├── base.html                 # Template base
│   ├── index.html                # Página inicial
│   ├── produto.html              # Detalhes do produto
│   ├── checkout.html             # Finalização de compra
│   ├── compra_confirmada.html    # Confirmação de pedido
│   └── account/                  # Templates de autenticação
├── media/                        # Uploads de mídia
│   └── produtos/                 # Imagens dos produtos
├── requirements.txt              # Dependências do projeto
└── manage.py                     # CLI do Django
⚙️ Instalação e Configuração
1. Clone e Ambiente Virtual
bash
Copiar código
git clone https://github.com/seu-usuario/parana-produtos-limpeza.git
cd parana-produtos-limpeza

# Ambiente virtual (Windows)
python -m venv venv
venv\Scripts\activate

# Instalação de dependências
pip install -r requirements.txt
2. Configuração de Ambiente
Crie o arquivo .env na raiz do projeto:

env
Copiar código
DEBUG=True
SECRET_KEY=sua-chave-secreta-aqui
MP_ACCESS_TOKEN=SEU_ACCESS_TOKEN_MERCADO_PAGO
ALLOWED_HOSTS=localhost,127.0.0.1
3. Banco de Dados e Superusuário
bash
Copiar código
# Migrações do banco
python manage.py makemigrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic
4. Executar Servidor
bash
Copiar código
python manage.py runserver
Site: http://127.0.0.1:8000

Admin: http://127.0.0.1:8000/admin

🎯 Modelos de Dados
Produto
Campo	Tipo	Descrição
nome	CharField	Nome do produto
preco	DecimalField	Preço atual
preco_original	DecimalField	Preço sem desconto
estoque	IntegerField	Quantidade disponível
imagem	ImageField	Imagem do produto
disponivel	BooleanField	Status de disponibilidade

Pedido
Campo	Tipo	Descrição
status	CharField	Status do pedido (8 opções)
valor_total	DecimalField	Total do pedido
preference_id	CharField	ID do Mercado Pago
dados_entrega	JSONField	Informações de entrega

ItemPedido
Campo	Tipo	Descrição
quantidade	IntegerField	Quantidade comprada
preco_unitario	DecimalField	Preço no momento da compra

🔧 Configurações de Produção
Variáveis de Ambiente (.env)
env
Copiar código
DEBUG=False
SECRET_KEY=produção-chave-super-secreta
MP_ACCESS_TOKEN=APP_USR-...
ALLOWED_HOSTS=seudominio.com,www.seudominio.com
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-app
Configurações de Segurança
python
Copiar código
# settings.py - Produção
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
📊 APIs Disponíveis
Endpoint	Método	Descrição
/api/criar-preferencia-pagamento/	POST	Cria pagamento Mercado Pago
/api/verificar-estoque/	POST	Verifica estoque em tempo real
/api/buscar-sugestoes/	GET	Busca produtos para autocomplete
/webhook/mercadopago/	POST	Webhook para notificações MP

🎨 Personalização
Cores do Tema (CSS Variables)
css
Copiar código
:root {
  --primary-color: #0d6efd;
  --success-color: #198754;
  --danger-color: #dc3545;
  --warning-color: #ffc107;
  --frete-gratis: 100.00;
  --valor-frete: 15.00;
}
Status de Pedidos
python
Copiar código
STATUS_CHOICES = [
    ('pendente', 'Pendente'),
    ('processando', 'Processando Pagamento'),
    ('pago', 'Pago'),
    ('preparando', 'Preparando Envio'),
    ('enviado', 'Enviado'),
    ('entregue', 'Entregue'),
    ('cancelado', 'Cancelado'),
    ('reembolsado', 'Reembolsado'),
]
🚀 Deploy em Produção
Opção 1: PythonAnywhere
bash
Copiar código
# Upload via Git
git push pythonanywhere master

# Configurar virtualenv
pip install -r requirements.txt

# Configurar WSGI
import sys
path = '/home/seusuario/parana-produtos-limpeza'
if path not in sys.path:
    sys.path.append(path)

from ecommerce.wsgi import application
Opção 2: VPS com Nginx + Gunicorn
bash
Copiar código
# Instalação do Gunicorn
pip install gunicorn

# Arquivo de serviço
# /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=usuario
Group=www-data
WorkingDirectory=/home/usuario/parana-produtos-limpeza
ExecStart=/home/usuario/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/home/usuario/parana-produtos-limpeza/ecommerce.sock ecommerce.wsgi:application

[Install]
WantedBy=multi-user.target
📞 Suporte e Contato
Desenvolvedor:
👨‍💻 Andrew Lemos - Desenvolvedor Fullstack
📧 Email: andrewfmlemos@gmail.com
💼 LinkedIn: linkedin.com/in/andrewlemos
🐙 GitHub: github.com/andrewlemos

📄 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

🔄 Changelog
v2.0.0 - Lançamento Completo
✅ Integração Mercado Pago

✅ Sistema de pedidos completo

✅ Webhooks para notificações

✅ Painel admin avançado

✅ APIs RESTful

v1.0.0 - Versão Inicial
✅ Catálogo de produtos

✅ Carrinho de compras

✅ Autenticação de usuários

✅ Layout responsivo
