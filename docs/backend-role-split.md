# 백엔드 3인 역할 분담 및 구현 순서

이 문서는 프론트엔드를 제외하고 백엔드 3명이 병렬로 개발할 때의 역할 분담과 통합 순서를 정리한다.

전체 목표 흐름은 다음과 같다.

```text
Upbit WebSocket
→ Redis 1분 MinuteBucket
→ 15분 IndicatorSnapshot
→ DB IndicatorSnapshot
→ 12/24시간 Persona + MarketReport API
```

## 1. 역할 분담

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

의존 계약:

- 입력: Upbit WebSocket 메시지
- 출력: Redis `MinuteBucket`
- 반드시 지킬 것: Redis key/field 이름

### 2번 담당자: 15분 지표 계산

담당 범위:

```text
Indicator Engine
15분 IndicatorSnapshot 생성
```

주요 역할:

- Redis에서 최근 15개의 1분 버킷 조회
- 15분 가격 변화율 계산
- 15분 변동성 계산
- 거래량 급증도 계산
- whale net flow 계산
- retail net flow 계산
- 수급 다이버전스 계산

산출물:

```text
Redis 15분 버킷 → IndicatorSnapshot
```

독립 개발 방법:

```text
fixture MinuteBucket 15개를 넣고 IndicatorSnapshot이 기대값으로 나오는지 테스트한다.
```

의존 계약:

- 입력: Redis `MinuteBucket` 최근 15개
- 출력: `IndicatorSnapshot`
- 반드시 지킬 것: 지표 필드명, 15분 window 기준

### 3번 담당자: DB 저장 / 12·24시간 Persona·리포트 / API

담당 범위:

```text
Snapshot Storage
Personality Engine
Report Engine
FastAPI 조회 API
```

주요 역할:

- 2번 담당자의 `IndicatorSnapshot`을 15분마다 DB에 저장
- `market_indicator_snapshots` 테이블 설계
- 최근 12시간 indicator snapshot 48개 조회
- 최근 24시간 indicator snapshot 96개 조회
- 12/24시간 단위 Persona 룰 구현
- 사용자용 리포트 생성
- FastAPI 조회 API 제공

산출물:

```text
15분 IndicatorSnapshot 저장
DB indicator snapshot 기반 12/24시간 Persona + MarketReport API
```

독립 개발 방법:

```text
fake IndicatorSnapshot 48개/96개를 DB에 넣고 Persona와 report 결과를 테스트한다.
```

의존 계약:

- 입력: `IndicatorSnapshot`
- 출력: DB 저장 IndicatorSnapshot, API `MarketReport`
- 반드시 지킬 것: DB schema, API response shape

## 2. 구현 순서

### Phase 0: 공통 계약 고정

세 명이 먼저 같이 고정한다.

- 데이터 타입
- Redis key/field
- DB schema
- Persona enum
- API response schema
- 시간 기준
- 지정 마켓

시간 기준은 내부 저장과 계산은 UTC, 사용자 표시와 리포트 문구는 KST(Asia/Seoul)로 고정한다.

지정 마켓은 `KRW-BTC`, `KRW-ETH`, `KRW-XRP` 세 개로 고정한다.

자세한 공통 계약은 [`phase0-contract.md`](./phase0-contract.md)를 기준으로 한다.

### Phase 1: 병렬 개발

각자 mock 데이터로 독립 개발한다.

```text
1번: fake TradeEvent → Redis MinuteBucket
2번: fake MinuteBucket 15개 → IndicatorSnapshot
3번: fake IndicatorSnapshot 48개/96개 → Persona + MarketReport API
```

이 단계에서는 실제 업비트 연결, 실제 Redis 데이터, 실제 DB 데이터가 모두 완성되어 있지 않아도 된다.

목표는 각 모듈이 독립 입력값으로 자기 책임을 끝까지 처리하는 것이다.

### Phase 2: 1번 + 2번 연결

Redis를 기준으로 수집 계층과 판단 계층을 붙인다.

```text
Upbit/fake trade
→ Redis 1분 버킷
→ 최근 15분 지표 계산
→ IndicatorSnapshot
```

검증할 것:

- Redis bucket 값이 정확히 누적되는지 확인한다.
- 최근 15개 bucket 조회가 정확한지 확인한다.
- 비어 있는 분이 있어도 엔진이 깨지지 않는지 확인한다.
- 15분 IndicatorSnapshot에 persona 정보가 섞이지 않는지 확인한다.

### Phase 3: 2번 + 3번 연결

15분 지표 결과를 DB에 저장하고, DB 지표 snapshot 기반으로 12/24시간 Persona와 리포트를 만든다.

```text
IndicatorSnapshot
→ IndicatorSnapshot DB upsert
→ 12/24시간 Persona 도출
→ 12/24시간 MarketReport
```

검증할 것:

- 15분 경계 시각 기준으로 snapshot이 저장되는지 확인한다.
- 같은 `market + snapshot_at` 재실행 시 중복 insert가 아니라 upsert 되는지 확인한다.
- 12시간 리포트가 최근 48개 snapshot 기준으로 만들어지는지 확인한다.
- 24시간 리포트가 최근 96개 snapshot 기준으로 만들어지는지 확인한다.
- Persona가 15분마다 저장되지 않고 12/24시간 리포트 생성 시점에만 도출되는지 확인한다.

### Phase 4: 전체 통합

최종 파이프라인을 검증한다.

```text
Upbit WebSocket
→ Redis 1분 버킷
→ 15분 Indicator
→ DB IndicatorSnapshot
→ 12/24시간 Persona + Report API
```

검증할 것:

- WebSocket 연결이 장시간 유지되는지 확인한다.
- Redis 1분 버킷이 지속적으로 쌓이고 TTL로 정리되는지 확인한다.
- 15분마다 DB indicator snapshot이 저장되는지 확인한다.
- 12/24시간 Persona와 리포트가 DB indicator snapshot 기준으로 생성되는지 확인한다.
- API 응답이 Phase 0 계약과 맞는지 확인한다.

## 3. 독립 개발 가능 범위

완전히 독립적으로 먼저 개발 가능한 작업:

- Upbit trade message parser
- fake `TradeEvent` 기반 Redis bucket writer
- fixture `MinuteBucket` 기반 indicator engine
- fake `IndicatorSnapshot` 기반 persona rule engine
- fake `IndicatorSnapshot` 기반 report engine
- FastAPI 조회 API response schema

서로 의존하는 작업:

- 15분 indicator는 Redis bucket schema에 의존한다.
- DB 저장은 `IndicatorSnapshot`에 의존한다.
- Persona engine은 DB에 저장된 indicator field와 Persona enum에 의존한다.
- Report API는 DB indicator snapshot schema에 의존한다.

## 4. 완료 기준

역할 분담 기준 완료 상태:

- 1번 담당자는 fake 또는 실제 체결을 Redis 1분 bucket으로 적재할 수 있다.
- 2번 담당자는 Redis 15분 bucket을 읽어 IndicatorSnapshot을 만들 수 있다.
- 3번 담당자는 IndicatorSnapshot을 DB에 저장하고 12/24시간 Persona/report API를 제공할 수 있다.
- 세 모듈이 Phase 0 공통 계약의 필드명, enum, 시간 기준을 그대로 사용한다.
