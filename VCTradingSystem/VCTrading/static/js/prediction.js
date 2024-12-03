let predictionChart;
let predictionPeriod = 11;

function initChart() {
    const ctx = document.getElementById('predictionChart').getContext('2d');
    predictionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '예측 가격',
                data: [],
                borderColor: '#4CAF50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `₩${context.parsed.y.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '₩' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

async function updatePrediction(coinId) {
    try {
        const response = await fetch(`/api/predict/${coinId}/?period=${predictionPeriod}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        
        if (data.status === 'error') {
            throw new Error(data.error);
        }

        updateDisplay(data);
    } catch (error) {
        console.error('Prediction error:', error);
        showError();
    }
}

function updateDisplay(data) {
    if (!data || !data.prices || data.prices.length === 0) {
        throw new Error('예측 데이터를 가져오는 데 실패했습니다.');
    }

    // 현재가 업데이트
    document.getElementById('currentPrice').textContent = 
        `₩${Math.round(data.current_price).toLocaleString()}`;

    // 예측 데이터 업데이트
    document.getElementById('predictedPrice').textContent = 
        `₩${Math.round(data.prices[0]).toLocaleString()}`;
    document.getElementById('minPrice').textContent = 
        `₩${Math.round(data.min_price).toLocaleString()}`;
    document.getElementById('maxPrice').textContent = 
        `₩${Math.round(data.max_price).toLocaleString()}`;
    document.getElementById('avgPrice').textContent = 
        `₩${Math.round(data.avg_price).toLocaleString()}`;

    // 차트 업데이트
    if (predictionChart) {
        predictionChart.data.labels = data.dates;
        predictionChart.data.datasets[0].data = data.prices;
        predictionChart.update();
    }
}

function showError() {
    const elements = ['currentPrice', 'predictedPrice', 'minPrice', 'maxPrice', 'avgPrice'];
    elements.forEach(id => document.getElementById(id).textContent = '오류 발생');
}

function setCustomPeriod() {
    const days = document.getElementById('customPeriod').value;
    if (!days || days < 1 || days > 365) {
        alert('1~365일 사이의 값을 입력해주세요.');
        return;
    }
    
    predictionPeriod = parseInt(days);
    const coinSelect = document.getElementById('coinSelect');
    const customCoin = document.getElementById('customCoin');
    
    if (coinSelect.value === 'OTHER' && customCoin.value) {
        predictCustomCoin();
    } else {
        updatePrediction(coinSelect.value);
    }
}

async function predictCustomCoin() {
    const coinInput = document.getElementById('customCoin').value.trim().toUpperCase();
    
    if (!coinInput) {
        alert('코인 심볼을 입력해주세요.');
        return;
    }

    try {
        const response = await fetch(`/api/predict/${coinInput}/?period=${predictionPeriod}`);
        const data = await response.json();
        
        if (response.status === 500 && data.error?.includes('Code not found')) {
            showError('아직 지원하지 않은 가상화폐입니다');
            clearChart();
            return;
        }
        
        if (!response.ok || data.status === 'error') {
            throw new Error('예측 중 오류가 발생했습니다');
        }
        
        updateDisplay(data);
    } catch (error) {
        console.error('Prediction error:', error);
        showError('예측 중 오류가 발생했습니다');
        clearChart();
    }
}

function clearChart() {
    if (predictionChart) {
        predictionChart.data.labels = [];
        predictionChart.data.datasets[0].data = [];
        predictionChart.update();
    }
}

function showError(message = '오류 발생') {
    const elements = ['currentPrice', 'predictedPrice', 'minPrice', 'maxPrice', 'avgPrice'];
    elements.forEach(id => document.getElementById(id).textContent = message);
}

document.addEventListener('DOMContentLoaded', () => {
    const coinSelect = document.getElementById('coinSelect');
    const customSearch = document.getElementById('customSearch');
    const customCoin = document.getElementById('customCoin');
    
    initChart();
    
    // 초기 BTC 예측
    coinSelect.value = 'BTC';
    updatePrediction('BTC');
    
    // 코인 선택 이벤트
    coinSelect.addEventListener('change', function() {
        const selectedCoin = this.value;
        if(selectedCoin === 'OTHER') {
            customSearch.classList.remove('hidden');
            customCoin.value = '';
            customCoin.focus();
        } else {
            customSearch.classList.add('hidden');
            updatePrediction(selectedCoin);
        }
    });

    // Enter 키 이벤트
    customCoin.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            predictCustomCoin();
        }
    });

    // 예측 기간 버튼 이벤트
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            predictionPeriod = parseInt(btn.dataset.days);
            const currentCoin = coinSelect.value === 'OTHER' ? customCoin.value : coinSelect.value;
            if (currentCoin) {
                if (coinSelect.value === 'OTHER') {
                    predictCustomCoin();
                } else {
                    updatePrediction(currentCoin);
                }
            }
        });
    });
});