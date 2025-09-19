document.addEventListener('DOMContentLoaded', function() {
    // Inicializar carrinho
    let carrinho = JSON.parse(sessionStorage.getItem('carrinho')) || [];
    atualizarContadorCarrinho();
    
    // Função para adicionar produto ao carrinho
    function adicionarAoCarrinho(produtoId) {
        carrinho.push(produtoId);
        sessionStorage.setItem('carrinho', JSON.stringify(carrinho));
        atualizarContadorCarrinho();
        
        // Mostrar feedback visual
        alert('Produto adicionado ao carrinho!');
    }
    
    // Função para atualizar contador
    function atualizarContadorCarrinho() {
        const contador = document.getElementById('contador-carrinho');
        if (contador) {
            contador.textContent = carrinho.length;
        }
    }
    
    // Adicionar event listeners aos botões
    document.querySelectorAll('.btn-adicionar-carrinho').forEach(btn => {
        btn.addEventListener('click', function() {
            const produtoId = this.dataset.produtoId;
            adicionarAoCarrinho(produtoId);
        });
    });
    
    // Finalizar compra
    const finalizarCompraBtn = document.getElementById('finalizar-compra');
    if (finalizarCompraBtn) {
        finalizarCompraBtn.addEventListener('click', function() {
            if (carrinho.length === 0) {
                alert('Seu carrinho está vazio!');
                return;
            }
            
            // Simular criação de preferência de pagamento
            fetch('/criar-pagamento/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({itens: carrinho})
            })
            .then(response => response.json())
            .then(data => {
                alert('Redirecionando para o pagamento...');
                console.log('Dados do pagamento:', data);
                // Em produção, aqui você redirecionaria para o Mercado Pago
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro ao processar pagamento.');
            });
        });
    }
    
    // Função auxiliar para obter cookie CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
