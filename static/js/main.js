// main.js - Funcionalidades Essenciais do E-commerce
document.addEventListener('DOMContentLoaded', function() {
    console.log('E-commerce inicializado!');
    
    // Configurações iniciais
    configurarPreferenciasUsuario();
    inicializarModais();
    configurarBuscaEmTempoReal();
    configurarEventListenersGlobais();
});

// ========== PREFERÊNCIAS DO USUÁRIO ==========
function configurarPreferenciasUsuario() {
    // Tema claro/escuro
    const tema = localStorage.getItem('tema') || 'claro';
    document.body.setAttribute('data-tema', tema);
}

// ========== MODAIS ==========
function inicializarModais() {
    // Modal de produto rápido
    document.querySelectorAll('[data-modal-produto]').forEach(btn => {
        btn.addEventListener('click', function() {
            const produtoId = this.dataset.produtoId;
            abrirModalProduto(produtoId);
        });
    });
}

function abrirModal(idModal) {
    const modal = document.getElementById(idModal);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

function fecharModal(idModal) {
    const modal = document.getElementById(idModal);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// ========== BUSCA EM TEMPO REAL ==========
function configurarBuscaEmTempoReal() {
    const barraBusca = document.getElementById('barra-busca');
    if (!barraBusca) return;
    
    let timeoutBusca;
    barraBusca.addEventListener('input', function(e) {
        clearTimeout(timeoutBusca);
        const termo = e.target.value.trim();
        
        if (termo.length > 2) {
            timeoutBusca = setTimeout(() => {
                buscarSugestoes(termo);
            }, 300);
        } else {
            ocultarSugestoes();
        }
    });
}

function buscarSugestoes(termo) {
    // Simulação de dados - substitua pela sua API real
    const produtosSimulados = [
        {id: 1, nome: "Detergente Líquido", preco: "5.90", imagem: "/static/images/detergente.jpg"},
        {id: 2, nome: "Desinfetante Pinho", preco: "8.50", imagem: "/static/images/desinfetante.jpg"},
        {id: 3, nome: "Esponja Multiuso", preco: "2.99", imagem: "/static/images/esponja.jpg"},
        {id: 4, nome: "Água Sanitária", preco: "6.80", imagem: "/static/images/agua-sanitaria.jpg"},
        {id: 5, nome: "Limpa Vidros", preco: "9.90", imagem: "/static/images/limpa-vidros.jpg"}
    ];
    
    const sugestoes = produtosSimulados.filter(produto =>
        produto.nome.toLowerCase().includes(termo.toLowerCase())
    ).slice(0, 5);
    
    mostrarSugestoes(sugestoes);
}

function mostrarSugestoes(sugestoes) {
    const container = document.getElementById('sugestoes-busca');
    if (!container) return;
    
    if (sugestoes.length > 0) {
        container.innerHTML = sugestoes.map(produto => `
            <div class="sugestao-item" onclick="selecionarSugestao('${produto.nome.replace(/'/g, "\\'")}')">
                <i class="fas fa-search me-2"></i>${produto.nome}
            </div>
        `).join('');
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
}

function ocultarSugestoes() {
    const container = document.getElementById('sugestoes-busca');
    if (container) {
        container.style.display = 'none';
    }
}

function selecionarSugestao(termo) {
    document.getElementById('barra-busca').value = termo;
    ocultarSugestoes();
    document.getElementById('barra-busca').focus();
}

// ========== EVENT LISTENERS GLOBAIS ==========
function configurarEventListenersGlobais() {
    // Fechar sugestões ao clicar fora
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-container')) {
            ocultarSugestoes();
        }
    });
    
    // Fechar modais com ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal[style="display: block"]').forEach(modal => {
                fecharModal(modal.id);
            });
        }
    });
}

// Exportar funções para uso global
window.abrirModal = abrirModal;
window.fecharModal = fecharModal;
window.selecionarSugestao = selecionarSugestao;

console.log('Main.js carregado com sucesso!');