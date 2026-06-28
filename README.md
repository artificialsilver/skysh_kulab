# skysh_kulab

관심종목 3개(`KRW-BTC`, `KRW-ETH`, `KRW-XRP`)의 수집, 지표/Persona 계산, SQLite 저장/API, 프론트 대시보드를 함께 실행할 수 있다.

## 전체 실행

Python 의존성:

```bash
python -m pip install -r requirements.txt
```

프론트 의존성:

```bash
npm install
```

백엔드 API:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

프론트:

```bash
npm run dev -- --port 5173
```

접속:

```text
http://127.0.0.1:5173
```

Windows에서 한 번에 실행:

```cmd
run_all.cmd
```

개별 실행:

```cmd
run_redis.cmd
run_ingestion.cmd
run_snapshot_worker.cmd
run_backend.cmd
run_frontend.cmd
```

기본값에서는 demo snapshot을 만들지 않는다. Redis 수집과 snapshot worker가 돌아서 SQLite에 저장한 값만 프론트에 표시된다. 임시 demo seed가 필요할 때만 `SKYSH_SEED_DEMO=1`로 백엔드를 실행한다.

실제 수집부터 DB 저장까지 실행:

PowerShell:

```powershell
docker compose up -d redis
python -m skysh_kulab.ingestion.main run
```

Git Bash:

```bash
docker compose up -d redis
python -m skysh_kulab.ingestion.main run
```

다른 터미널에서 Redis bucket을 SQLite snapshot으로 저장:

PowerShell:

```powershell
python -m app.snapshot_worker run --interval 30
```

snapshot worker는 Redis에 실제 존재하는 bucket key를 최신순으로 읽는다. `15m`은 최신 최대 15개, `4h`는 최신 최대 240개를 사용한다. 서버 시작 직후 bucket이 5개뿐이면 두 timeframe 모두 5개 기준으로 계산하고, bucket이 30개면 `15m`은 최신 15개, `4h`는 최신 30개 기준으로 계산한다.

Git Bash:

```bash
python -m app.snapshot_worker run --interval 30
```

수집/저장 상태 확인:

PowerShell:

```powershell
python -m skysh_kulab.ingestion.main ping-redis
python -m app.snapshot_worker once
```

Git Bash:

```bash
python -m skysh_kulab.ingestion.main ping-redis
python -m app.snapshot_worker once
```

루트 패키지 shim이 `src/skysh_kulab`를 자동으로 연결하므로 repo root에서는 별도 `PYTHONPATH` 없이 실행된다.

## 검증

```bash
python -m pytest -q
npm run build
```

## 모듈 연결

```text
Upbit WebSocket
→ Redis 1분 MinuteBucket
→ app.pipeline adapter
→ 15m / 4h IndicatorSnapshot
→ 15m / 4h PersonaSnapshot
→ SQLite 저장
→ FastAPI
→ Vite frontend
```

1번 담당자 범위의 Python 구현이다.

```text
Upbit WebSocket
→ TradeEvent
→ Redis 1분 MinuteBucket
```

## Redis 실행

```bash
docker compose up -d redis
```

Redis는 메모리 사용량이 약 20MB에 도달하면 TTL이 설정된 key를 자동으로 제거한다.

```text
maxmemory 20mb
maxmemory-policy volatile-ttl
```

## Redis 적재 확인

```bash
python3 -m skysh_kulab.ingestion.main ping-redis
python3 -m skysh_kulab.ingestion.main fake-once
```

`fake-once`는 현재 UTC minute 기준으로 아래 형태의 Redis hash를 만든다.

```text
bucket:KRW-BTC:{yyyyMMddHHmm}
```

## Upbit WebSocket 실행

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m skysh_kulab.ingestion.main run
```

수집 마켓은 `KRW-BTC`, `KRW-ETH`, `KRW-XRP`로 고정되어 있다.

## Redis 20MB 삭제 정책 테스트

설정이 적용됐는지 확인한다.

```bash
docker compose up -d redis
docker exec -it skysh-kulab-redis redis-cli CONFIG GET maxmemory
docker exec -it skysh-kulab-redis redis-cli CONFIG GET maxmemory-policy
```

예상값:

```text
maxmemory: 20971520
maxmemory-policy: volatile-ttl
```

현재 메모리 사용량은 이렇게 본다.

```bash
docker exec -it skysh-kulab-redis redis-cli INFO memory
```

실제 삭제 동작은 많은 bucket key가 쌓인 뒤 아래 값이 증가하는지 보면 된다.

```bash
docker exec -it skysh-kulab-redis redis-cli INFO stats
```

`evicted_keys`가 0보다 커지면 Redis가 20MB 제한 때문에 key를 자동 삭제한 것이다.
