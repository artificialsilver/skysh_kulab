# skysh_kulab

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
