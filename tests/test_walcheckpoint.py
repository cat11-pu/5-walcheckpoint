import unittest

from store import Store
from wal import Wal


class TestBasics(unittest.TestCase):
    def test_put_get(self):
        store = Store(Wal())
        store.put("a", "1")
        self.assertEqual(store.get("a"), "1")

    def test_delete(self):
        store = Store(Wal())
        store.put("a", "1")
        store.delete("a")
        self.assertIsNone(store.get("a"))

    def test_wal_appends(self):
        wal = Wal()
        store = Store(wal)
        store.put("a", "1")
        store.put("b", "2")
        self.assertEqual(wal.appended, 2)

    def test_wal_roundtrip(self):
        wal = Wal()
        wal.append({"op": "put", "key": "a", "value": "1", "seq": 1})
        blob = wal.dump()
        fresh = Wal()
        self.assertEqual(fresh.load(blob), 1)

    def test_counters(self):
        store = Store(Wal())
        store.put("a", "1")
        store.delete("a")
        self.assertEqual((store.puts, store.deletes), (1, 1))


if __name__ == "__main__":
    unittest.main()
