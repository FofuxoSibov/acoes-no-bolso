document.addEventListener('DOMContentLoaded', () => {
    const collectBtn = document.getElementById('collect-btn');
    const statusMessage = document.getElementById('status-message');
    const historyTable = document.getElementById('history-table');
    const thead = historyTable.querySelector('thead');
    const tbody = historyTable.querySelector('tbody');

    // Mapeamento para nomes amigáveis das colunas
    const COLUMN_NAMES = {
        'ticker': 'Ticker',
        'reference_month': 'Mês',
        'regular_market_price': 'Preço (R$)',
        'regular_market_change_percent': 'Variação (%)',
        'market_cap': 'Valor de Mercado',
        'regular_market_volume': 'Volume',
        'price_earnings': 'P/L',
        'earnings_per_share': 'LPA',
        'fifty_two_week_low': 'Mínima 52s',
        'fifty_two_week_high': 'Máxima 52s'
    };

    let priceChart = null;

    function showStatus(message, isError = false) {
        statusMessage.textContent = message;
        statusMessage.className = isError ? 'error' : 'success';
        statusMessage.classList.remove('hidden');
        setTimeout(() => {
            statusMessage.classList.add('hidden');
        }, 5000);
    }

    async function loadData() {
        try {
            const response = await fetch('/api/history');
            if (!response.ok) throw new Error('Erro ao buscar dados');
            const data = await response.json();
            renderTable(data);
            renderChart(data);
        } catch (error) {
            showStatus(error.message, true);
        }
    }

    function renderChart(data) {
        const ctx = document.getElementById('priceChart').getContext('2d');
        if (priceChart) priceChart.destroy();
        if (!data || data.length === 0) return;

        // Filtrar apenas os últimos 30 dias
        const hoje = new Date();
        const trintaDiasAtras = new Date();
        trintaDiasAtras.setDate(hoje.getDate() - 30);

        const dataFiltrada = data.filter(d => {
            // Usa reference_month ou collected_at dependendo da disponibilidade
            const dataCotacao = new Date(d.reference_month || d.collected_at);
            return dataCotacao >= trintaDiasAtras;
        });

        if (dataFiltrada.length === 0) {
            // Se não houver dados nos últimos 30 dias, exibe o mais recente
            dataFiltrada.push(...data.slice(-10)); // Exemplo de fallback
        }

        // Pegar meses únicos ordenados e tickers únicos
        const labels = Array.from(new Set(dataFiltrada.map(d => d.reference_month))).sort();
        const tickers = Array.from(new Set(dataFiltrada.map(d => d.ticker)));
        const colors = ['#2c3e50', '#27ae60', '#e74c3c', '#f39c12', '#9b59b6', '#34495e', '#16a085'];

        const datasets = tickers.map((ticker, index) => {
            const tickerData = dataFiltrada.filter(d => d.ticker === ticker);
            const dataPoints = labels.map(month => {
                const record = tickerData.find(d => d.reference_month === month);
                return record ? record.regular_market_price : null;
            });
            return {
                label: ticker,
                data: dataPoints,
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length],
                tension: 0.1,
                fill: false,
                spanGaps: true
            };
        });

        priceChart = new Chart(ctx, {
            type: 'line',
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: { legend: { position: 'top' } },
                scales: {
                    y: { title: { display: true, text: 'Preço (R$)' } }
                }
            }
        });
    }

    function renderTable(data) {
        thead.innerHTML = '';
        tbody.innerHTML = '';

        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="100%">Nenhum dado encontrado.</td></tr>';
            return;
        }

        // Criar cabeçalhos
        const columns = Object.keys(data[0]);
        const trHead = document.createElement('tr');
        columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = COLUMN_NAMES[col] || col;
            trHead.appendChild(th);
        });
        thead.appendChild(trHead);

        // Criar linhas
        data.forEach(row => {
            const tr = document.createElement('tr');
            columns.forEach(col => {
                const td = document.createElement('td');
                let val = row[col];
                
                // Formatação
                if (typeof val === 'number') {
                    if (val % 1 !== 0) {
                        val = val.toFixed(2); // Duas casas decimais
                    } else if (val > 1000) {
                        val = val.toLocaleString('pt-BR'); // Separador de milhares
                    }
                } else if (val === null || val === undefined) {
                    val = '-';
                }
                
                td.textContent = val;
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    collectBtn.addEventListener('click', async () => {
        collectBtn.disabled = true;
        collectBtn.textContent = 'Atualizando...';
        showStatus('Coletando novos dados...');

        try {
            const response = await fetch('/api/collect', { method: 'POST' });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Erro ao coletar dados');
            }
            const result = await response.json();
            showStatus(`Sucesso! Linhas atualizadas: ${result.rows_updated}`);
            await loadData(); // Recarrega a tabela após sucesso
        } catch (error) {
            showStatus(error.message, true);
        } finally {
            collectBtn.disabled = false;
            collectBtn.textContent = 'Atualizar Dados (BRAPI)';
        }
    });

    // Carga inicial
    loadData();
});

