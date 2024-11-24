import pymysql

# MySQL 연결 설정
db_config = {
    "host": "127.0.0.1",          # Cloud SQL 프록시 주소
    "port" : 3307,                 # 프록시 포트
    "user" : "root",               # MySQL 사용자 이름
    "password" : "1234",           # MySQL 비밀번호
    "database" : "VCDatabase"      # 연결할 데이터베이스 이름
}

# 데이터베이스 연결
connection = pymysql.connect(**db_config)

try:
    with connection.cursor() as cursor:
        # 1. 테이블 생성
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute("USE VCDatabase;")
        print("Database selected: VCDatabase")
        # cursor.execute(create_table_query)
        # print("Table 'users' created successfully.")

        # 2. 데이터 삽입
        insert_data_query = """
        INSERT INTO users (name, email)
        VALUES (%s, %s);
        """
        user_data = [
            ("Alice1", "alice1@example.com"),
            ("Bob1", "bob1@example.com"),
            ("Charlie1", "charlie1@example.com")
        ]
        cursor.executemany(insert_data_query, user_data)
        connection.commit()  # 변경 사항 저장
        print(f"{cursor.rowcount} rows inserted into 'users' table.")

        # 3. 데이터 확인
        cursor.execute("SELECT * FROM users;")
        rows = cursor.fetchall()
        print("Inserted data:")
        for row in rows:
            print(row)

finally:
    # 연결 종료
    connection.close()
    print("Database connection closed.")