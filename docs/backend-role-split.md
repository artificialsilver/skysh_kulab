# 백엔드 3인 역할 분담 및 구현 순서

이 문서는 프론트엔드를 제외하고 백엔드 3명이 병렬로 개발할 때의 역할 분담과 통합 순서를 정리한다.

전체 목표 흐름은 다음과 같다.

```text
Upbit WebSocket
→ Redis 1분 MinuteBucket
→ 15m / 4h IndicatorSnapshot
→ 15m / 4h PersonaSnapshot
→ DB 저장
→ API / Optional Alert
```

## 1. 역할 분담

### 1번 담당자: 실시간 수집 / Redis 적재

담당 범위:

```text
Data Ingestion
Upbit WebSocket
Redis 1분 MinuteBucket
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
- 반드시 지킬 것: Redis key/field 이름, 지정 마켓 3개

### 2번 담당자: 15m/4h 지표 계산 + Persona 판별

담당 범위:

```text
Indicator Engine
15m / 4h IndicatorSnapshot 계산
Persona Engine
15m / 4h PersonaSnapshot 도출
```

주요 역할:

- Redis에서 timeframe별 1분 버킷 조회
- 15m `IndicatorSnapshot` 계산
- 4h `IndicatorSnapshot` 계산
- 코인별·timeframe별 threshold 적용
- `IndicatorSnapshot` 기반 `PersonaSnapshot` 도출
- 15m와 4h 계산 왜곡 차이 반영
- 15m는 단기 강도 중심으로 계산
- 4h는 빈도수·지속성 중심으로 계산

산출물:

```text
Redis 1분 MinuteBucket
→ 15m / 4h IndicatorSnapshot
→ 15m / 4h PersonaSnapshot
```

독립 개발 방법:

```text
fixture MinuteBucket 15개/240개를 넣고 IndicatorSnapshot과 PersonaSnapshot이 기대값으로 나오는지 테스트한다.
```

의존 계약:

- 입력: Redis `MinuteBucket`
- 출력: `IndicatorSnapshot`, `PersonaSnapshot`
- 반드시 지킬 것: 지표 필드명, Persona enum, `market + timeframe`별 threshold
- 코드 저장, DB upsert, API 구현은 담당하지 않는다.

### 3번 담당자: DB 저장 / API / 알림 설정

담당 범위:

```text
Snapshot Storage
FastAPI 조회 API
Alert Settings
Optional Alert Dispatch Targeting
```

주요 역할:

- 2번 담당자의 `IndicatorSnapshot`을 DB에 저장
- 2번 담당자의 `PersonaSnapshot`을 DB에 저장
- `market_indicator_snapshots` 테이블 설계
- `market_persona_snapshots` 테이블 설계
- `(market, timeframe, snapshot_at)` 기준 upsert 구현
- FastAPI 조회 API 제공
- 15m 알림 설정 저장/조회
- 알림 enabled 여부에 따른 발송 대상 판별

산출물:

```text
IndicatorSnapshot / PersonaSnapshot
→ DB 저장
→ timeframe 기반 조회 API
→ Optional Alert
```

독립 개발 방법:

```text
fake IndicatorSnapshot과 fake PersonaSnapshot을 DB에 넣고 조회 API와 알림 설정 동작을 테스트한다.
```

의존 계약:

- 입력: `IndicatorSnapshot`, `PersonaSnapshot`
- 출력: DB 저장 snapshot, FastAPI response, 알림 발송 대상
- 반드시 지킬 것: DB schema, API response shape, 알림 enabled 판별

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
- threshold 설정 위치와 임시값

시간 기준은 내부 저장과 계산은 UTC, 사용자 표시는 KST(Asia/Seoul)로 고정한다.

지정 마켓은 `KRW-BTC`, `KRW-ETH`, `KRW-XRP` 세 개로 고정한다.

v1 분석 timeframe은 `15m`, `4h`만 지원한다.

자세한 공통 계약은 [`phase0-contract.md`](./phase0-contract.md)를 기준으로 한다.

### Phase 1: 병렬 개발

각자 mock 데이터로 독립 개발한다.

```text
1번: fake TradeEvent → Redis MinuteBucket
2번: fake MinuteBucket 15개/240개 → IndicatorSnapshot → PersonaSnapshot
3번: fake IndicatorSnapshot/PersonaSnapshot → DB 저장 + API + 알림 설정
```

이 단계에서는 실제 업비트 연결, 실제 Redis 데이터, 실제 DB 데이터가 모두 완성되어 있지 않아도 된다.

목표는 각 모듈이 독립 입력값으로 자기 책임을 끝까지 처리하는 것이다.

### Phase 2: 1번 + 2번 연결

Redis를 기준으로 수집 계층과 지표/Persona 판단 계층을 붙인다.

```text
Upbit/fake trade
→ Redis 1분 버킷
→ 15m / 4h IndicatorSnapshot
→ 15m / 4h PersonaSnapshot
```

검증할 것:

- Redis bucket 값이 정확히 누적되는지 확인한다.
- timeframe별 bucket 조회가 정확한지 확인한다.
- 비어 있는 분이 있어도 엔진이 깨지지 않는지 확인한다.
- BTC/ETH/XRP별 threshold가 따로 적용되는지 확인한다.
- 15m와 4h가 같은 Persona enum을 쓰되 다른 계산/임계값을 적용하는지 확인한다.
- 4h Persona가 단일 1분 bucket 급등락 하나에 과하게 흔들리지 않는지 확인한다.

### Phase 3: 2번 + 3번 연결

15m/4h 지표와 Persona 결과를 DB에 저장하고, timeframe 기반 API로 조회한다.

```text
IndicatorSnapshot
→ PersonaSnapshot
→ DB upsert
→ timeframe 기반 API
→ Optional Alert
```

검증할 것:

- 15m/4h 경계 시각 기준으로 snapshot이 저장되는지 확인한다.
- 같은 `market + timeframe + snapshot_at` 재실행 시 중복 insert가 아니라 upsert 되는지 확인한다.
- DB에 IndicatorSnapshot의 지표 필드가 누락 없이 저장되는지 확인한다.
- PersonaSnapshot이 같은 시각의 IndicatorSnapshot 기반으로 저장되는지 확인한다.
- 15m Persona가 계산되어도 알림 off면 알림되지 않는지 확인한다.

### Phase 4: 전체 통합

최종 파이프라인을 검증한다.

```text
Upbit WebSocket
→ Redis 1분 MinuteBucket
→ 15m / 4h IndicatorSnapshot
→ 15m / 4h PersonaSnapshot
→ DB 저장
→ API / Optional Alert
```

검증할 것:

- WebSocket 연결이 장시간 유지되는지 확인한다.
- Redis 1분 버킷이 지속적으로 쌓이고 TTL로 정리되는지 확인한다.
- 15m와 4h IndicatorSnapshot이 지속적으로 계산되는지 확인한다.
- 15m와 4h PersonaSnapshot이 지속적으로 계산되는지 확인한다.
- DB unique 기준이 `(market, timeframe, snapshot_at)`으로 동작하는지 확인한다.
- API 응답이 Phase 0 계약과 맞는지 확인한다.
- 15m 알림 설정에 따라 발송 대상이 정확히 판별되는지 확인한다.

## 3. API Contract

신규 API는 timeframe 중심으로 정리한다.

```text
GET /api/markets
GET /api/market/{market}/snapshots?timeframe=15m
GET /api/market/{market}/snapshots?timeframe=4h
GET /api/market/{market}/persona?timeframe=15m
GET /api/market/{market}/persona?timeframe=4h
GET /api/market/{market}/alerts/settings
PUT /api/market/{market}/alerts/settings
```

고정 규칙:

- `timeframe`은 v1에서 `15m`, `4h`만 허용한다.
- `/snapshots`는 IndicatorSnapshot을 반환한다.
- `/persona`는 PersonaSnapshot을 반환한다.
- 알림 설정은 v1에서 15m Persona 알림에 적용한다.

## 4. 독립 개발 가능 범위

완전히 독립적으로 먼저 개발 가능한 작업:

- Upbit trade message parser
- fake `TradeEvent` 기반 Redis bucket writer
- fixture `MinuteBucket` 기반 15m/4h indicator engine
- fake `IndicatorSnapshot` 기반 persona rule engine
- fake `IndicatorSnapshot`/`PersonaSnapshot` 기반 DB upsert
- FastAPI 조회 API response schema
- 15m 알림 설정 저장/조회

서로 의존하는 작업:

- 15m/4h indicator는 Redis bucket schema에 의존한다.
- Persona engine은 IndicatorSnapshot field와 Persona enum에 의존한다.
- DB 저장은 `IndicatorSnapshot`과 `PersonaSnapshot`에 의존한다.
- API는 DB snapshot schema에 의존한다.
- 알림 발송 대상 판별은 15m PersonaSnapshot과 알림 설정에 의존한다.

## 5. 완료 기준

역할 분담 기준 완료 상태:

- 1번 담당자는 fake 또는 실제 체결을 Redis 1분 bucket으로 적재할 수 있다.
- 2번 담당자는 Redis bucket을 읽어 15m/4h IndicatorSnapshot을 만들 수 있다.
- 2번 담당자는 IndicatorSnapshot 기반으로 15m/4h PersonaSnapshot을 만들 수 있다.
- 2번 담당자는 코인별·timeframe별 threshold와 15m/4h 계산 차이를 반영할 수 있다.
- 3번 담당자는 IndicatorSnapshot과 PersonaSnapshot을 DB에 저장할 수 있다.
- 3번 담당자는 timeframe 기반 API와 15m 알림 설정 API를 제공할 수 있다.
- 세 모듈이 Phase 0 공통 계약의 필드명, enum, 시간 기준을 그대로 사용한다.
