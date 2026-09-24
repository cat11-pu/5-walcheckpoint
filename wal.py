"""wal.py：追加日志（JSONL，识别末尾残尾，支持按 seq 截断）。"""
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
        """按行解析 JSONL。

        末尾最后一条没写完整的记录（无法解析的残尾）直接丢弃并计入
        ``truncated``，前面的完整记录照常载入。
        """
        self.records = []
        self.truncated = 0
        for line in blob.decode("utf-8").split("\n"):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                # 残尾只能出现在日志末尾：丢掉它，后面也不会再有完整记录。
                self.truncated += 1
                break
            self.records.append(record)
        return len(self.records)

    def truncate(self, upto: int) -> int:
        """丢掉 seq 不大于 ``upto`` 的记录，返回丢掉的条数。"""
        kept = [record for record in self.records if record["seq"] > upto]
        dropped = len(self.records) - len(kept)
        self.records = kept
        return dropped
