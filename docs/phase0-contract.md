# Phase 0 공통 계약서

이 문서는 백엔드 3명이 병렬 개발을 시작하기 전에 반드시 같이 고정해야 하는 공통 계약이다.

Phase 0의 목적은 구현을 시작하기 전에 다음 항목을 명확히 맞추는 것이다.

- 데이터 타입
- Redis key/field
- DB schema
- Persona enum
- API response schema
- 시간 기준
- 지정 마켓

시간 기준은 **내부 저장과 계산은 UTC**, **사용자 화면과 리포트 표시는 KST(Asia/Seoul)** 로 고정한다.

## 1. 전체 데이터 흐름

```text
Upbit WebSocket
→ TradeEvent
→ Redis 1분 MinuteBucket
→ 15분 IndicatorSnapshot
→ DB IndicatorSnapshot
→ 12/24시간 Persona + MarketReport API
```

원본 tick 데이터는 DB에 저장하지 않는다.

Redis는 실시간 1분 압축 계층이고, DB는 15분 단위 지표 snapshot 저장소다.

## 2. 지정 마켓

v1에서 수집하고 분석하는 지정 마켓은 아래 3개로 고정한다.

```text
KRW-BTC
KRW-ETH
KRW-XRP
```

`GET /api/markets`는 위 3개 마켓만 반환한다.

## 3. 데이터 타입

### TradeEvent

업비트 WebSocket 체결 메시지를 내부 표준 형태로 변환한 단위다.

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
- `side`는 `buy` 또는 `sell`
- `actor`는 `whale` 또는 `retail`
- `amount_krw >= 10000000`이면 `whale`
- `amount_krw < 10000000`이면 `retail`

### MinuteBucket

Redis에 저장되는 1분 단위 압축 데이터다.

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

최근 15개의 `MinuteBucket`을 합산해 만든 15분 지표다.

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

### IndicatorSnapshot 저장 모델

DB에 15분마다 저장하는 지표 스냅샷이다.

```json
{
  "market": "KRW-BTC",
  "snapshot_at": "2026-06-28T05:30:00Z",
  "price_open": 97000000.0,
  "price_close": 98500000.0,
  "price_change_pct": 1.55,
  "volatility_pct": 2.1,
  "total_volume_krw": 7200000000.0,
  "volume_surge_ratio": 1.8,
  "whale_net_krw": 1400000000.0,
  "retail_net_krw": 800000000.0,
  "divergence_score": 0.0
}
```

### MarketReport

DB에 저장된 15분 `IndicatorSnapshot`을 12시간 또는 24시간 단위로 요약하고, 이때 시장 성격을 도출한 사용자 리포트다.

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
  "confidence": 0.82,
  "summary": "최근 24시간 동안 가격은 상승했지만 고래 순매도와 개미 매수 유입이 반복되었습니다."
}
```

## 4. Redis Key / Field

Redis key 형식:

```text
bucket:{market}:{yyyyMMddHHmm}
```

예시:

```text
bucket:KRW-BTC:202606280530
```

Redis Hash field:

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
- Redis에는 원본 tick을 저장하지 않는다.

## 5. DB Schema

테이블명:

```text
market_indicator_snapshots
```

컬럼:

```text
id
market
snapshot_at
price_open
price_close
price_change_pct
volatility_pct
total_volume_krw
volume_surge_ratio
whale_net_krw
retail_net_krw
divergence_score
created_at
```

고정 규칙:

- `snapshot_at`은 UTC 기준 15분 경계 시각이다.
- `(market, snapshot_at)`은 unique 처리한다.
- 같은 `market + snapshot_at` 재실행 시 insert가 아니라 upsert한다.
- 12시간 리포트는 최근 48개 snapshot 기준이다.
- 24시간 리포트는 최근 96개 snapshot 기준이다.
- 15분 snapshot에는 persona, persona_name, confidence, insight를 저장하지 않는다.

## 6. Persona Enum

Persona는 15분마다 도출하지 않고, 12/24시간 리포트 생성 시점에만 도출한다.

내부 enum은 영어 key로 고정한다.

```text
accumulation
breakout
distribution_trap
panic_sell
retail_chop
sleep
```

한글 표시명:

```text
accumulation       → 심해의 진공청소기
breakout           → 폭주 기관차
distribution_trap  → 교활한 낚시꾼
panic_sell         → 무자비한 불도저
retail_chop        → 시끄러운 시장통
sleep              → 겨울잠 자는 곰
```

위험 Persona:

```text
distribution_trap
panic_sell
```

## 7. API Response Schema

### GET /api/markets

```json
{
  "markets": ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
}
```

### GET /api/market/{market}/snapshots?hours=12

```json
{
  "market": "KRW-BTC",
  "hours": 12,
  "snapshots": [
    {
      "snapshot_at": "2026-06-28T05:30:00Z",
      "price_change_pct": 1.55,
      "volatility_pct": 2.1,
      "whale_net_krw": 1400000000.0,
      "retail_net_krw": 800000000.0,
      "divergence_score": 0.0
    }
  ]
}
```

### GET /api/market/{market}/report?hours=24

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
  "confidence": 0.82,
  "summary": "최근 24시간 동안 가격은 상승했지만 고래 순매도와 개미 매수 유입이 반복되었습니다."
}
```

응답 고정 규칙:

- 시간 필드는 ISO 8601 UTC 문자열로 내려준다.
- 금액은 KRW 숫자로 내려준다.
- `/snapshots` 응답에는 persona를 포함하지 않는다.
- `/report` 응답에는 12/24시간 단위로 도출한 persona 영어 enum과 한글 표시명을 같이 내려준다.
- `hours`는 v1에서 12 또는 24만 허용한다.

## 8. 시간 기준

시간 기준은 다음으로 고정한다.

```text
내부 저장: UTC
Redis key: UTC
DB timestamp: UTC
API timestamp: UTC ISO 8601
사용자 화면 표시: KST(Asia/Seoul)
사용자 리포트 문구: KST(Asia/Seoul)
```

이유:

- 서버와 DB의 시간 기준을 UTC로 통일하면 배포 환경이 바뀌어도 계산이 흔들리지 않는다.
- 한국 사용자에게 보여주는 화면과 문구만 KST로 변환하면 된다.
- 15분 경계, 12시간, 24시간 계산은 모두 UTC timestamp 기준으로 수행한다.

## 9. Phase 0 완료 기준

Phase 0는 아래 항목이 합의되면 완료로 본다.

- 위 데이터 타입 이름과 필드명을 그대로 사용한다.
- Redis key/field 이름을 그대로 사용한다.
- DB 테이블명과 컬럼명을 그대로 사용한다.
- 15분 snapshot에는 persona를 저장하지 않는다.
- Persona enum은 12/24시간 report의 내부 표준으로 사용한다.
- API 응답은 위 JSON 형태를 기준으로 구현한다.
- 내부 시간은 UTC, 사용자 표시는 KST로 고정한다.
- 지정 마켓은 `KRW-BTC`, `KRW-ETH`, `KRW-XRP` 세 개로 고정한다.
