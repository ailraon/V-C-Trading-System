import pymysql

"""데이터베이스 연결 확인 코드"""
# MySQL 연결 정보
connection = pymysql.connect(
    host="127.0.0.1",          # Cloud SQL 프록시 주소
    port=3307,                 # 프록시 포트
    user="root",               # MySQL 사용자 이름
    password="1234",           # MySQL 비밀번호
    database="VCDatabase"      # 연결할 데이터베이스 이름
)

try:
    with connection.cursor() as cursor:
        # MySQL 버전 확인
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()
        print(f"MySQL Version: {version[0]}")

        # 데이터베이스 조회 테스트
        cursor.execute("SHOW DATABASES;")
        databases = cursor.fetchall()
        print("Databases:")
        for db in databases:
            print(f" - {db[0]}")

finally:
    connection.close()