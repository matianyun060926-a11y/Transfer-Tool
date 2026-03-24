from transfer_tool.services.trusted_device_store import TrustedDeviceStore


def test_trusted_device_is_updated_in_place(tmp_path) -> None:
    store = TrustedDeviceStore(tmp_path / "trusted_devices.json")

    first_token, first_record = store.issue_trust("mobile-1", "Matt's iPhone")
    restored = store.restore_trust(first_token, "mobile-1", "Matt's iPhone")
    second_token, second_record = store.issue_trust("mobile-1", "Matt's iPhone")

    assert restored is not None
    assert first_record["device_id"] == "mobile-1"
    assert second_record["pair_count"] == 2
    assert first_token != second_token


def test_trusted_devices_can_be_revoked(tmp_path) -> None:
    store = TrustedDeviceStore(tmp_path / "trusted_devices.json")

    store.issue_trust("mobile-1", "One")
    assert store.revoke_device("mobile-1") is True
    assert store.list_devices() == []
