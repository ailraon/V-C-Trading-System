import json
from django.http import JsonResponse
import requests

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
    # market_data_json = json.dumps(market_data_with_prices, ensure_ascii=False)  # ensure_ascii=False는 한글을 처리
    # print("DEBUG: market_data_json =", market_data_json)
    # return market_data_json

def get_crypto_detail_info(crypto_id, market_data):
    """가상화폐 상세정보"""
    server_url = "https://api.upbit.com/v1/ticker"

    params = {
        "markets": crypto_id
    }

    res = requests.get(server_url, params=params)
    details = res.json()

    # 필터링하여 추가 정보 병합
    filtered_item = next((item for item in market_data if item["market"] == crypto_id), None)
    if filtered_item and details:
        for detail in details:
            detail["korean_name"] = filtered_item["korean_name"]

    return details

def get_crypto_detail_chart_info(crypto_id, time):

    url = "https://api.upbit.com/v1/candles/"
    params = {  
        'market': crypto_id,  
        'count': 100,
        'to': ''
    }  
    headers = {"accept": "application/json"}

    times = {
        's': 'seconds',
        'm1': 'minutes/1',
        'm5': 'minutes/5',
        'm15': 'minutes/15',
        'h1': 'minutes/60',
        'd': 'days',
        'w': 'weeks',
        'm': 'months'
    }

    response = requests.get(url + times[time], params=params, headers=headers)

    datas = response.json()
    
    return datas