"""wal.py：追加日志（基线：只追加，不认残尾）。"""
from __future__ import annotations

import json


class Wal:
    def __init__(self):
        self.records = []
        self.appended = 0
        self.truncated = 0

    def append(self, record: dict) -> int:
        self.records.append(record)
        self.appended += 1
        return self.appended

    def dump(self) -> bytes:
        return b"".join((json.dumps(r, ensure_ascii=False) + "\n").encode() for r in self.records)

    def load(self, blob: bytes) -> int:
        """基线：整段按行解析，遇到坏行直接抛错。"""
        self.records = []
        for line in blob.decode().splitlines():
            if not line.strip():
                continue
            self.records.append(json.loads(line))
        return len(self.records)

    def truncate(self, upto: int) -> int:
        return 0
