"""store.py：内存表（基线：没有检查点，重启全靠回放）。"""
from __future__ import annotations

from wal import Wal


class Store:
    def __init__(self, wal: Wal):
        self.wal = wal
        self.data = {}
        self.puts = 0
        self.deletes = 0
        self.replayed = 0

    def put(self, key, value):
        self.data[key] = value
        self.puts += 1
        self.wal.append({"op": "put", "key": key, "value": value, "seq": self.puts + self.deletes})
        return True

    def delete(self, key):
        self.data.pop(key, None)
        self.deletes += 1
        self.wal.append({"op": "del", "key": key, "seq": self.puts + self.deletes})
        return True

    def get(self, key):
        return self.data.get(key)

    def checkpoint(self) -> bytes:
        raise NotImplementedError("检查点还没实现")

    def recover(self, blob: bytes, checkpoint: bytes = None) -> dict:
        raise NotImplementedError("恢复还没实现")
