from pathlib import Path

from transfer_tool.models.history import HistoryEntry
from transfer_tool.services.history_store import HistoryStore


def test_history_store_trims_to_limit(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "history.json", limit=2)
    store.add_entry(HistoryEntry(direction="outgoing", status="success", peer_device_name="A"))
    store.add_entry(HistoryEntry(direction="outgoing", status="success", peer_device_name="B"))
    store.add_entry(HistoryEntry(direction="outgoing", status="success", peer_device_name="C"))

    entries = store.load()

    assert len(entries) == 2
    assert entries[0].peer_device_name == "C"
    assert entries[1].peer_device_name == "B"

