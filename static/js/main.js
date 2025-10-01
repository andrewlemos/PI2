/**
 * Main.js - Sistema Principal do E-commerce
 * Versão 2.0 - Corrigida e Integrada
 */

class MainApp {
    constructor() {
        this.init();
    }

    init() {
        console.log('🚀 MainApp inicializado');
        this.setupPreferenciasUsuario();
        this.setupEventListenersGlobais();
        this.setupModais();
        this.verificarDependencias();
    }

    setupPreferenciasUsuario() {
        // Tema claro/escuro
        const tema = localStorage.getItem('tema') || 'claro';
        document.body.setAttribute('data-bs-theme', tema);
        
        // Configurações de acessibilidade
        this.setupAcessibilidade();
    }

    setupAcessibilidade() {
        // Melhorar foco para navegação por teclado
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('user-tabbing');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('user-tabbing');
        });

        // Adicionar skip link para acessibilidade
        this.adicionarSkipLink();
    }

    adicionarSkipLink() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-link btn btn-primary';
        skipLink.innerHTML = 'Pular para o conteúdo principal';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            z-index: 10000;
            transition: top 0.3s;
        `;
        
        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '6px';
        });
        
        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-40px';
        });

        document.body.prepend(skipLink);
    }

    setupModais() {
        // Configurar modais de produto rápido
        document.querySelectorAll('[data-modal-produto]').forEach(btn => {
            btn.addEventListener('click', () => {
                const produtoId = btn.dataset.modalProduto;
                this.abrirModalProduto(produtoId);
            });
        });

        // Melhorar acessibilidade dos modais
        this.enhanceModalAccessibility();
    }

    enhanceModalAccessibility() {
        // Fechar modal com ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.fecharModalAtivo();
            }
        });

        // Manter foco dentro do modal
        document.addEventListener('focusin', (e) => {
            const modal = e.target.closest('.modal');
            if (modal && modal.style.display === 'block') {
                this.trapFocus(modal);
            }
        });
    }

    trapFocus(modal) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        modal.addEventListener('keydown', (e) => {
            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        });
    }

    setupEventListenersGlobais() {
        // Prevenir comportamentos indesejados
        this.setupPrevencoes();
        
        // Melhorar performance
        this.setupOtimizacoes();
        
        // Tratamento de erros global
        this.setupErrorHandling();
    }

    setupPrevencoes() {
        // Prevenir envio duplo de formulários
        document.addEventListener('submit', (e) => {
            const form = e.target;
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processando...';
                
                // Reativar após 5 segundos (fallback)
                setTimeout(() => {
                    if (submitBtn.disabled) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = submitBtn.dataset.originalText || 'Enviar';
                    }
                }, 5000);
            }
        });

        // Prevenir clique rápido em botões
        let lastClickTime = 0;
        document.addEventListener('click', (e) => {
            const now = Date.now();
            if (now - lastClickTime < 500) {
                e.preventDefault();
                e.stopPropagation();
                return;
            }
            lastClickTime = now;
        }, true);
    }

    setupOtimizacoes() {
        // Lazy loading para imagens
        if ('IntersectionObserver' in window) {
            this.setupLazyLoading();
        }

        // Prefetch para links prováveis
        this.setupPrefetch();
    }

    setupLazyLoading() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    observer.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            observer.observe(img);
        });
    }

    setupPrefetch() {
        // Prefetch para páginas prováveis
        const links = document.querySelectorAll('a[href^="/"]');
        links.forEach(link => {
            if (link.href.includes('/produto/') || link.href.includes('/checkout')) {
                link.addEventListener('mouseenter', () => {
                    const prefetchLink = document.createElement('link');
                    prefetchLink.rel = 'prefetch';
                    prefetchLink.href = link.href;
                    document.head.appendChild(prefetchLink);
                }, { once: true });
            }
        });
    }

    setupErrorHandling() {
        // Capturar erros não tratados
        window.addEventListener('error', (e) => {
            console.error('Erro capturado:', e.error);
            this.mostrarErroGlobal('Ocorreu um erro inesperado. A página será recarregada.');
            
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        });

        // Capturar promises rejeitadas
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Promise rejeitada:', e.reason);
            e.preventDefault();
        });
    }

    mostrarErroGlobal(mensagem) {
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-danger border-0 position-fixed top-0 start-50 translate-middle-x mt-3';
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${mensagem}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        document.body.appendChild(toast);
        
        if (typeof bootstrap !== 'undefined') {
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        } else {
            setTimeout(() => toast.remove(), 5000);
        }
    }

    abrirModal(idModal) {
        const modalElement = document.getElementById(idModal);
        if (!modalElement) return;

        if (typeof bootstrap !== 'undefined') {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        } else {
            // Fallback para Bootstrap não carregado
            modalElement.style.display = 'block';
            document.body.style.overflow = 'hidden';
            modalElement.setAttribute('aria-hidden', 'false');
        }
    }

    fecharModal(idModal) {
        const modalElement = document.getElementById(idModal);
        if (!modalElement) return;

        if (typeof bootstrap !== 'undefined') {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) modal.hide();
        } else {
            // Fallback para Bootstrap não carregado
            modalElement.style.display = 'none';
            document.body.style.overflow = 'auto';
            modalElement.setAttribute('aria-hidden', 'true');
        }
    }

    fecharModalAtivo() {
        const modalAtivo = document.querySelector('.modal.show, .modal[style*="display: block"]');
        if (modalAtivo) {
            this.fecharModal(modalAtivo.id);
        }
    }

    async abrirModalProduto(produtoId) {
        try {
            // Carregar dados do produto via API
            const response = await fetch(`/api/produto/${produtoId}/`);
            const produto = await response.json();

            // Criar ou atualizar modal de produto rápido
            this.criarModalProdutoRapido(produto);
            
        } catch (error) {
            console.error('Erro ao carregar produto:', error);
            if (typeof carrinho !== 'undefined') {
                carrinho.mostrarNotificacao('Erro ao carregar produto', 'error');
            }
        }
    }

    criarModalProdutoRapido(produto) {
        let modal = document.getElementById('modal-produto-rapido');
        
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'modal-produto-rapido';
            modal.className = 'modal fade';
            modal.tabIndex = '-1';
            modal.innerHTML = `
                <div class="modal-dialog modal-lg modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Visualização Rápida</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" id="modal-produto-conteudo">
                            <!-- Conteúdo dinâmico -->
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        // Preencher conteúdo do modal
        const conteudo = document.getElementById('modal-produto-conteudo');
        conteudo.innerHTML = this.getProdutoRapidoHTML(produto);

        this.abrirModal('modal-produto-rapido');
    }

    getProdutoRapidoHTML(produto) {
        return `
            <div class="row">
                <div class="col-md-6">
                    <img src="${produto.imagem || '/static/img/sem-imagem.jpg'}" 
                         alt="${produto.nome}" 
                         class="img-fluid rounded"
                         onerror="this.src='/static/img/sem-imagem.jpg'">
                </div>
                <div class="col-md-6">
                    <h4>${produto.nome}</h4>
                    <div class="mb-3">
                        ${produto.preco_original ? `
                            <span class="text-muted text-decoration-line-through">R$ ${produto.preco_original}</span>
                            <span class="h5 text-danger ms-2">R$ ${produto.preco}</span>
                        ` : `
                            <span class="h5 text-primary">R$ ${produto.preco}</span>
                        `}
                    </div>
                    <p class="text-muted">${produto.descricao || 'Sem descrição disponível.'}</p>
                    
                    <div class="d-grid gap-2">
                        <button class="btn btn-primary btn-adicionar-carrinho"
                                data-produto-id="${produto.id}"
                                data-produto-nome="${produto.nome}"
                                data-produto-preco="${produto.preco}"
                                data-produto-imagem="${produto.imagem || '/static/img/sem-imagem.jpg'}">
                            <i class="fas fa-shopping-cart me-2"></i>Adicionar ao Carrinho
                        </button>
                        <a href="/produto/${produto.id}/" class="btn btn-outline-secondary">
                            Ver Detalhes Completos
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    verificarDependencias() {
        // Verificar se Bootstrap está carregado
        if (typeof bootstrap === 'undefined') {
            console.warn('Bootstrap não encontrado. Carregando fallback...');
            this.carregarBootstrapFallback();
        }

        // Verificar se o gerenciador de carrinho está disponível
        setTimeout(() => {
            if (typeof carrinho === 'undefined') {
                console.error('Gerenciador de carrinho não carregado');
            }
        }, 1000);
    }

    carregarBootstrapFallback() {
        // Implementar funcionalidades básicas se Bootstrap não estiver disponível
        console.log('Carregando fallback para funcionalidades do Bootstrap');
    }

    // Utilitários globais
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// Inicializar aplicação
document.addEventListener('DOMContentLoaded', function() {
    window.mainApp = new MainApp();
});

// Manter compatibilidade com funções globais existentes
window.abrirModal = (idModal) => window.mainApp.abrirModal(idModal);
window.fecharModal = (idModal) => window.mainApp.fecharModal(idModal);

console.log('🚀 Main.js carregado com sucesso!');