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
        const response = await fetch('/api/predict/ZRX/');
        const data = await response.json();
        
        if (data.status === 'error') {
            throw new Error(data.error);
        }

        // 현재가 업데이트
        document.getElementById('currentPrice').textContent = 
            `₩${Math.round(data.current_price).toLocaleString()}`;

        // 예측 가격 업데이트
        const firstPrediction = Math.round(data.predictions.prices[0]);
        document.getElementById('predictedPrice').textContent = 
            `₩${firstPrediction.toLocaleString()}`;

        // 통계 데이터 업데이트
        document.getElementById('minPrice').textContent = 
            `₩${Math.round(data.predictions.min_price).toLocaleString()}`;
        document.getElementById('maxPrice').textContent = 
            `₩${Math.round(data.predictions.max_price).toLocaleString()}`;
        document.getElementById('avgPrice').textContent = 
            `₩${Math.round(data.predictions.avg_price).toLocaleString()}`;

        // 차트 업데이트
        updateChart(data.predictions.dates, data.predictions.prices);
        
    } catch (error) {
        console.error('Prediction error:', error);
        document.getElementById('currentPrice').textContent = '오류 발생';
        document.getElementById('predictedPrice').textContent = '오류 발생';
        document.getElementById('minPrice').textContent = '오류 발생';
        document.getElementById('maxPrice').textContent = '오류 발생';
        document.getElementById('avgPrice').textContent = '오류 발생';
    }
}

function updateChart(dates, prices) {
    if (predictionChart && dates && prices) {
        predictionChart.data.labels = dates;
        predictionChart.data.datasets[0].data = prices;
        predictionChart.update();
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    updatePrediction();
});