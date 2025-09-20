// carrinho.js - Gerenciamento robusto do carrinho de compras
console.log('Carrinho.js iniciando...');

// Inicializar carrinho
function inicializarCarrinho() {
    console.log('Inicializando carrinho...');
    try {
        const carrinhoData = sessionStorage.getItem('carrinho');
        console.log('Dados do sessionStorage:', carrinhoData);
        
        let carrinho = [];
        if (carrinhoData) {
            carrinho = JSON.parse(carrinhoData);
            console.log('Carrinho parseado:', carrinho);
        }
        
        atualizarContadorCarrinho();
        return carrinho;
    } catch (error) {
        console.error('Erro ao inicializar carrinho:', error);
        return [];
    }
}

// Adicionar produto ao carrinho
function adicionarAoCarrinho(produto) {
    console.log('Tentando adicionar produto:', produto);
    
    try {
        let carrinho = JSON.parse(sessionStorage.getItem('carrinho')) || [];
        
        // Validar dados do produto
        if (!produto || !produto.id) {
            console.error('Dados do produto inválidos:', produto);
            mostrarNotificacao('Erro: Produto inválido.', 'error');
            return false;
        }
        
        // Garantir que os valores sejam corretos
        const produtoProcessado = {
            id: produto.id.toString(),
            nome: produto.nome || 'Produto sem nome',
            preco: parseFloat(produto.preco) || 0,
            imagem: produto.imagem || '/static/img/sem-imagem.png',
            quantidade: parseInt(produto.quantidade) || 1
        };
        
        console.log('Produto processado:', produtoProcessado);

        // Verificar se o produto já está no carrinho
        const produtoExistenteIndex = carrinho.findIndex(item => item.id === produtoProcessado.id);
        
        if (produtoExistenteIndex !== -1) {
            // Se já existe, aumentar a quantidade
            carrinho[produtoExistenteIndex].quantidade += produtoProcessado.quantidade;
            console.log('Produto existente atualizado:', carrinho[produtoExistenteIndex]);
        } else {
            // Se não existe, adicionar novo produto
            carrinho.push(produtoProcessado);
            console.log('Novo produto adicionado:', produtoProcessado);
        }
        
        // Salvar no sessionStorage
        sessionStorage.setItem('carrinho', JSON.stringify(carrinho));
        console.log('Carrinho salvo:', carrinho);
        
        atualizarContadorCarrinho();
        
        // Mostrar feedback visual
        mostrarNotificacao(`${produtoProcessado.quantidade}x ${produtoProcessado.nome} adicionado ao carrinho!`, 'success');
        
        return true;
        
    } catch (error) {
        console.error('Erro ao adicionar ao carrinho:', error);
        mostrarNotificacao('Erro ao adicionar produto ao carrinho.', 'error');
        return false;
    }
}

// Event delegation para botões de adicionar ao carrinho
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.btn-adicionar-carrinho');
    if (!btn) return;
    
    e.preventDefault();
    
    // Obter dados do produto
    const dataset = btn.dataset;
    const id = dataset.produtoId || dataset.produtoID;
    const nome = dataset.produtoNome || dataset.nome;
    let preco = dataset.produtoPreco || dataset.preco;
    const imagem = dataset.produtoImagem || dataset.imagem;
    
    // Processar preço (suporte a vírgula como separador decimal)
    if (preco && typeof preco === 'string') {
        preco = preco.replace(',', '.').trim();
    }
    
    // Obter quantidade (do input ou padrão 1)
    let quantidade = 1;
    const quantityInput = document.querySelector('#quantity, .quantity-input, input[name="quantity"]');
    if (quantityInput && !isNaN(parseInt(quantityInput.value))) {
        quantidade = parseInt(quantityInput.value);
    }
    
    // Validar dados mínimos
    if (!id || !nome || !preco || isNaN(parseFloat(preco))) {
        console.error('Dados insuficientes para adicionar ao carrinho:', {id, nome, preco});
        mostrarNotificacao('Erro: Dados do produto incompletos.', 'error');
        return;
    }
    
    // Criar objeto produto
    const produto = {
        id: id,
        nome: nome,
        preco: parseFloat(preco),
        imagem: imagem,
        quantidade: quantidade
    };
    
    // Adicionar ao carrinho
    adicionarAoCarrinho(produto);
});

// Remover produto do carrinho
function removerDoCarrinho(produtoId) {
    console.log('Removendo produto:', produtoId);
    
    try {
        let carrinho = JSON.parse(sessionStorage.getItem('carrinho')) || [];
        const initialLength = carrinho.length;
        
        carrinho = carrinho.filter(item => item.id !== produtoId.toString());
        
        if (carrinho.length < initialLength) {
            sessionStorage.setItem('carrinho', JSON.stringify(carrinho));
            console.log('Produto removido. Carrinho atual:', carrinho);
            
            atualizarContadorCarrinho();
            
            // Recarregar itens se estiver na página do carrinho
            if (window.location.pathname.includes('carrinho') || window.location.pathname.includes('checkout')) {
                carregarItensCarrinho();
            }
            
            mostrarNotificacao('Produto removido do carrinho.', 'success');
            return true;
        } else {
            console.log('Produto não encontrado para remover:', produtoId);
            return false;
        }
        
    } catch (error) {
        console.error('Erro ao remover do carrinho:', error);
        mostrarNotificacao('Erro ao remover produto do carrinho.', 'error');
        return false;
    }
}

// Atualizar quantidade do produto
function atualizarQuantidade(produtoId, novaQuantidade) {
    console.log('Atualizando quantidade:', produtoId, novaQuantidade);
    
    try {
        let carrinho = JSON.parse(sessionStorage.getItem('carrinho')) || [];
        const produtoIndex = carrinho.findIndex(item => item.id === produtoId.toString());
        
        if (produtoIndex !== -1) {
            novaQuantidade = parseInt(novaQuantidade);
            
            if (isNaN(novaQuantidade) || novaQuantidade <= 0) {
                // Remover se quantidade for 0 ou negativa
                return removerDoCarrinho(produtoId);
            } else {
                carrinho[produtoIndex].quantidade = novaQuantidade;
                sessionStorage.setItem('carrinho', JSON.stringify(carrinho));
                console.log('Quantidade atualizada:', carrinho[produtoIndex]);
                
                // Recarregar itens se estiver na página do carrinho
                if (window.location.pathname.includes('carrinho') || window.location.pathname.includes('checkout')) {
                    carregarItensCarrinho();
                }
                
                return true;
            }
        } else {
            console.log('Produto não encontrado para atualizar:', produtoId);
            return false;
        }
        
    } catch (error) {
        console.error('Erro ao atualizar quantidade:', error);
        mostrarNotificacao('Erro ao atualizar quantidade.', 'error');
        return false;
    }
}

// Atualizar contador do carrinho
function atualizarContadorCarrinho() {
    try {
        const carrinho = JSON.parse(sessionStorage.getItem('carrinho')) || [];
        const contador = document.getElementById('contador-carrinho');
        
        if (contador) {
            const totalItens = carrinho.reduce((total, item) => total + (item.quantidade || 0), 0);
            contador.textContent = totalItens;
            contador.style.display = totalItens > 0 ? 'inline-block' : 'none';
            console.log('Contador atualizado:', totalItens);
        }
    } catch (error) {
        console.error('Erro ao atualizar contador:', error);
    }
}

// Carregar itens do carrinho na página
function carregarItensCarrinho() {
    console.log('Carregando itens do carrinho...');
    
    try {
        const carrinho = JSON.parse(sessionStorage.getItem('carrinho')) || [];
        const container = document.getElementById('carrinho-itens');
        
        if (!container) {
            console.log('Container de carrinho não encontrado');
            return;
        }
        
        console.log('Carrinho atual:', carrinho);

        if (carrinho.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-shopping-cart fa-3x text-muted mb-3"></i>
                    <h5>Seu carrinho está vazio</h5>
                    <p class="text-muted">Adicione produtos para continuar</p>
                    <a href="/" class="btn btn-primary">Continuar Comprando</a>
                </div>
            `;
            atualizarTotais(0);
            return;
        }
        
        let html = '';
        let subtotal = 0;
        
        carrinho.forEach(produto => {
            // Garantir valores numéricos
            const preco = parseFloat(produto.preco) || 0;
            const quantidade = parseInt(produto.quantidade) || 1;
            const precoTotal = preco * quantidade;
            subtotal += precoTotal;
            
            // Usar imagem padrão se não houver
            const imagemSrc = produto.imagem && produto.imagem !== 'undefined' 
                ? produto.imagem 
                : '/static/img/sem-imagem.png';
            
            html += `
                <div class="checkout-item" data-produto-id="${produto.id}">
                    <div class="d-flex align-items-center">
                        <div class="flex-shrink-0">
                            <img src="${imagemSrc}" 
                                 alt="${produto.nome || 'Produto'}" 
                                 class="rounded" width="80" height="80" style="object-fit: cover;"
                                 onerror="this.src='/static/img/sem-imagem.png'">
                        </div>
                        <div class="flex-grow-1 ms-3">
                            <h6 class="mb-1">${produto.nome || 'Produto sem nome'}</h6>
                            <p class="text-muted mb-2">R$ ${preco.toFixed(2)} cada</p>
                            <div class="d-flex align-items-center justify-content-between">
                                <div class="input-group" style="width: 140px;">
                                    <button class="btn btn-outline-secondary btn-sm" type="button" 
                                            onclick="atualizarQuantidade('${produto.id}', ${quantidade - 1})">-</button>
                                    <input type="number" class="form-control form-control-sm text-center" 
                                           value="${quantidade}" min="1"
                                           onchange="atualizarQuantidade('${produto.id}', this.value)">
                                    <button class="btn btn-outline-secondary btn-sm" type="button" 
                                            onclick="atualizarQuantidade('${produto.id}', ${quantidade + 1})">+</button>
                                </div>
                                <span class="text-primary fw-bold">R$ ${precoTotal.toFixed(2)}</span>
                            </div>
                        </div>
                        <button class="btn btn-link text-danger ms-2" onclick="removerDoCarrinho('${produto.id}')" 
                                title="Remover produto">
                            <i class="fas fa-trash fa-lg"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        
        // Atualizar interface
        container.innerHTML = html;
        atualizarTotais(subtotal);
        console.log('Itens do carrinho carregados com sucesso');
        
    } catch (error) {
        console.error('Erro ao carregar itens do carrinho:', error);
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
}

// Atualizar totais do pedido
function atualizarTotais(subtotal) {
    try {
        subtotal = parseFloat(subtotal) || 0;
        
        // Calcular frete (grátis para compras acima de R$ 100)
        const frete = subtotal > 100 ? 0 : 15;
        const total = subtotal + frete;
        
        // Atualizar elementos da interface
        const elementos = {
            'subtotal': `R$ ${subtotal.toFixed(2)}`,
            'frete': `R$ ${frete.toFixed(2)}`,
            'desconto': '- R$ 0,00',
            'total': `R$ ${total.toFixed(2)}`
        };
        
        Object.entries(elementos).forEach(([id, texto]) => {
            const elemento = document.getElementById(id);
            if (elemento) {
                elemento.textContent = texto;
            }
        });
        
        console.log('Totais atualizados:', elementos);
        
    } catch (error) {
        console.error('Erro ao atualizar totais:', error);
    }
}

// Finalizar compra
function finalizarCompra() {
    try {
        const carrinho = JSON.parse(sessionStorage.getItem('carrinho')) || [];
        
        if (carrinho.length === 0) {
            mostrarNotificacao('Seu carrinho está vazio!', 'error');
            return;
        }
        
        const form = document.getElementById('form-entrega');
        if (form && !form.checkValidity()) {
            form.classList.add('was-validated');
            mostrarNotificacao('Por favor, preencha todos os campos obrigatórios.', 'error');
            return;
        }
        
        // Simular processo de pagamento
        const btn = document.getElementById('btn-finalizar-pagamento');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Processando...';
        }
        
        // Simular delay do processamento
        setTimeout(() => {
            mostrarNotificacao('Compra finalizada com sucesso!', 'success');
            
            // Limpar carrinho após compra
            sessionStorage.removeItem('carrinho');
            atualizarContadorCarrinho();
            
            // Redirecionar para página inicial após 2 segundos
            setTimeout(() => {
                window.location.href = "/";
            }, 2000);
        }, 2000);
        
    } catch (error) {
        console.error('Erro ao finalizar compra:', error);
        mostrarNotificacao('Erro ao finalizar compra. Tente novamente.', 'error');
        
        const btn = document.getElementById('btn-finalizar-pagamento');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = 'Finalizar Pagamento';
        }
    }
}

// Função de notificação
function mostrarNotificacao(mensagem, tipo = 'info') {
    try {
        // Criar elemento de notificação simples
        const notificacao = document.createElement('div');
        notificacao.className = `alert alert-${tipo === 'error' ? 'danger' : tipo === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed`;
        notificacao.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
        notificacao.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas ${tipo === 'error' ? 'fa-exclamation-circle' : tipo === 'success' ? 'fa-check-circle' : 'fa-info-circle'} me-2"></i>
                <span>${mensagem}</span>
                <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(notificacao);
        
        // Remover após 3 segundos
        setTimeout(() => {
            if (notificacao.parentNode) {
                notificacao.parentNode.removeChild(notificacao);
            }
        }, 3000);
        
    } catch (error) {
        console.error('Erro ao mostrar notificação:', error);
        alert(mensagem); // Fallback simples
    }
}

// Debug: Verificar sessionStorage
function debugCarrinho() {
    console.log('=== DEBUG CARRINHO ===');
    console.log('sessionStorage carrinho:', sessionStorage.getItem('carrinho'));
    console.log('JSON parseado:', JSON.parse(sessionStorage.getItem('carrinho') || '[]'));
    console.log('======================');
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM carregado, inicializando carrinho...');
    
    try {
        inicializarCarrinho();
        
        // Carregar itens do carrinho se estiver na página de checkout/carrinho
        if (window.location.pathname.includes('carrinho') || window.location.pathname.includes('checkout')) {
            console.log('Página de carrinho/checkout detectada');
            carregarItensCarrinho();
        }
        
        // Configurar botão de finalizar compra
        const finalizarBtn = document.getElementById('btn-finalizar-pagamento');
        if (finalizarBtn) {
            finalizarBtn.addEventListener('click', finalizarCompra);
        }
        
        console.log('Carrinho inicializado com sucesso');
        
    } catch (error) {
        console.error('Erro na inicialização do carrinho:', error);
    }
});

// Exportar funções para uso global
window.adicionarAoCarrinho = adicionarAoCarrinho;
window.removerDoCarrinho = removerDoCarrinho;
window.atualizarQuantidade = atualizarQuantidade;
window.finalizarCompra = finalizarCompra;
window.mostrarNotificacao = mostrarNotificacao;
window.carregarItensCarrinho = carregarItensCarrinho;
window.debugCarrinho = debugCarrinho;

console.log('Carrinho.js carregado com sucesso!');