"""store.py：内存表 + WAL，支持检查点与按检查点恢复。"""
from __future__ import annotations

import json
import struct

from wal import Wal


_MAGIC = b"WCP"
_HEADER = struct.Struct(">QI")  # 最大 seq、累计 put 数（del 数 = seq - puts）


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
        """返回检查点字节：魔数 + seq/puts + 内存表快照（紧凑 JSON）。"""
        snapshot = json.dumps(self.data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return _MAGIC + _HEADER.pack(self.puts + self.deletes, self.puts) + snapshot

    def recover(self, blob: bytes, checkpoint: bytes = None) -> dict:
        """先载入检查点，再只回放 seq 严格大于检查点 seq 的记录。"""
        checkpoint_seq = 0
        self.data = {}
        self.puts = 0
        self.deletes = 0

        if checkpoint:
            offset = len(_MAGIC)
            magic = checkpoint[:offset]
            if magic != _MAGIC:
                raise ValueError("检查点格式无法识别")
            checkpoint_seq, self.puts = _HEADER.unpack_from(checkpoint, offset)
            offset += _HEADER.size
            self.data = json.loads(checkpoint[offset:].decode("utf-8"))
            self.deletes = checkpoint_seq - self.puts

        self.wal = Wal()
        self.wal.load(blob)
        truncated = self.wal.truncated

        replayed = 0
        last_seq = checkpoint_seq
        seq_ok = True
        for record in self.wal.records:
            seq = record.get("seq", 0)
            if seq <= checkpoint_seq:
                continue
            # seq 必须严格递增、相邻连续，否则说明日志有空洞。
            if seq != last_seq + 1:
                seq_ok = False
                continue
            last_seq = seq
            if record["op"] == "put":
                self.data[record["key"]] = record["value"]
                self.puts += 1
            else:
                self.data.pop(record["key"], None)
                self.deletes += 1
            replayed += 1

        self.replayed = replayed
        remaining = sum(1 for record in self.wal.records if record.get("seq", 0) > checkpoint_seq)
        return {
            "replayed": replayed,
            "truncated": truncated,
            "checkpoint_seq": checkpoint_seq,
            "remaining": remaining,
            "puts": self.puts,
            "seq_ok": seq_ok,
        }
