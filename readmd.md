# CoinflowPersona

CoinflowPersona는 Upbit 체결 데이터를 Redis에 1분 단위로 모으고, 최근 bucket을 기준으로 고래/개미 수급과 페르소나를 계산해 보여주는 대시보드입니다.

## 실행

처음 한 번만 의존성을 설치합니다.

```cmd
python -m pip install -r requirements.txt
npm install
```

전체 실행은 아래 파일 하나로 시작합니다.

```cmd
run_all.cmd
```

전체 종료는 아래 파일을 사용합니다.

```cmd
stop_all.cmd
```

개별 실행이 필요하면 각 터미널에서 아래 순서로 실행합니다.

```cmd
run_redis.cmd
run_ingestion.cmd
run_snapshot_worker.cmd
run_backend.cmd
run_frontend.cmd
```

접속 주소는 `http://127.0.0.1:5173` 입니다.

## 화면 구성

관심종목 화면에는 `KRW-BTC`, `KRW-ETH`, `KRW-XRP`가 등록된 상태로 표시됩니다. 종목 카드를 누르면 별도 상세 화면으로 이동하고, 브라우저 뒤로가기 또는 `Watchlist` 버튼으로 목록에 돌아올 수 있습니다.

상세 화면에는 현재가, 변화율, 거래대금, 고래 순매수, 고래/개미 매수·매도 흐름, 페르소나 이미지, 체결 수가 표시됩니다. 페르소나 스냅샷은 PNG 이미지로 표시하며, 알림조건은 별도 탭에서 종목과 페르소나 조합으로 선택합니다.

## 데이터 기준

수집기는 Upbit 체결 데이터를 Redis bucket에 저장합니다. 체결금액이 약 1,000만원 이상이면 고래, 그보다 작으면 개미로 분류합니다. 매수 쪽 체결은 buy, 매도 쪽 체결은 sell에 합산합니다.

스냅샷은 실제 존재하는 Redis bucket 중 최신값을 사용합니다.

- `15m`: 최신 최대 15개 bucket
- `4h`: 최신 최대 240개 bucket

서버를 막 시작해서 bucket이 5개뿐이면 15m와 4h 모두 5개 기준으로 계산합니다. bucket이 30개면 15m는 최신 15개, 4h는 최신 30개 기준으로 계산합니다.

## 확인 명령

프론트 빌드:

```cmd
npm run build
```

백엔드 테스트:

```cmd
python -m pytest -q
```
