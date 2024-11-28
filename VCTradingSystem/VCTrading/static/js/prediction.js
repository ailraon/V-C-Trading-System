let predictionChart;

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

async function updatePrediction() {
    try {
        const coinSelect = document.getElementById('coinSelect');
        const selectedCoin = coinSelect.value;
        
        const response = await fetch(`/api/predict/${selectedCoin}/`);
        const data = await response.json();
        
        if (data.status === 'error') {
            throw new Error(data.error);
        }

        // 현재가 업데이트
        const currentPrice = data.current_price;
        if (currentPrice) {
            document.getElementById('currentPrice').textContent = 
                `₩${Math.round(currentPrice).toLocaleString()}`;
        } else {
            document.getElementById('currentPrice').textContent = '가격 조회 실패';
        }

        // 예측 데이터 업데이트
        if (data.dates && data.prices) {
            document.getElementById('predictedPrice').textContent = 
                `₩${Math.round(data.prices[0]).toLocaleString()}`;
            
            document.getElementById('minPrice').textContent = 
                `₩${Math.round(Math.min(...data.prices)).toLocaleString()}`;
            document.getElementById('maxPrice').textContent = 
                `₩${Math.round(Math.max(...data.prices)).toLocaleString()}`;
            
            const avgPrice = data.prices.reduce((a, b) => a + b, 0) / data.prices.length;
            document.getElementById('avgPrice').textContent = 
                `₩${Math.round(avgPrice).toLocaleString()}`;

            // 차트 업데이트
            if (predictionChart) {
                predictionChart.data.labels = data.dates;
                predictionChart.data.datasets[0].data = data.prices;
                predictionChart.update();
            }
        }
        
    } catch (error) {
        console.error('Prediction error:', error);
        // 오류 발생 시 모든 값을 '오류 발생'으로 표시
        document.getElementById('currentPrice').textContent = '오류 발생';
        document.getElementById('predictedPrice').textContent = '오류 발생';
        document.getElementById('minPrice').textContent = '오류 발생';
        document.getElementById('maxPrice').textContent = '오류 발생';
        document.getElementById('avgPrice').textContent = '오류 발생';
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    const coinSelect = document.getElementById('coinSelect');
    const customSearch = document.getElementById('customSearch');
    
    // 초기 BTC 예측
    updatePrediction('BTC');
    
    coinSelect.addEventListener('change', function() {
        if(this.value === 'OTHER') {
            customSearch.classList.remove('hidden');
        } else {
            customSearch.classList.add('hidden');
            updatePrediction(this.value);
        }
    });
});

// prediction.js 수정
document.getElementById('coinSelect').addEventListener('change', function () {
    const selectedCoin = this.value;

    // '그 외' 선택 시 입력 필드 초기화
    if (selectedCoin === 'OTHER') {
        document.getElementById('customCoin').value = '';
    } else {
        document.getElementById('customCoin').value = selectedCoin;
        predictCustomCoin(); // 콤보박스 선택 즉시 예측 실행
    }
});

// 사용자가 직접 입력한 코인 심볼로 예측 요청
async function predictCustomCoin() {
    const coinInput = document.getElementById('customCoin').value.trim().toUpperCase();
    const coinSelect = document.getElementById('coinSelect');

    if (!coinInput) {
        alert('코인 심볼을 입력해주세요.');
        return;
    }

    // 콤보박스 옵션에서 입력값이 없는 경우 '그 외'로 설정
    const validOptions = Array.from(coinSelect.options).map(option => option.value);
    if (!validOptions.includes(coinInput)) {
        coinSelect.value = 'OTHER';
    } else {
        coinSelect.value = coinInput; // 입력값이 콤보박스에 있으면 해당 값 선택
    }

    try {
        // API 요청
        const response = await fetch(`/api/predict/${coinInput}/`);
        const data = await response.json();

        // API 에러 처리
        if (data.status === 'error') {
            alert(data.error || '예측 중 오류가 발생했습니다.');
            return;
        }

        updatePredictionDisplay(data); // 예측 결과 UI 업데이트
    } catch (error) {
        console.error('Prediction error:', error);
        alert(`예측 중 오류가 발생했습니다: ${error.message}`);
    }
}

// 예측 데이터를 화면에 표시
function updatePredictionDisplay(data) {
    if (!data || !data.prices || data.prices.length === 0) {
        alert('예측 데이터를 가져오는 데 실패했습니다.');
        return;
    }

    // 현재가 업데이트
    document.getElementById('currentPrice').textContent = `₩${Math.round(data.current_price).toLocaleString()}`;

    // 예측 가격 업데이트
    document.getElementById('predictedPrice').textContent = `₩${Math.round(data.prices[0]).toLocaleString()}`;

    // 통계 데이터 업데이트
    document.getElementById('minPrice').textContent = `₩${Math.round(data.min_price).toLocaleString()}`;
    document.getElementById('maxPrice').textContent = `₩${Math.round(data.max_price).toLocaleString()}`;
    document.getElementById('avgPrice').textContent = `₩${Math.round(data.avg_price).toLocaleString()}`;

    // 차트 업데이트
    if (predictionChart) {
        predictionChart.data.labels = data.dates;
        predictionChart.data.datasets[0].data = data.prices;
        predictionChart.update();
    }
}