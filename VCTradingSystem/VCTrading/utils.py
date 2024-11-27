import pyupbit
import requests

def get_markets():
    """
    업비트 지원 마켓 목록 조회
    """
    try:
        # url = "https://api.upbit.com/v1/market/all"
        # response = requests.get(url)
        # response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        # data = response.json()
        # return data  # 시장 정보 (예: [{'market': 'KRW-BTC', 'korean_name': '비트코인', ...}])
        markets = pyupbit.get_tickers(fiat="KRW")
        return markets
    except requests.exceptions.RequestException as e:
        print(f"Error fetching market data: {e}")
        return []

def get_current_price(market):
    """
    특정 마켓의 현재 가격 조회
    """
    try:
        price = pyupbit.get_current_price(market)
        return price
    except Exception as e:
        print(f"Error fetching current price for {market}: {e}")
        return None

def get_krw_markets_with_prices_and_change():
    # 1. 업비트 마켓 정보 가져오기
    market_url = "https://api.upbit.com/v1/market/all?is_details=true"
    headers = {"accept": "application/json"}
    market_response = requests.get(market_url, headers=headers)
    markets = market_response.json()

    # 2. KRW 마켓 필터링
    krw_markets = [market['market'] for market in markets if market['market'].startswith('KRW')]

    # 3. Ticker API로 현재가 및 변동률 정보 가져오기
    ticker_url = "https://api.upbit.com/v1/ticker/all"
    params = {"quote_currencies": "KRW"}
    ticker_response = requests.get(ticker_url, headers=headers, params=params)
    tickers = ticker_response.json()

    # 4. KRW 마켓 데이터 병합
    market_data_with_prices = []
    for ticker in tickers:
        market_info = next((market for market in markets if market['market'] == ticker['market']), None)
        if market_info:
            market_data_with_prices.append({
                "market": ticker['market'],
                "korean_name": market_info['korean_name'],
                "english_name": market_info['english_name'],
                "current_price": ticker['trade_price'],               # 현재가
                "change_rate": round(ticker['change_rate'] * 100, 1),   # 변동률 (%)
            })

    return market_data_with_prices

# 결과 출력
# market_data = get_krw_markets_with_prices()
# for data in market_data:
#     print(f"{data['market']} ({data['korean_name']}, {data['english_name']}): {data['current_price']} KRW")
