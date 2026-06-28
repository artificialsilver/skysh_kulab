# Phase 0 공통 계약서

이 문서는 백엔드 3명이 병렬 개발을 시작하기 전에 반드시 같이 고정해야 하는 공통 계약이다.

Phase 0의 목적은 구현을 시작하기 전에 다음 항목을 명확히 맞추는 것이다.

- 데이터 타입
- Redis key/field
- DB schema
- Indicator/Persona enum
- API response schema
- 시간 기준
- 지정 마켓

시간 기준은 **내부 저장과 계산은 UTC**, **사용자 화면 표시는 KST(Asia/Seoul)** 로 고정한다.

## 1. 전체 데이터 흐름

```text
Upbit WebSocket
→ Redis 1분 MinuteBucket
→ 15m / 4h IndicatorSnapshot
→ 15m / 4h PersonaSnapshot
→ DB 저장
→ API / Optional Alert
```

원본 tick 데이터는 DB에 저장하지 않는다.

Redis는 실시간 1분 압축 계층이고, DB는 15m/4h 단위 지표와 Persona snapshot 저장소다.

v1 분석 timeframe은 `15m`, `4h`만 지원한다.

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
- whale/retail 분류 기준은 `market + timeframe`별 threshold를 따른다.
- 실시간 `TradeEvent` 분류에는 기본 `whale_threshold_krw`를 적용하고, snapshot 계산 시 timeframe별 threshold로 재계산할 수 있다.

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

`MinuteBucket`을 timeframe 기준으로 집계해 만든 지표다. 15m는 최근 15개의 1분 bucket, 4h는 최근 240개의 1분 bucket을 기준으로 계산한다.

```json
{
  "market": "KRW-BTC",
  "timeframe": "15m",
  "window_start": "2026-06-28T05:15:00Z",
  "window_end": "2026-06-28T05:30:00Z",
  "snapshot_at": "2026-06-28T05:30:00Z",
  "price_open": 97000000.0,
  "price_high": 99000000.0,
  "price_low": 96900000.0,
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
  "whale_net_ratio": 0.1944,
  "retail_net_ratio": 0.1111,
  "divergence_score": 0.0,
  "trade_count": 18420,
  "whale_count": 211,
  "retail_count": 18209,
  "metrics_json": {
    "threshold_version": "v1-temp"
  }
}
```

고정 규칙:

- `timeframe`은 `15m` 또는 `4h`다.
- `window_start`, `window_end`, `snapshot_at`은 UTC ISO 8601 문자열이다.
- `snapshot_at`은 기본적으로 `window_end`와 같다.
- OHLC는 `price_open`, `price_high`, `price_low`, `price_close`로 저장한다.
- DB에는 계산 지표를 생략하지 않고 저장한다.

### PersonaSnapshot

`IndicatorSnapshot` 기반으로 도출한 시장 성격 snapshot이다.

```json
{
  "market": "KRW-BTC",
  "timeframe": "15m",
  "snapshot_at": "2026-06-28T05:30:00Z",
  "persona": "breakout",
  "confidence": 0.82,
  "reason_codes": ["volume_surge", "price_breakout", "whale_buy"],
  "metrics_json": {
    "price_change_pct": 1.55,
    "volume_surge_ratio": 1.8,
    "whale_net_ratio": 0.1944
  }
}
```

고정 규칙:

- 15m와 4h 모두 같은 Persona enum을 사용한다.
- Persona 판별 입력은 항상 `IndicatorSnapshot`이다.
- 임계값은 `market + timeframe`별로 다르게 적용한다.
- 15m Persona는 항상 계산하고 저장한다.
- 15m 알림은 사용자가 알림을 켠 경우에만 발송 대상이 된다.

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
- bucket TTL은 최소 5시간 이상으로 둔다.
- Redis에는 원본 tick을 저장하지 않는다.

## 5. Threshold 설정

코인별·timeframe별 임계값을 둔다.

```json
{
  "KRW-BTC": {
    "15m": {
      "whale_threshold_krw": 10000000,
      "volume_surge_ratio": 1.8,
      "volatility_pct": 1.2
    },
    "4h": {
      "whale_threshold_krw": 10000000,
      "volume_surge_ratio": 1.4,
      "volatility_pct": 3.5
    }
  }
}
```

고정 규칙:

- 위 숫자는 임시값이다.
- 실제 구현 시 설정 파일 또는 상수로 분리한다.
- `KRW-BTC`, `KRW-ETH`, `KRW-XRP`는 각각 별도 threshold를 가진다.
- 같은 Persona enum을 쓰더라도 threshold는 `market + timeframe` 기준으로 적용한다.

## 6. DB Schema

### market_indicator_snapshots

컬럼:

```text
id
market
timeframe
snapshot_at
window_start
window_end
price_open
price_high
price_low
price_close
price_change_pct
volatility_pct
total_volume_krw
volume_surge_ratio
whale_buy_krw
whale_sell_krw
retail_buy_krw
retail_sell_krw
whale_net_krw
retail_net_krw
whale_net_ratio
retail_net_ratio
divergence_score
trade_count
whale_count
retail_count
metrics_json
created_at
updated_at
```

고정 규칙:

- `snapshot_at`은 UTC 기준 timeframe 경계 시각이다.
- `(market, timeframe, snapshot_at)`은 unique 처리한다.
- 같은 `market + timeframe + snapshot_at` 재실행 시 insert가 아니라 upsert한다.
- IndicatorSnapshot에는 persona, persona_name, confidence, insight를 저장하지 않는다.

### market_persona_snapshots

컬럼:

```text
id
market
timeframe
snapshot_at
persona
confidence
reason_codes
metrics_json
created_at
updated_at
```

고정 규칙:

- `(market, timeframe, snapshot_at)`은 unique 처리한다.
- PersonaSnapshot은 같은 시각의 IndicatorSnapshot을 기준으로 도출한다.
- 15m와 4h 모두 저장 대상이다.

### market_alert_settings

컬럼:

```text
id
market
timeframe
enabled
created_at
updated_at
```

고정 규칙:

- v1 알림 설정 대상 timeframe은 `15m`다.
- 15m Persona 계산과 저장은 알림 설정과 무관하게 항상 수행한다.
- 알림 발송 대상 판별에서만 `enabled`를 적용한다.

## 7. Persona Enum

내부 enum은 영어 key로 고정한다.

```text
accumulation
breakout
distribution_trap
panic_sell
retail_chop
sleep
```

위험 Persona:

```text
distribution_trap
panic_sell
```

판별 기준:

- Persona 판별은 `IndicatorSnapshot` 기반으로 통일한다.
- 15m는 단기 강도 중심으로 계산한다.
- 4h는 빈도수·지속성 중심으로 계산해 단일 1분 bucket 급등락에 과하게 흔들리지 않도록 한다.
- 같은 enum을 사용하되, threshold와 계산 가중치는 `market + timeframe`별로 다르게 적용한다.

## 8. API Response Schema

### GET /api/markets

```json
{
  "markets": ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
}
```

### GET /api/market/{market}/snapshots?timeframe=15m

```json
{
  "market": "KRW-BTC",
  "timeframe": "15m",
  "snapshots": [
    {
      "snapshot_at": "2026-06-28T05:30:00Z",
      "window_start": "2026-06-28T05:15:00Z",
      "window_end": "2026-06-28T05:30:00Z",
      "price_open": 97000000.0,
      "price_high": 99000000.0,
      "price_low": 96900000.0,
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
      "whale_net_ratio": 0.1944,
      "retail_net_ratio": 0.1111,
      "divergence_score": 0.0,
      "trade_count": 18420,
      "whale_count": 211,
      "retail_count": 18209,
      "metrics_json": {
        "threshold_version": "v1-temp"
      }
    }
  ]
}
```

### GET /api/market/{market}/snapshots?timeframe=4h

응답 shape은 15m snapshot과 동일하며 `timeframe`만 `4h`로 내려준다.

### GET /api/market/{market}/persona?timeframe=15m

```json
{
  "market": "KRW-BTC",
  "timeframe": "15m",
  "snapshot_at": "2026-06-28T05:30:00Z",
  "persona": "breakout",
  "confidence": 0.82,
  "reason_codes": ["volume_surge", "price_breakout", "whale_buy"],
  "metrics_json": {
    "price_change_pct": 1.55,
    "volume_surge_ratio": 1.8,
    "whale_net_ratio": 0.1944
  }
}
```

### GET /api/market/{market}/persona?timeframe=4h

응답 shape은 15m PersonaSnapshot과 동일하며 `timeframe`만 `4h`로 내려준다.

### GET /api/market/{market}/alerts/settings

```json
{
  "market": "KRW-BTC",
  "timeframe": "15m",
  "enabled": true
}
```

### PUT /api/market/{market}/alerts/settings

요청:

```json
{
  "timeframe": "15m",
  "enabled": false
}
```

응답:

```json
{
  "market": "KRW-BTC",
  "timeframe": "15m",
  "enabled": false
}
```

응답 고정 규칙:

- 시간 필드는 ISO 8601 UTC 문자열로 내려준다.
- 금액은 KRW 숫자로 내려준다.
- `/snapshots` 응답에는 persona를 포함하지 않는다.
- `/persona` 응답은 PersonaSnapshot을 반환한다.
- `timeframe`은 v1에서 `15m` 또는 `4h`만 허용한다.

## 9. 시간 기준

시간 기준은 다음으로 고정한다.

```text
내부 저장: UTC
Redis key: UTC
DB timestamp: UTC
API timestamp: UTC ISO 8601
사용자 화면 표시: KST(Asia/Seoul)
```

이유:

- 서버와 DB의 시간 기준을 UTC로 통일하면 배포 환경이 바뀌어도 계산이 흔들리지 않는다.
- 한국 사용자에게 보여주는 화면만 KST로 변환하면 된다.
- 15m와 4h 계산은 모두 UTC timestamp 기준으로 수행한다.

## 10. Test Plan

- BTC/ETH/XRP별 threshold가 따로 적용되는지 확인한다.
- 15m와 4h가 같은 Persona enum을 쓰되 다른 계산/임계값을 적용하는지 확인한다.
- 15m Persona가 계산되어도 알림 off면 알림되지 않는지 확인한다.
- 4h Persona가 단일 1분 bucket 급등락 하나에 과하게 흔들리지 않는지 확인한다.
- DB에 IndicatorSnapshot의 지표 필드가 누락 없이 저장되는지 확인한다.

## 11. Phase 0 완료 기준

Phase 0는 아래 항목이 합의되면 완료로 본다.

- 위 데이터 타입 이름과 필드명을 그대로 사용한다.
- Redis key/field 이름을 그대로 사용한다.
- DB 테이블명과 컬럼명을 그대로 사용한다.
- IndicatorSnapshot에는 `timeframe`을 포함한다.
- DB unique 기준은 `(market, timeframe, snapshot_at)`으로 고정한다.
- IndicatorSnapshot 지표 필드는 DB에 누락 없이 저장한다.
- PersonaSnapshot은 IndicatorSnapshot 기반으로 도출한다.
- 15m와 4h Persona는 같은 enum을 사용한다.
- API 응답은 timeframe 중심 JSON 형태를 기준으로 구현한다.
- 내부 시간은 UTC, 사용자 표시는 KST로 고정한다.
- 지정 마켓은 `KRW-BTC`, `KRW-ETH`, `KRW-XRP` 세 개로 고정한다.
