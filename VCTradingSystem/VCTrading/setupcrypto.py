import pymysql
import requests
from datetime import datetime
from decimal import Decimal

# Upbit API로 데이터 가져오기
def fetch_crypto_data():
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
                "crypto_id": ticker['market'],
                "crypto_type" : ticker['market'].replace('KRW-', ''),
                "crypto_name": market_info['korean_name'],
                "crypto_price": ticker['trade_price'],
                "crypto_volume" : ticker["trade_volume"],
                "crypto_cap" : ticker["acc_trade_price"],
                "executed_price" : ticker["acc_trade_price_24h"],
                "executed_quantity" : ticker["acc_trade_volume_24h"]
            })

    return market_data_with_prices

# Google Cloud SQL(MySQL) 연결
def connect_to_db():
    return pymysql.connect(
        host="127.0.0.1",          # Cloud SQL 프록시 주소
        port=3307,                 # 프록시 포트
        user="root",               # MySQL 사용자 이름
        password="1234",           # MySQL 비밀번호
        database="VCDatabase",      # 연결할 데이터베이스 이름
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

# 데이터 저장 및 업데이트
def save_to_db(data):
    connection = connect_to_db()
    try:
        with connection.cursor() as cursor:
            # CryptoInfo 테이블에 데이터 삽입 또는 업데이트
            for crypto in data:
                sql = """
                INSERT INTO Crypto_Info (
                    crypto_id, crypto_type, crypto_name, crypto_price, crypto_volume, crypto_cap, executed_price, executed_quantity, quote_timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    crypto_price = VALUES(crypto_price),
                    crypto_volume = VALUES(crypto_volume),
                    crypto_cap = VALUES(crypto_cap),
                    executed_price = VALUES(executed_price),
                    executed_quantity = VALUES(executed_quantity),
                    quote_timestamp = VALUES(quote_timestamp)
                """
                cursor.execute(sql, (
                    crypto["crypto_id"],
                    crypto["crypto_type"],
                    crypto["crypto_name"],
                    Decimal(crypto["crypto_price"]),
                    Decimal(crypto["crypto_volume"]),
                    Decimal(crypto["crypto_cap"]),
                    Decimal(crypto["executed_price"]),
                    Decimal(crypto["executed_quantity"]),
                    datetime.now()
                ))
        connection.commit()
    finally:
        connection.close()

if __name__ == "__main__":
    # 1. 데이터 가져오기
    crypto_data = fetch_crypto_data()
    
    # 2. 데이터베이스에 저장
    save_to_db(crypto_data)

    print(crypto_data)