/**
 * Sistema de Carrinho - E-commerce
 * Versão 2.0 - Corrigida e Melhorada
 */

class CarrinhoManager {
    constructor() {
        this.carrinhoKey = 'carrinho_ecommerce';
        this.init();
    }

    init() {
        console.log('🛒 CarrinhoManager inicializado');
        this.setupEventListeners();
        this.atualizarContadorCarrinho();
        
        // Carregar itens se estiver na página de checkout
        if (this.isCheckoutPage()) {
            this.carregarItensCarrinho();
        }
    }

    setupEventListeners() {
        // Event delegation para botões de adicionar ao carrinho
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn-adicionar-carrinho');
            if (btn) {
                e.preventDefault();
                this.handleAdicionarAoCarrinho(btn);
            }
        });

        // Configurar botão de finalizar compra
        const finalizarBtn = document.getElementById('btn-finalizar-pagamento');
        if (finalizarBtn) {
            finalizarBtn.addEventListener('click', () => this.finalizarCompra());
        }
    }

    async handleAdicionarAoCarrinho(btn) {
        try {
            const produto = this.extrairDadosProduto(btn);
            
            if (!this.validarDadosProduto(produto)) {
                this.mostrarNotificacao('Erro: Dados do produto incompletos.', 'error');
                return;
            }

            const adicionado = await this.adicionarAoCarrinho(produto);
            if (adicionado) {
                this.mostrarNotificacao(`${produto.quantidade}x ${produto.nome} adicionado ao carrinho!`, 'success');
            }
        } catch (error) {
            console.error('Erro ao adicionar ao carrinho:', error);
            this.mostrarNotificacao('Erro ao adicionar produto ao carrinho.', 'error');
        }
    }

    extrairDadosProduto(btn) {
        const dataset = btn.dataset;
        let preco = dataset.produtoPreco || dataset.preco;
        
        // Processar preço (suporte a vírgula como separador decimal)
        if (preco && typeof preco === 'string') {
            preco = preco.replace(',', '.').trim();
        }

        // Obter quantidade
        let quantidade = 1;
        const quantityInput = document.querySelector('#quantity, .quantity-input, input[name="quantity"]');
        if (quantityInput && !isNaN(parseInt(quantityInput.value))) {
            quantidade = parseInt(quantityInput.value);
        }

        return {
            id: (dataset.produtoId || dataset.produtoID).toString(),
            nome: dataset.produtoNome || dataset.nome || 'Produto sem nome',
            preco: parseFloat(preco) || 0,
            imagem: dataset.produtoImagem || dataset.imagem || '/static/img/sem-imagem.png',
            quantidade: quantidade
        };
    }

    validarDadosProduto(produto) {
        return produto.id && produto.nome && !isNaN(produto.preco) && produto.preco > 0;
    }

    async verificarEstoque(produtoId, quantidade) {
        try {
            const response = await fetch('/api/verificar-estoque/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    produto_id: produtoId,
                    quantidade: quantidade
                })
            });

            if (!response.ok) {
                throw new Error('Erro ao verificar estoque');
            }

            return await response.json();
        } catch (error) {
            console.error('Erro na verificação de estoque:', error);
            throw error;
        }
    }

    async adicionarAoCarrinho(produto) {
        try {
            // Verificar estoque primeiro
            const estoqueInfo = await this.verificarEstoque(produto.id, produto.quantidade);
            
            if (!estoqueInfo.disponivel) {
                this.mostrarNotificacao(
                    `Estoque insuficiente para ${produto.nome}. Disponível: ${estoqueInfo.estoque_atual}`,
                    'error'
                );
                return false;
            }

            let carrinho = this.obterCarrinho();
            const produtoIndex = carrinho.findIndex(item => item.id === produto.id);

            if (produtoIndex !== -1) {
                // Verificar estoque para a quantidade total
                const novaQuantidade = carrinho[produtoIndex].quantidade + produto.quantidade;
                const estoqueTotalInfo = await this.verificarEstoque(produto.id, novaQuantidade);
                
                if (!estoqueTotalInfo.disponivel) {
                    this.mostrarNotificacao(
                        `Não há estoque suficiente para ${novaQuantidade} unidades. Disponível: ${estoqueTotalInfo.estoque_atual}`,
                        'error'
                    );
                    return false;
                }
                
                carrinho[produtoIndex].quantidade = novaQuantidade;
            } else {
                carrinho.push(produto);
            }

            this.salvarCarrinho(carrinho);
            this.atualizarContadorCarrinho();
            return true;

        } catch (error) {
            console.error('Erro ao adicionar ao carrinho:', error);
            this.mostrarNotificacao('Erro ao verificar estoque do produto.', 'error');
            return false;
        }
    }

    removerDoCarrinho(produtoId) {
        try {
            let carrinho = this.obterCarrinho();
            const initialLength = carrinho.length;
            
            carrinho = carrinho.filter(item => item.id !== produtoId.toString());
            
            if (carrinho.length < initialLength) {
                this.salvarCarrinho(carrinho);
                this.atualizarContadorCarrinho();
                
                if (this.isCheckoutPage()) {
                    this.carregarItensCarrinho();
                }
                
                this.mostrarNotificacao('Produto removido do carrinho.', 'success');
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('Erro ao remover do carrinho:', error);
            this.mostrarNotificacao('Erro ao remover produto do carrinho.', 'error');
            return false;
        }
    }

    async atualizarQuantidade(produtoId, novaQuantidade) {
        try {
            novaQuantidade = parseInt(novaQuantidade);
            
            if (isNaN(novaQuantidade) || novaQuantidade <= 0) {
                return this.removerDoCarrinho(produtoId);
            }

            // Verificar estoque para a nova quantidade
            const estoqueInfo = await this.verificarEstoque(produtoId, novaQuantidade);
            if (!estoqueInfo.disponivel) {
                this.mostrarNotificacao(
                    `Estoque insuficiente. Disponível: ${estoqueInfo.estoque_atual}`,
                    'error'
                );
                return false;
            }

            let carrinho = this.obterCarrinho();
            const produtoIndex = carrinho.findIndex(item => item.id === produtoId.toString());
            
            if (produtoIndex !== -1) {
                carrinho[produtoIndex].quantidade = novaQuantidade;
                this.salvarCarrinho(carrinho);
                
                if (this.isCheckoutPage()) {
                    this.carregarItensCarrinho();
                }
                
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('Erro ao atualizar quantidade:', error);
            this.mostrarNotificacao('Erro ao atualizar quantidade.', 'error');
            return false;
        }
    }

    obterCarrinho() {
        try {
            const carrinhoData = sessionStorage.getItem(this.carrinhoKey);
            return carrinhoData ? JSON.parse(carrinhoData) : [];
        } catch (error) {
            console.error('Erro ao obter carrinho:', error);
            return [];
        }
    }

    salvarCarrinho(carrinho) {
        try {
            sessionStorage.setItem(this.carrinhoKey, JSON.stringify(carrinho));
        } catch (error) {
            console.error('Erro ao salvar carrinho:', error);
        }
    }

    atualizarContadorCarrinho() {
        try {
            const carrinho = this.obterCarrinho();
            const contador = document.getElementById('contador-carrinho');
            
            if (contador) {
                const totalItens = carrinho.reduce((total, item) => total + (item.quantidade || 0), 0);
                contador.textContent = totalItens;
                contador.style.display = totalItens > 0 ? 'inline-block' : 'none';
            }
        } catch (error) {
            console.error('Erro ao atualizar contador:', error);
        }
    }

    carregarItensCarrinho() {
        try {
            const carrinho = this.obterCarrinho();
            const container = document.getElementById('carrinho-itens');
            
            if (!container) return;

            if (carrinho.length === 0) {
                container.innerHTML = this.getEmptyCartHTML();
                this.atualizarTotais(0);
                return;
            }
            
            let html = '';
            let subtotal = 0;
            
            carrinho.forEach(produto => {
                const preco = parseFloat(produto.preco) || 0;
                const quantidade = parseInt(produto.quantidade) || 1;
                const precoTotal = preco * quantidade;
                subtotal += precoTotal;
                
                html += this.getItemHTML(produto, preco, quantidade, precoTotal);
            });
            
            container.innerHTML = html;
            this.atualizarTotais(subtotal);
            
        } catch (error) {
            console.error('Erro ao carregar itens do carrinho:', error);
            this.showCartError();
        }
    }

    getEmptyCartHTML() {
        return `
            <div class="text-center py-5">
                <i class="fas fa-shopping-cart fa-3x text-muted mb-3"></i>
                <h5>Seu carrinho está vazio</h5>
                <p class="text-muted">Adicione produtos para continuar</p>
                <a href="/" class="btn btn-primary">Continuar Comprando</a>
            </div>
        `;
    }

    getItemHTML(produto, preco, quantidade, precoTotal) {
        const imagemSrc = produto.imagem && produto.imagem !== 'undefined' 
            ? produto.imagem 
            : '/static/img/sem-imagem.png';

        return `
            <div class="checkout-item mb-3 p-3 border rounded" data-produto-id="${produto.id}">
                <div class="d-flex align-items-center">
                    <div class="flex-shrink-0">
                        <img src="${imagemSrc}" 
                             alt="${produto.nome}" 
                             class="rounded" 
                             width="80" 
                             height="80" 
                             style="object-fit: cover;"
                             onerror="this.src='/static/img/sem-imagem.png'">
                    </div>
                    <div class="flex-grow-1 ms-3">
                        <h6 class="mb-1">${produto.nome}</h6>
                        <p class="text-muted mb-2">R$ ${preco.toFixed(2)} cada</p>
                        <div class="d-flex align-items-center justify-content-between">
                            <div class="input-group" style="width: 140px;">
                                <button class="btn btn-outline-secondary btn-sm" 
                                        type="button" 
                                        onclick="carrinho.atualizarQuantidade('${produto.id}', ${quantidade - 1})">
                                    -
                                </button>
                                <input type="number" 
                                       class="form-control form-control-sm text-center" 
                                       value="${quantidade}" 
                                       min="1"
                                       onchange="carrinho.atualizarQuantidade('${produto.id}', this.value)">
                                <button class="btn btn-outline-secondary btn-sm" 
                                        type="button" 
                                        onclick="carrinho.atualizarQuantidade('${produto.id}', ${quantidade + 1})">
                                    +
                                </button>
                            </div>
                            <span class="text-primary fw-bold">R$ ${precoTotal.toFixed(2)}</span>
                        </div>
                    </div>
                    <button class="btn btn-link text-danger ms-2" 
                            onclick="carrinho.removerDoCarrinho('${produto.id}')" 
                            title="Remover produto">
                        <i class="fas fa-trash fa-lg"></i>
                    </button>
                </div>
            </div>
        `;
    }

    showCartError() {
        const container = document.getElementById('carrinho-itens');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Erro ao carregar carrinho. Por favor, recarregue a página.
                </div>
            `;
        }
    }

    atualizarTotais(subtotal) {
        try {
            subtotal = parseFloat(subtotal) || 0;
            
            // Usar configurações do Django ou valores padrão
            const freteGratisAcimaDe = typeof FRETE_GRATIS_ACIMA_DE !== 'undefined' ? FRETE_GRATIS_ACIMA_DE : 100;
            const valorFrete = typeof VALOR_FRETE !== 'undefined' ? VALOR_FRETE : 15;
            
            const frete = subtotal > freteGratisAcimaDe ? 0 : valorFrete;
            const total = subtotal + frete;
            
            const elementos = {
                'subtotal': `R$ ${subtotal.toFixed(2)}`,
                'frete': frete > 0 ? `R$ ${frete.toFixed(2)}` : 'Grátis',
                'total': `R$ ${total.toFixed(2)}`
            };
            
            Object.entries(elementos).forEach(([id, texto]) => {
                const elemento = document.getElementById(id);
                if (elemento) {
                    elemento.textContent = texto;
                }
            });
            
        } catch (error) {
            console.error('Erro ao atualizar totais:', error);
        }
    }

    async finalizarCompra() {
        const carrinho = this.obterCarrinho();
        if (carrinho.length === 0) {
            this.mostrarNotificacao('Seu carrinho está vazio!', 'error');
            return;
        }

        // Validar formulário de entrega
        const form = document.getElementById('form-entrega');
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            this.mostrarNotificacao('Preencha todos os campos obrigatórios.', 'error');
            return;
        }

        // Coletar dados do formulário
        const formData = new FormData(form);
        const dadosEntrega = Object.fromEntries(formData.entries());

        try {
            const btn = document.getElementById('btn-finalizar-pagamento');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processando...';
            btn.disabled = true;

            // Verificar estoque final antes do pagamento
            const estoqueResponse = await fetch('/api/atualizar-estoque-carrinho/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ itens: carrinho })
            });

            const estoqueData = await estoqueResponse.json();
            
            if (!estoqueData.valido) {
                throw new Error(estoqueData.mensagem || 'Estoque insuficiente para alguns produtos');
            }

            // Criar preferência de pagamento
            const response = await fetch('/api/criar-preferencia-pagamento/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ 
                    itens: carrinho,
                    dados_entrega: dadosEntrega
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `Erro ${response.status}`);
            }

            if (data.init_point) {
                // Salvar dados temporários e limpar carrinho
                sessionStorage.setItem('ultima_compra', JSON.stringify({
                    carrinho: carrinho,
                    dados_entrega: dadosEntrega,
                    pedido_id: data.pedido_id,
                    data: new Date().toISOString()
                }));
                
                this.limparCarrinho();
                window.location.href = data.init_point;
            } else {
                throw new Error(data.error || 'Link de pagamento não gerado');
            }

        } catch (error) {
            console.error('Erro ao finalizar compra:', error);
            
            const btn = document.getElementById('btn-finalizar-pagamento');
            if (btn) {
                btn.innerHTML = 'Finalizar Pagamento';
                btn.disabled = false;
            }
            
            this.mostrarNotificacao(error.message || 'Erro ao processar pagamento. Tente novamente.', 'error');
        }
    }

    limparCarrinho() {
        sessionStorage.removeItem(this.carrinhoKey);
        this.atualizarContadorCarrinho();
    }

    isCheckoutPage() {
        return window.location.pathname.includes('checkout');
    }

    getCSRFToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === 'csrftoken=') {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue;
    }

    mostrarNotificacao(mensagem, tipo = 'info') {
        try {
            // Usar Bootstrap toast se disponível
            if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
                this.mostrarToastBootstrap(mensagem, tipo);
            } else {
                this.mostrarAlertSimples(mensagem, tipo);
            }
        } catch (error) {
            console.error('Erro ao mostrar notificação:', error);
            alert(mensagem);
        }
    }

    mostrarToastBootstrap(mensagem, tipo) {
        const toastContainer = document.getElementById('toast-container') || this.criarToastContainer();
        
        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-bg-${tipo === 'error' ? 'danger' : tipo === 'success' ? 'success' : 'info'} border-0`;
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas ${this.getIconeTipo(tipo)} me-2"></i>
                    ${mensagem}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastEl);
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
        
        // Remover após ser escondido
        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    }

    mostrarAlertSimples(mensagem, tipo) {
        const notificacao = document.createElement('div');
        notificacao.className = `alert alert-${tipo === 'error' ? 'danger' : tipo === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed`;
        notificacao.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
        notificacao.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas ${this.getIconeTipo(tipo)} me-2"></i>
                <span>${mensagem}</span>
                <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(notificacao);
        
        setTimeout(() => {
            if (notificacao.parentNode) {
                notificacao.parentNode.removeChild(notificacao);
            }
        }, 5000);
    }

    criarToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1090';
        document.body.appendChild(container);
        return container;
    }

    getIconeTipo(tipo) {
        const icones = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'info': 'fa-info-circle'
        };
        return icones[tipo] || 'fa-info-circle';
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    window.carrinho = new CarrinhoManager();
});

// Manter compatibilidade com funções globais existentes
window.adicionarAoCarrinho = (produto) => window.carrinho.adicionarAoCarrinho(produto);
window.removerDoCarrinho = (produtoId) => window.carrinho.removerDoCarrinho(produtoId);
window.atualizarQuantidade = (produtoId, quantidade) => window.carrinho.atualizarQuantidade(produtoId, quantidade);
window.finalizarCompra = () => window.carrinho.finalizarCompra();
window.mostrarNotificacao = (mensagem, tipo) => window.carrinho.mostrarNotificacao(mensagem, tipo);
window.carregarItensCarrinho = () => window.carrinho.carregarItensCarrinho();

console.log('🛒 Carrinho.js carregado com sucesso!');