# Phase 0 공통 계약서

이 문서는 백엔드 3명이 병렬로 개발하기 전에 맞춰야 할 공통 계약을 고정한다.

목표 흐름은 다음과 같다.

```text
Upbit WebSocket
→ TradeEvent
→ Redis 1분 MinuteBucket
→ 15분 IndicatorSnapshot
→ PersonaSnapshot
→ DB MarketSnapshot
→ 12/24시간 MarketReport API
```

프론트엔드는 이번 분업 범위에서 제외한다.

## 1. 백엔드 3인 분업 기준

### 1번 담당자: 실시간 수집 / Redis 적재

담당 범위:

```text
Data Ingestion
Upbit WebSocket
Redis 1분 버킷
```

주요 역할:

- 업비트 WebSocket 연결
- 지정 마켓 구독
- 원본 trade 메시지 파싱
- 내부 표준 `TradeEvent` 생성
- 체결금액 계산
- whale/retail 분류
- Redis 1분 버킷 누적
- WebSocket 재연결 처리
- Redis bucket TTL 설정

산출물:

```text
업비트 실시간 체결 → Redis 1분 MinuteBucket
```

독립 개발 방법:

```text
fake TradeEvent를 넣었을 때 Redis bucket이 정확히 쌓이는지 테스트한다.
```

### 2번 담당자: 15분 지표 / Persona 판별

담당 범위:

```text
Indicator Engine
Personality Engine
Insight 생성
```

주요 역할:

- Redis에서 최근 15개의 1분 버킷 조회
- 15분 가격 변화율 계산
- 15분 변동성 계산
- 거래량 급증도 계산
- whale net flow 계산
- retail net flow 계산
- 수급 다이버전스 계산
- Persona 룰 구현
- 짧은 insight 문장 생성

산출물:

```text
Redis 15분 버킷 → 시장 지표 → PersonaSnapshot + insight
```

독립 개발 방법:

```text
fixture MinuteBucket 15개를 넣고 Persona가 기대값으로 나오는지 테스트한다.
```

### 3번 담당자: DB 저장 / 12·24시간 리포트 / API

담당 범위:

```text
Snapshot Storage
Report Engine
FastAPI 조회 API
```

주요 역할:

- 2번 담당자의 `PersonaSnapshot`과 `IndicatorSnapshot`을 15분마다 DB에 저장
- `market_snapshots` 테이블 설계
- 최근 12시간 snapshot 48개 조회
- 최근 24시간 snapshot 96개 조회
- 사용자용 리포트 생성
- FastAPI 조회 API 제공

산출물:

```text
15분 MarketSnapshot 저장
DB snapshot 기반 12/24시간 MarketReport API
```

독립 개발 방법:

```text
fake MarketSnapshot 48개/96개를 DB에 넣고 report 결과를 테스트한다.
```

## 2. 공통 데이터 타입

### TradeEvent

업비트 WebSocket 원본 메시지를 내부 표준 형태로 변환한 단위다.

```json
{
  "market": "KRW-BTC",
  "trade_ts": "2026-06-28T05:30:12.123Z",
  "price": 98500000.0,
  "volume": 0.12,
  "amount_krw": 11820000.0,
  "side": "buy",
  "actor": "whale"
}
```

고정 규칙:

- `amount_krw = price * volume`
- `side`는 `buy` 또는 `sell`만 허용한다.
- `actor`는 `whale` 또는 `retail`만 허용한다.
- `amount_krw >= WHALE_THRESHOLD_KRW`이면 `whale`이다.
- 기본 `WHALE_THRESHOLD_KRW`는 `10000000`이다.

### MinuteBucket

Redis 1분 버킷의 논리 모델이다.

```json
{
  "market": "KRW-BTC",
  "bucket_minute": "2026-06-28T05:30:00Z",
  "open": 98400000.0,
  "high": 98700000.0,
  "low": 98350000.0,
  "close": 98500000.0,
  "total_volume_krw": 530000000.0,
  "whale_buy_krw": 210000000.0,
  "whale_sell_krw": 90000000.0,
  "retail_buy_krw": 150000000.0,
  "retail_sell_krw": 80000000.0,
  "trade_count": 1520,
  "whale_count": 18,
  "retail_count": 1502
}
```

### IndicatorSnapshot

최근 15분의 `MinuteBucket` 15개를 합산하고 계산한 숫자 지표다.

```json
{
  "market": "KRW-BTC",
  "window_start": "2026-06-28T05:15:00Z",
  "window_end": "2026-06-28T05:30:00Z",
  "price_open": 97000000.0,
  "price_close": 98500000.0,
  "price_change_pct": 1.55,
  "volatility_pct": 2.1,
  "total_volume_krw": 7200000000.0,
  "volume_surge_ratio": 1.8,
  "whale_buy_krw": 2600000000.0,
  "whale_sell_krw": 1200000000.0,
  "retail_buy_krw": 2100000000.0,
  "retail_sell_krw": 1300000000.0,
  "whale_net_krw": 1400000000.0,
  "retail_net_krw": 800000000.0,
  "divergence_score": 0.0
}
```

### PersonaSnapshot

`IndicatorSnapshot`을 해석한 시장 성격 결과다.

```json
{
  "market": "KRW-BTC",
  "evaluated_at": "2026-06-28T05:30:00Z",
  "persona": "breakout",
  "persona_name": "폭주 기관차",
  "confidence": 0.82,
  "insight": "최근 15분간 고래와 개미 매수세가 동시에 강해졌고 가격 변동성이 확대되었습니다."
}
```

### MarketSnapshot

DB에 15분마다 저장되는 최종 스냅샷이다.

```json
{
  "market": "KRW-BTC",
  "snapshot_at": "2026-06-28T05:30:00Z",
  "persona": "breakout",
  "persona_name": "폭주 기관차",
  "confidence": 0.82,
  "price_open": 97000000.0,
  "price_close": 98500000.0,
  "price_change_pct": 1.55,
  "volatility_pct": 2.1,
  "total_volume_krw": 7200000000.0,
  "volume_surge_ratio": 1.8,
  "whale_net_krw": 1400000000.0,
  "retail_net_krw": 800000000.0,
  "divergence_score": 0.0,
  "insight": "최근 15분간 고래와 개미 매수세가 동시에 강해졌고 가격 변동성이 확대되었습니다."
}
```

### MarketReport

DB에 저장된 15분 `MarketSnapshot`을 12시간 또는 24시간 단위로 요약한 사용자 리포트다.

```json
{
  "market": "KRW-BTC",
  "hours": 24,
  "report_start": "2026-06-27T05:30:00Z",
  "report_end": "2026-06-28T05:30:00Z",
  "dominant_persona": "distribution_trap",
  "dominant_persona_name": "교활한 낚시꾼",
  "persona_change_count": 9,
  "snapshot_count": 96,
  "price_change_pct": 3.2,
  "total_volume_krw": 420000000000.0,
  "whale_net_krw": -1240000000.0,
  "retail_net_krw": 2100000000.0,
  "risk_count": 14,
  "summary": "최근 24시간 동안 가격은 상승했지만 고래 순매도와 개미 매수 유입이 반복되었습니다."
}
```

## 3. Redis 계약

Redis key:

```text
bucket:{market}:{yyyyMMddHHmm}
```

예시:

```text
bucket:KRW-BTC:202606280530
```

Redis Hash fields:

```text
open
high
low
close
total_volume_krw
whale_buy_krw
whale_sell_krw
retail_buy_krw
retail_sell_krw
trade_count
whale_count
retail_count
```

고정 규칙:

- key의 시간은 UTC minute 기준이다.
- 금액 필드는 KRW 기준 float이다.
- count 필드는 integer다.
- bucket TTL은 기본 2시간이다.
- 원본 tick은 Redis나 DB에 저장하지 않는다.

## 4. DB 계약

테이블명:

```text
market_snapshots
```

컬럼:

```text
id
market
snapshot_at
persona
persona_name
confidence
price_open
price_close
price_change_pct
volatility_pct
total_volume_krw
volume_surge_ratio
whale_net_krw
retail_net_krw
divergence_score
insight
created_at
```

고정 규칙:

- `snapshot_at`은 15분 경계 시각이다.
- `(market, snapshot_at)`은 unique 처리한다.
- 12시간 리포트는 최근 48개 snapshot 기준이다.
- 24시간 리포트는 최근 96개 snapshot 기준이다.
- 같은 `market + snapshot_at` 재실행 시 중복 insert가 아니라 upsert한다.

## 5. Persona Enum

내부 enum은 영어 key로 고정한다.

```text
accumulation
breakout
distribution_trap
panic_sell
retail_chop
sleep
```

화면/리포트용 한글 이름:

```text
accumulation       → 심해의 진공청소기
breakout           → 폭주 기관차
distribution_trap  → 교활한 낚시꾼
panic_sell         → 무자비한 불도저
retail_chop        → 시끄러운 시장통
sleep              → 겨울잠 자는 곰
```

위험 Persona 기본 분류:

```text
distribution_trap
panic_sell
```

## 6. API 계약

3번 담당자가 제공할 백엔드 조회 API다.

```text
GET /api/markets
GET /api/market/{market}/snapshots?hours=12
GET /api/market/{market}/snapshots?hours=24
GET /api/market/{market}/report?hours=12
GET /api/market/{market}/report?hours=24
```

추후 실시간 확인용 API:

```text
GET /api/market/{market}/live
```

응답 원칙:

- 시간 필드는 ISO 8601 UTC 문자열로 내려준다.
- 금액은 KRW 숫자로 내려준다.
- persona는 영어 enum과 한글 표시명을 같이 내려준다.
- `hours`는 v1에서 12 또는 24만 허용한다.

## 7. 구현 순서

### Phase 0: 공통 계약 고정

세 명이 이 문서를 기준으로 타입, Redis field, DB schema, API shape를 맞춘다.

### Phase 1: 병렬 개발

각자 mock 데이터로 독립 개발한다.

```text
1번: fake TradeEvent → Redis MinuteBucket
2번: fake MinuteBucket 15개 → IndicatorSnapshot / PersonaSnapshot
3번: fake MarketSnapshot 48개/96개 → MarketReport API
```

### Phase 2: 1번 + 2번 연결

Redis를 기준으로 수집 계층과 판단 계층을 붙인다.

```text
Upbit/fake trade
→ Redis 1분 버킷
→ 최근 15분 지표 계산
→ PersonaSnapshot
```

### Phase 3: 2번 + 3번 연결

Persona와 지표 결과를 DB에 저장한다.

```text
IndicatorSnapshot + PersonaSnapshot
→ MarketSnapshot DB upsert
→ 12/24시간 MarketReport
```

### Phase 4: 전체 통합

최종 파이프라인을 검증한다.

```text
Upbit WebSocket
→ Redis 1분 버킷
→ 15분 Indicator
→ Persona
→ DB Snapshot
→ Report API
```

## 8. 담당자별 의존 계약

1번 담당자:

- 입력: Upbit WebSocket 메시지
- 출력: Redis `MinuteBucket`
- 반드시 지킬 것: Redis key/field 이름

2번 담당자:

- 입력: Redis `MinuteBucket` 최근 15개
- 출력: `IndicatorSnapshot`, `PersonaSnapshot`
- 반드시 지킬 것: Persona enum, 지표 필드명

3번 담당자:

- 입력: `PersonaSnapshot` + `IndicatorSnapshot`
- 출력: DB `MarketSnapshot`, API `MarketReport`
- 반드시 지킬 것: DB schema, API response shape

## 9. 공통 가정

- 내부 저장 시간은 UTC로 통일한다.
- 사용자용 문구와 화면 표시는 KST로 변환한다.
- Whale 기준은 v1에서 1,000만 원으로 시작한다.
- 15분 snapshot은 매 15분 경계마다 저장한다.
- Redis 1분 버킷은 실시간 계산용이며 영구 저장소가 아니다.
- DB는 15분 snapshot과 12/24시간 report의 근거 데이터다.
