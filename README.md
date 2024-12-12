# 🏦 V&C Trading System(가상화폐 거래 시스템)

💱 가상화폐 거래 웹 서비스

## 📋 프로젝트 정보

### ⏰ 1. 제작기간
2024.09.10 ~ 2024.12.14

### 👥 2. 팀 구성
| Name | Position |
|------|----------|
| 김민욱 | 착수, 계획, 분석 팀장 |
| 이성균 | 시험, 종료 팀장 |
| 정형일 | 설계, 구현 팀장 |

### 🛠️ 3. 기술 스택
| **Category**        | **Technology**               |
|---------------------|------------------------------|
| Backend Framework   | Django (Python)              |
| Frontend            | HTML, CSS, JavaScript        |
| Chart Library       | Lightweight Charts, d3       |
| Database            | MySQL (Google Cloud SQL)     |
| Deployment          | Google Cloud Run             |
| Cloud Storage       | Google Cloud Storage         |
| Authentication      | Django Authentication        |
| API Integration     | Cryptocurrency APIs (Upbit)  |

### 📊 4. 시스템 구조
Frontend (HTML, JS, CSS) 
↕ 
Backend (Django Framework) 
↕ 
Database (MySQL via Google Cloud SQL) 
↕ 
Cloud (Google Cloud Run & Google Cloud Storage)

### 🔍 5. 주요 기능
1. **실시간 가상화폐 거래**
   - 실시간 시장 데이터를 확인하고 매수/매도를 간편하게 실행할 수 있습니다.
   - 가상화폐 API를 통해 최신 데이터를 제공합니다.

2. **포트폴리오 관리**
   - 보유 자산, 평균 매수가, 수익/손실을 직관적으로 확인 가능합니다.

3. **캔들스틱 차트**
   - 시장 변동성을 시각화하여 트렌드를 분석할 수 있습니다.
   - **D3**를 활용하여 차트 구현.

4. **가상화폐 예측**
   - 여러 변수를 이용하여 인공지능통한 가상화폐 예측 기능 제공.
   - **Lightweight Charts**를 활용한 동적 차트 구현.

4. **안전한 인증 시스템**
   - CSRF 보호를 포함한 사용자 인증 및 세션 관리.

5. **확장 가능한 배포**
   - **Docker**를 통해 컨테이너화되어 **Google Cloud Run**에 배포.
   - 정적 파일은 **Google Cloud Storage**를 통해 제공.

### Live Demo
- live site : https://trading-system-862908053898.asia-northeast3.run.app

---

## 📑 기능 설명

### 사용자 인증
- **로그인**: CSRF 보호를 포함한 안전한 로그인.
- **세션 관리**: 사용자 데이터의 안전한 관리.

### 시장 현황
- **실시간 가격 확인**: 시장 데이터를 실시간으로 확인.
- **필터 기능**: 인기순, 변동률 등으로 정렬.

### 거래
- **매수/매도**: 간편한 주문 처리.
- **거래 기록**: 과거 거래 내역 및 포트폴리오 통계 확인.

### 데이터 시각화
- **캔들스틱 차트**: 가격 변동 트렌드를 분석.
- **성능 지표**: 실시간 수익/손실 확인.

### AI 활용
- **가상화폐 예측**: tensorflow를 활용하여 가상화폐 정보를 예측 및 예측 정보 제공

---