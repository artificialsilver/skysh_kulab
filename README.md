# 업비트 WebSocket 실시간 거래 데이터 수집 시스템

## 📋 개요

이 프로젝트는 **업비트 API의 WebSocket**을 이용하여 실시간 거래 데이터를 효율적으로 수집하는 Python 기반 시스템입니다.

## 🎯 주요 기능

### 1️⃣ **Ticker (현재가)**
- 실시간 현재가, 시가, 고가, 저가
- 전일 대비 변동률 및 변동가
- 거래량, 누적 거래대금
- 52주 최고/최저가
- 거래 상태 정보

**사용 사례**: 실시간 시세 모니터링, 트레이딩봇, 가격 알림

### 2️⃣ **Trade (체결)**
- 체결 가격 및 거래량
- 매수/매도 구분
- 최우선 호가 정보
- 체결 타임스탬프
- 거래 일련번호

**사용 사례**: 거래량 분석, 시장 심리 파악, 체결 기록

### 3️⃣ **Orderbook (호가)**
- 실시간 매수/매도 호가
- 각 호가 단계별 잔량
- 총 매수/매도 잔량
- 호가 모아보기 (그룹핑)

**사용 사례**: 호가 분석, 유동성 파악, 가격 변동 예측

### 4️⃣ **Candle (캔들)**
- OHLCV (시가, 고가, 저가, 종가, 거래량)
- 다양한 시간 단위 (1초, 1분, 3분, 5분, 10분, 15분, 30분, 60분, 240분)
- 누적 거래량 및 거래대금

**사용 사례**: 기술적 분석, 차트 생성, 트레이딩 전략

---

## 🚀 빠른 시작

### 1. 설치

```bash
# 저장소 클론
cd /home/silver/Desktop/projects/d

# 필요한 패키지 설치
pip install -r requirements.txt
```

### 2. 기본 사용법

```python
import asyncio
from upbit_websocket_client import UpbitWebSocketClient

async def main():
    client = UpbitWebSocketClient()
    
    # WebSocket 연결
    if not await client.connect():
        return
    
    # Ticker(현재가) 구독
    await client.subscribe_ticker(["KRW-BTC", "KRW-ETH"])
    
    # 메시지 수신 (30초)
    try:
        await asyncio.wait_for(
            client.receive_messages(),
            timeout=30
        )
    except asyncio.TimeoutError:
        await client.disconnect()

asyncio.run(main())
```

### 3. 실행 방법

**기본 예시 실행:**
```bash
python examples.py
```

**데이터 수집 및 저장:**
```bash
python data_recorder.py
```

---

## 📁 파일 구조

```
/home/silver/Desktop/projects/d/
├── upbit_websocket_client.py    # 메인 WebSocket 클라이언트
├── examples.py                   # 다양한 사용 예시
├── data_recorder.py              # 데이터 수집 및 CSV 저장
├── requirements.txt              # 필요 패키지
└── README.md                     # 이 파일
```

---

## 📖 상세 사용 예시

### 예시 1: Ticker(현재가) 수신

```python
import asyncio
from upbit_websocket_client import UpbitWebSocketClient

async def main():
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    # BTC, ETH, XRP의 현재가 구독
    await client.subscribe_ticker(["KRW-BTC", "KRW-ETH", "KRW-XRP"])
    
    # 30초간 메시지 수신
    try:
        await asyncio.wait_for(
            client.receive_messages(),
            timeout=30
        )
    except asyncio.TimeoutError:
        await client.disconnect()

asyncio.run(main())
```

**출력 예시:**
```
[14:23:45.123] KRW-BTC | ticker: 97,500,000원 (RISE +2.15%)
[14:23:46.456] KRW-ETH | ticker: 3,500,000원 (FALL -0.50%)
```

---

### 예시 2: Trade(체결) 데이터 수신

```python
async def main():
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    # 체결 데이터 구독
    await client.subscribe_trade(["KRW-BTC", "KRW-ETH"])
    
    try:
        await asyncio.wait_for(
            client.receive_messages(),
            timeout=30
        )
    except asyncio.TimeoutError:
        await client.disconnect()

asyncio.run(main())
```

**출력 예시:**
```
[14:23:50.789] KRW-BTC | trade: 97,500,000원 x 0.00125 (BID)
[14:23:51.234] KRW-BTC | trade: 97,501,000원 x 0.00250 (ASK)
```

---

### 예시 3: Orderbook(호가) 데이터 수신

```python
async def main():
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    # 호가 데이터 구독 (level=100000으로 10만원 단위 그룹핑)
    await client.subscribe_orderbook(["KRW-BTC", "KRW-ETH"], level=100000)
    
    try:
        await asyncio.wait_for(
            client.receive_messages(),
            timeout=30
        )
    except asyncio.TimeoutError:
        await client.disconnect()

asyncio.run(main())
```

---

### 예시 4: Candle(캔들) 데이터 수신

```python
async def main():
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    # 1분봉 캔들 구독
    await client.subscribe_candle(["KRW-BTC", "KRW-ETH"], "1m")
    
    try:
        await asyncio.wait_for(
            client.receive_messages(),
            timeout=30
        )
    except asyncio.TimeoutError:
        await client.disconnect()

asyncio.run(main())
```

**지원하는 캔들 유형:**
- `1s`: 1초봉
- `1m`: 1분봉
- `3m`: 3분봉
- `5m`: 5분봉
- `10m`: 10분봉
- `15m`: 15분봉
- `30m`: 30분봉
- `60m`: 1시간봉
- `240m`: 4시간봉

---

### 예시 5: 커스텀 콜백 함수로 데이터 처리

```python
async def my_callback(data):
    """데이터를 받으면 호출되는 함수"""
    msg_type = data.get("type")
    code = data.get("code")
    
    if msg_type == "ticker":
        price = data.get("tp", 0)
        print(f"{code}: {price:,.0f}원")

async def main():
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    await client.subscribe_ticker(["KRW-BTC", "KRW-ETH"])
    
    # 콜백 함수를 지정하여 메시지 처리
    try:
        await asyncio.wait_for(
            client.receive_messages(callback=my_callback),
            timeout=30
        )
    except asyncio.TimeoutError:
        await client.disconnect()

asyncio.run(main())
```

---

### 예시 6: 데이터를 CSV 파일로 저장

```bash
python data_recorder.py
```

**자동으로 `data/` 디렉토리에 CSV 파일이 생성됩니다:**

```
data/
├── ticker_KRW-BTC.csv
├── ticker_KRW-ETH.csv
├── trade_KRW-BTC.csv
└── orderbook_KRW-BTC.csv
```

**CSV 파일 예시:**
```csv
timestamp,code,price,previous_close,change,change_rate,volume,acc_volume
2024-12-28T14:23:45.123,KRW-BTC,97500000,97000000,500000,0.00515,0.0125,1234.567
```

---

## 🎨 API 클래스 참조

### UpbitWebSocketClient

#### 주요 메서드

##### `async connect()`
WebSocket 연결을 설정합니다.
```python
success = await client.connect()
```

##### `async disconnect()`
WebSocket 연결을 종료합니다.
```python
await client.disconnect()
```

##### `async subscribe_ticker(codes, format="DEFAULT")`
Ticker(현재가) 데이터를 구독합니다.
```python
await client.subscribe_ticker(["KRW-BTC", "KRW-ETH"])
```

##### `async subscribe_trade(codes, format="DEFAULT")`
Trade(체결) 데이터를 구독합니다.
```python
await client.subscribe_trade(["KRW-BTC"])
```

##### `async subscribe_orderbook(codes, level=None)`
Orderbook(호가) 데이터를 구독합니다.
```python
await client.subscribe_orderbook(["KRW-BTC"], level=100000)
```

##### `async subscribe_candle(codes, candle_type="1m")`
Candle(캔들) 데이터를 구독합니다.
```python
await client.subscribe_candle(["KRW-BTC"], "1m")
```

##### `async receive_messages(callback=None)`
메시지를 수신하고 필요시 콜백 함수를 호출합니다.
```python
await client.receive_messages(callback=my_callback)
```

---

## 📊 Ticker 데이터 필드 설명

| 필드 | 영문명 | 설명 |
|------|--------|------|
| code | code | 마켓 코드 (예: KRW-BTC) |
| tp | trade_price | 현재가 |
| op | opening_price | 시가 |
| hp | high_price | 고가 |
| lp | low_price | 저가 |
| pcp | prev_closing_price | 전일 종가 |
| cr | change_rate | 전일 대비 등락율 |
| scp | signed_change_price | 전일 대비 가격 변동값 |
| tv | trade_volume | 최근 거래량 |
| atv | acc_trade_volume | 누적 거래량 |
| atv24h | acc_trade_volume_24h | 24시간 누적 거래량 |
| atp | acc_trade_price | 누적 거래대금 |
| atp24h | acc_trade_price_24h | 24시간 누적 거래대금 |

---

## ⚙️ 고급 설정

### 여러 마켓 동시 구독

```python
codes = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-AVAX"]
await client.subscribe_ticker(codes)
```

### 데이터 필터링

```python
def my_callback(data):
    # BTC 데이터만 처리
    if data.get("code") == "KRW-BTC":
        print(f"BTC 현재가: {data.get('tp'):,.0f}원")

await client.receive_messages(callback=my_callback)
```

---

## 🐛 트러블슈팅

### 연결 오류
```
❌ WebSocket 연결 실패
```

**해결 방법:**
1. 인터넷 연결 확인
2. 업비트 서버 상태 확인 (https://status.upbit.com)
3. 방화벽 설정 확인

### 타임아웃
- `timeout` 값을 증가시키세요
- 안정적인 네트워크 환경 확인

---

## 📈 실제 사용 사례

### 1️⃣ 실시간 가격 모니터링 봇
```python
while True:
    await client.subscribe_ticker(["KRW-BTC"])
    if price < threshold:
        alert_user()
```

### 2️⃣ 거래량 분석
```python
ticker_data = []
await client.receive_messages(
    callback=lambda d: ticker_data.append(d)
)
analyze_volume(ticker_data)
```

### 3️⃣ 실시간 차트 생성
```python
await client.subscribe_candle(["KRW-BTC"], "1m")
# 수신한 데이터로 차트 업데이트
```

---

## 📝 주의사항

1. **Rate Limit**: 과도한 요청은 제한될 수 있습니다
2. **데이터 정확성**: 네트워크 지연으로 데이터 손실 가능
3. **리소스**: 장시간 실행 시 메모리 사용량 모니터링

---

## 🔗 참고 자료

- [업비트 API 문서](https://docs.upbit.com)
- [WebSocket 공식 문서](https://docs.upbit.com/kr/reference/websocket-guide)
- [Python asyncio 문서](https://docs.python.org/3/library/asyncio.html)

---

**마지막 업데이트**: 2024년 12월 28일
