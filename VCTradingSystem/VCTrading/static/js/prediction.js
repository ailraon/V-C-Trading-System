// 전역 변수
let chart = null;
let candleSeries = null;
let currentChartData = []; // 현재 캔들스틱 데이터를 추적
let predictionPeriod = 11;

function initChart() {
    try {
        const container = document.getElementById('predictionChart');
        if (!container) {
            console.error('Chart container not found');
            return false;
        }

        // 기존 차트 제거
        if (chart) {
            chart.remove();
            container.innerHTML = '';
        }

        // 초기 크기 설정
        const defaultWidth = Math.max(container.clientWidth, 1000);
        const defaultHeight = Math.max(container.clientHeight, 700);

        // 차트 생성
        chart = LightweightCharts.createChart(container, {
            width: defaultWidth,
            height: defaultHeight,
            layout: {
                background: { type: 'solid', color: 'white' },
                textColor: 'black',
                fontSize: 14,
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif',
            },
            grid: {
                vertLines: { color: '#E0E0E0' },
                horzLines: { color: '#E0E0E0' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#DFDFDF',
                visible: true,
                autoScale: true,
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1,
                },
            },
            timeScale: {
                borderColor: '#DFDFDF',
                timeVisible: true,
                secondsVisible: false,
                rightOffset: 2,        // 오른쪽 여백 감소
                leftOffset: 10,        // 왼쪽 여백 추가
                barSpacing: 40,
                minBarSpacing: 20,
                fixLeftEdge: false,    // 왼쪽 고정 해제
                fixRightEdge: false,   // 오른쪽 고정 해제
            },
            handleScale: true,
            handleScroll: true,
        });

        // 캔들스틱 시리즈 추가
        candleSeries = chart.addCandlestickSeries({
            upColor: '#FF4C4C',
            downColor: '#4C9BFF',
            borderUpColor: '#FF4C4C',
            borderDownColor: '#4C9BFF',
            wickUpColor: '#FF4C4C',
            wickDownColor: '#4C9BFF',
            priceFormat: { type: 'price', precision: 0, minMove: 1 },
        });

        // 반응형 설정
        const resizeChart = () => {
            const width = container.clientWidth;
            const height = Math.max(container.clientHeight, 700);
            chart.resize(width, height);
            chart.timeScale().fitContent();
        };

        // 초기 크기 조정
        window.addEventListener('resize', resizeChart);
        
        // 초기 데이터 로드 후 왼쪽으로 스크롤
        setTimeout(() => {
            chart.timeScale().scrollToPosition(-10, false);
        }, 100);

        return true;
    } catch (error) {
        console.error('Chart initialization error:', error);
        return false;
    }
}

// 예제 데이터 업데이트 함수
function updateChartData(data) {
    if (candleSeries && data) {
        candleSeries.setData(data);
    }
}

// DOMContentLoaded 이벤트에서 차트 초기화
document.addEventListener('DOMContentLoaded', () => {
    if (!initChart()) {
        console.error('Chart initialization failed');
    }
});


async function updatePrediction(coinId) {
    try {
        showLoading();
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

function generateRandomPrice(basePrice) {
    const change = (Math.random() - 0.5) * 2 * (basePrice * 0.02);
    return basePrice + change;
}

function updateDisplay(data) {
    if (!data || !data.prices || data.prices.length === 0) {
        throw new Error('예측 데이터를 가져오는 데 실패했습니다.');
    }

    // 기본 정보 업데이트
    document.getElementById('currentPrice').textContent = 
        `₩${Math.round(data.current_price).toLocaleString()}`;
    document.getElementById('predictedPrice').textContent = 
        `₩${Math.round(data.prices[0]).toLocaleString()}`;
    document.getElementById('minPrice').textContent = 
        `₩${Math.round(data.min_price).toLocaleString()}`;
    document.getElementById('maxPrice').textContent = 
        `₩${Math.round(data.max_price).toLocaleString()}`;
    document.getElementById('avgPrice').textContent = 
        `₩${Math.round(data.avg_price).toLocaleString()}`;

    // 캔들스틱 데이터 생성
    const candleData = [];
    let lastPrice = data.current_price;

    for (let i = 0; i < data.prices.length; i++) {
        const time = Math.floor(new Date(data.dates[i]).getTime() / 1000);
        const currentPrice = data.prices[i];

        // 변동성 계산
        const volatility = currentPrice * 0.01;

        // 시가와 종가 계산
        const open = lastPrice;
        const close = currentPrice;

        // 고가와 저가 계산
        const high = Math.max(open, close) + volatility;
        const low = Math.min(open, close) - volatility;

        candleData.push({
            time: time,
            open: open,
            high: high,
            low: low,
            close: close,
        });

        lastPrice = currentPrice;
    }

    // 차트 업데이트
    if (candleSeries) {
        candleSeries.setData([]);  // 기존 데이터 초기화
        requestAnimationFrame(() => {
            candleSeries.setData(candleData);
            chart.timeScale().fitContent();
            
            // 추가 지연 후 한 번 더 fitContent 실행
            setTimeout(() => {
                chart.timeScale().fitContent();
            }, 100);
        });
    }
}

function showLoading() {
    const elements = ['currentPrice', 'predictedPrice', 'minPrice', 'maxPrice', 'avgPrice'];
    elements.forEach(id => {
        document.getElementById(id).textContent = '로딩중...';
    });
}

function showError(message = '오류 발생') {
    const elements = ['currentPrice', 'predictedPrice', 'minPrice', 'maxPrice', 'avgPrice'];
    elements.forEach(id => {
        document.getElementById(id).textContent = message;
    });

    if (candleSeries) {
        candleSeries.setData([]);
    }
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
        showLoading();
        await updatePrediction(coinInput);
    } catch (error) {
        console.error('Custom coin prediction error:', error);
        showError('예측 중 오류가 발생했습니다');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (typeof LightweightCharts === 'undefined') {
        console.error('LightweightCharts 라이브러리를 찾을 수 없습니다');
        showError('차트 초기화 실패');
        return;
    }

    const coinSelect = document.getElementById('coinSelect');
    const customSearch = document.getElementById('customSearch');
    const customCoin = document.getElementById('customCoin');

    // 차트 초기화
    if (!initChart()) {
        showError('차트 초기화 실패');
        return;
    }

    // 초기 데이터 로드
    updatePrediction('BTC');

    // 이벤트 리스너 설정
    coinSelect.addEventListener('change', function() {
        const selectedCoin = this.value;
        if (selectedCoin === 'OTHER') {
            customSearch.classList.remove('hidden');
            customCoin.value = '';
            customCoin.focus();
        } else {
            customSearch.classList.add('hidden');
            updatePrediction(selectedCoin);
        }
    });

    customCoin.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            predictCustomCoin();
        }
    });

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