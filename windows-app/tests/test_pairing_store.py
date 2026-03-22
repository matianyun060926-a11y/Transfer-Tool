from transfer_tool.services.pairing import PairingManager


def test_pairing_manager_accepts_valid_code() -> None:
    manager = PairingManager()
    snapshot = manager.enable_receive_mode()

    session = manager.create_session("sender1", "Laptop", snapshot.pairing_code)

    assert manager.validate_session(session.session_token) is not None


def test_pairing_manager_rejects_invalid_code() -> None:
    manager = PairingManager()
    manager.enable_receive_mode()

    try:
        manager.create_session("sender1", "Laptop", "000000")
    except ValueError as exc:
        assert "did not match" in str(exc)
    else:
        raise AssertionError("Expected invalid pairing code to fail")

