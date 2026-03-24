import pytest

from transfer_tool.services.pairing import PairingManager


def test_pairing_manager_accepts_valid_code() -> None:
    manager = PairingManager()
    snapshot = manager.enable_receive_mode()

    session = manager.create_session("sender1", "Laptop", snapshot.pairing_code)

    assert manager.validate_session(session.session_token) is not None


def test_pairing_manager_rejects_invalid_code() -> None:
    manager = PairingManager()
    manager.enable_receive_mode()

    with pytest.raises(ValueError, match="did not match"):
        manager.create_session("sender1", "Laptop", "000000")


def test_pairing_manager_accepts_qr_token_once() -> None:
    manager = PairingManager()
    snapshot = manager.enable_receive_mode()

    session = manager.create_session_from_qr("sender1", "Laptop", snapshot.qr_pair_token)

    assert manager.validate_session(session.session_token) is not None
    with pytest.raises(ValueError, match="no longer valid"):
        manager.create_session_from_qr("sender1", "Laptop", snapshot.qr_pair_token)


def test_pairing_manager_creates_trusted_session_without_receive_mode() -> None:
    manager = PairingManager()
    manager.disable_receive_mode()

    session = manager.create_trusted_session("sender1", "Laptop")

    assert manager.validate_session(session.session_token) is not None
