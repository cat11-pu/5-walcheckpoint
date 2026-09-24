"""把 sample/crash.json 跑一遍，打印验收面（三个子系统）。"""
import json
import os
import sys

from store import Store
from wal import Wal


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("sample", "crash.json")
    with open(path, encoding="utf-8") as handle:
        spec = json.load(handle)
    wal = Wal()
    store = Store(wal)
    for item in spec["writes"]:
        if item["op"] == "put":
            store.put(item["key"], item["value"])
        else:
            store.delete(item["key"])
    blob = wal.dump()
    mark = spec["crash_at"]
    cut = blob[: mark] if mark <= len(blob) else blob
    checkpoint = store.checkpoint()
    fresh_wal = Wal()
    fresh = Store(fresh_wal)
    info = fresh.recover(cut, checkpoint)
    print("恢复后的键值 =", sorted(fresh.data.items()))
    print("重放条数 =", info.get("replayed"))
    print("残尾忽略 =", info.get("truncated"))
    print("检查点覆盖的序号 =", info.get("checkpoint_seq"))
    print("检查点之后剩余日志条数 =", info.get("remaining"))
    print("恢复后总量不变 =", info.get("puts") == store.puts)
    print("不变量（seq 单调且无空洞） =", info.get("seq_ok"))
    print("检查点字节数 =", len(checkpoint))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
