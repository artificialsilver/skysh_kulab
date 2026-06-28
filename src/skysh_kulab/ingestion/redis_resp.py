from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Any


class RedisError(RuntimeError):
    pass


@dataclass
class RedisClient:
    host: str = "127.0.0.1"
    port: int = 6379
    db: int = 0
    timeout: float = 5.0

    def __post_init__(self) -> None:
        self._socket = socket.create_connection((self.host, self.port), self.timeout)
        self._file = self._socket.makefile("rb")
        if self.db:
            self.execute("SELECT", self.db)

    def close(self) -> None:
        self._file.close()
        self._socket.close()

    def execute(self, *parts: Any) -> Any:
        self._socket.sendall(encode_command(parts))
        return self._read_response()

    def ping(self) -> bool:
        return self.execute("PING") == "PONG"

    def hgetall(self, key: str) -> dict[str, str]:
        response = self.execute("HGETALL", key)
        return {
            response[index]: response[index + 1]
            for index in range(0, len(response), 2)
        }

    def keys(self, pattern: str) -> list[str]:
        response = self.execute("KEYS", pattern)
        return list(response or [])

    def _read_response(self) -> Any:
        prefix = self._file.read(1)
        if prefix == b"+":
            return self._read_line()
        if prefix == b"-":
            raise RedisError(self._read_line())
        if prefix == b":":
            return int(self._read_line())
        if prefix == b"$":
            length = int(self._read_line())
            if length == -1:
                return None
            data = self._file.read(length)
            self._file.read(2)
            return data.decode()
        if prefix == b"*":
            length = int(self._read_line())
            if length == -1:
                return None
            return [self._read_response() for _ in range(length)]
        raise RedisError(f"Unknown Redis response prefix: {prefix!r}")

    def _read_line(self) -> str:
        return self._file.readline().removesuffix(b"\r\n").decode()


def encode_command(parts: tuple[Any, ...]) -> bytes:
    chunks = [f"*{len(parts)}\r\n".encode()]
    for part in parts:
        data = str(part).encode()
        chunks.append(f"${len(data)}\r\n".encode())
        chunks.append(data)
        chunks.append(b"\r\n")
    return b"".join(chunks)
