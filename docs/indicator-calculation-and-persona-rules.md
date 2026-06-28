# Indicator 계산식 및 Persona 분류 기준

이 문서는 2번 담당자가 구현할 `15m / 4h IndicatorSnapshot` 계산식과 `PersonaSnapshot` 분류 기준을 고정한다.

코드는 작성하지 않고, 구현 기준이 되는 수식과 판단 순서만 정의한다.

## 1. 입력 데이터

Redis에는 1분 단위 `MinuteBucket`만 저장한다.

```text
15m Indicator = 최근 15개 1분 MinuteBucket
4h Indicator  = 최근 240개 1분 MinuteBucket
```

각 `MinuteBucket`은 아래 필드를 가진다.

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

## 2. 기본 지표 계산식

### Window

```text
window_buckets =
  timeframe == 15m ? latest 15 MinuteBucket
  timeframe == 4h  ? latest 240 MinuteBucket
```

유효 bucket이 하나도 없으면 IndicatorSnapshot을 만들지 않는다.

### OHLC

```text
price_open  = first_valid_bucket.open
price_high  = max(bucket.high)
price_low   = min(bucket.low)
price_close = last_valid_bucket.close
```

### 가격 변화율

```text
price_change_pct =
  ((price_close - price_open) / price_open) * 100
```

예외 처리:

```text
if price_open <= 0:
  price_change_pct = 0
```

### 변동성

```text
volatility_pct =
  ((price_high - price_low) / price_open) * 100
```

예외 처리:

```text
if price_open <= 0:
  volatility_pct = 0
```

### 거래대금

```text
total_volume_krw =
  sum(bucket.total_volume_krw)
```

### 수급 합산

```text
whale_buy_krw =
  sum(bucket.whale_buy_krw)

whale_sell_krw =
  sum(bucket.whale_sell_krw)

retail_buy_krw =
  sum(bucket.retail_buy_krw)

retail_sell_krw =
  sum(bucket.retail_sell_krw)
```

### 순수급

```text
whale_net_krw =
  whale_buy_krw - whale_sell_krw

retail_net_krw =
  retail_buy_krw - retail_sell_krw
```

### 수급 비율

```text
whale_net_ratio =
  whale_net_krw / total_volume_krw

retail_net_ratio =
  retail_net_krw / total_volume_krw
```

예외 처리:

```text
if total_volume_krw <= 0:
  whale_net_ratio = 0
  retail_net_ratio = 0
```

### 거래 카운트

```text
trade_count =
  sum(bucket.trade_count)

whale_count =
  sum(bucket.whale_count)

retail_count =
  sum(bucket.retail_count)
```

## 3. 거래량 급증도

거래량 급증도는 현재 window의 거래대금이 과거 평균 대비 얼마나 큰지 나타낸다.

```text
volume_surge_ratio =
  current_window_total_volume_krw / baseline_window_avg_volume_krw
```

기준:

```text
15m baseline = 직전 N개 15분 window 평균 거래대금
4h baseline  = 직전 N개 4시간 window 평균 거래대금
```

baseline 데이터가 부족하면 아래 값으로 둔다.

```text
volume_surge_ratio = 1.0
```

이 값은 “급증도 판단 불가, 평상 수준으로 취급”을 의미한다.

## 4. 다이버전스

다이버전스는 가격 방향과 고래 순수급 방향이 어긋나는 정도를 나타낸다.

```text
price_direction =
  sign(price_change_pct)

whale_direction =
  sign(whale_net_krw)
```

```text
divergence_score =
  if price_direction != 0
  and whale_direction != 0
  and price_direction != whale_direction:
    min(abs(whale_net_ratio), 1.0)
  else:
    0.0
```

해석:

```text
가격 상승 + 고래 순매도 = 상승 중 고래 이탈
가격 하락 + 고래 순매수 = 하락 중 고래 매집 가능성
```

## 5. 4h 보조 지표

4h는 단일 1분 bucket 하나보다 빈도수와 지속성을 더 본다.

4h 계산 시 아래 보조 지표를 `metrics_json`에 저장한다.

```text
positive_bucket_ratio =
  count(bucket.close > bucket.open) / valid_bucket_count

negative_bucket_ratio =
  count(bucket.close < bucket.open) / valid_bucket_count

whale_buy_bucket_ratio =
  count(bucket.whale_buy_krw > bucket.whale_sell_krw) / valid_bucket_count

whale_sell_bucket_ratio =
  count(bucket.whale_sell_krw > bucket.whale_buy_krw) / valid_bucket_count

divergence_bucket_count =
  count(bucket price direction and whale direction diverged)

strong_move_bucket_count =
  count(bucket volatility or volume exceeded threshold)
```

15m는 단기 강도 중심으로 기본 지표를 직접 반영한다.

4h는 기본 지표에 더해 위 보조 지표를 함께 사용해 단일 급등락 bucket 하나가 Persona를 과하게 흔들지 않도록 한다.

## 6. IndicatorSnapshot 필드

계산 결과는 아래 필드를 빠짐없이 포함한다.

```text
market
timeframe
window_start
window_end
snapshot_at
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
```

## 7. Persona Enum

Persona enum은 기존 6개를 그대로 사용한다.

```text
accumulation
breakout
distribution_trap
panic_sell
retail_chop
sleep
```

Persona 판별은 항상 `IndicatorSnapshot`을 입력으로 한다.

동일한 enum을 `15m`, `4h`에서 모두 사용하지만, threshold는 `market + timeframe`별로 다르게 적용한다.

## 8. Persona 분류 기준

아래 `T.*`는 `market + timeframe`별 threshold config 값을 의미한다.

### accumulation

고래 매집.

```text
whale_net_ratio >= T.whale_net_strong
and abs(price_change_pct) <= T.price_flat
and volatility_pct <= T.volatility_low
```

보조 조건:

```text
retail_net_ratio <= T.retail_net_weak
```

### breakout

상방 분출.

```text
price_change_pct >= T.price_up_strong
and volume_surge_ratio >= T.volume_surge
and whale_net_ratio >= T.whale_net_positive
```

보조 조건:

```text
volatility_pct >= T.volatility_mid
```

### distribution_trap

상승 중 고래 이탈 또는 FOMO 위험.

```text
price_change_pct >= T.price_up
and whale_net_ratio <= -T.whale_net_negative
and retail_net_ratio >= T.retail_net_positive
and divergence_score >= T.divergence
```

### panic_sell

하방 투매.

```text
price_change_pct <= -T.price_down_strong
and volatility_pct >= T.volatility_high
and whale_net_ratio <= -T.whale_net_negative
```

보조 조건:

```text
volume_surge_ratio >= T.volume_surge
```

### retail_chop

개미 중심 난타전.

```text
abs(price_change_pct) <= T.price_flat
and volatility_pct >= T.volatility_mid
and abs(whale_net_ratio) <= T.whale_net_weak
and abs(retail_net_ratio) >= T.retail_net_active
```

### sleep

관망장.

```text
abs(price_change_pct) <= T.price_flat
and volatility_pct <= T.volatility_low
and volume_surge_ratio <= T.volume_quiet
and abs(whale_net_ratio) <= T.whale_net_weak
and abs(retail_net_ratio) <= T.retail_net_weak
```

## 9. Persona 분류 우선순위

여러 Persona 조건이 동시에 충족될 수 있으므로 아래 순서로 먼저 매칭되는 Persona를 선택한다.

```text
1. panic_sell
2. distribution_trap
3. breakout
4. accumulation
5. retail_chop
6. sleep
```

이유:

```text
위험 신호를 먼저 잡고,
그다음 추세 분출과 매집을 잡고,
마지막에 중립/관망 상태를 분류한다.
```

## 10. 15m / 4h 판별 차이

### 15m

15m는 단기 강도 중심이다.

주로 아래 지표를 직접 반영한다.

```text
price_change_pct
volatility_pct
volume_surge_ratio
whale_net_ratio
retail_net_ratio
divergence_score
```

### 4h

4h는 빈도수와 지속성 중심이다.

기본 지표는 240개 1분 bucket 전체로 계산한다.

Persona 판별 시 `metrics_json`의 보조 지표를 함께 사용한다.

```text
positive_bucket_ratio
negative_bucket_ratio
whale_buy_bucket_ratio
whale_sell_bucket_ratio
divergence_bucket_count
strong_move_bucket_count
```

4h는 단일 1분 bucket 하나의 급등락보다 4시간 동안 반복된 방향성과 수급 지속성을 우선한다.
