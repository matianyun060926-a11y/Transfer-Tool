from pathlib import Path

import transfer_tool.services.runtime_paths as runtime_paths


def test_resolve_paths_in_source_mode(monkeypatch) -> None:
    monkeypatch.delattr(runtime_paths.sys, "frozen", raising=False)
    monkeypatch.delattr(runtime_paths.sys, "_MEIPASS", raising=False)

    paths = runtime_paths.resolve_app_paths()

    assert paths.is_frozen is False
    assert paths.web_root.name == "web-app"
    assert paths.icon_path.name == "transfer-tool.ico"


def test_resolve_paths_in_packaged_mode_uses_local_app_data(monkeypatch, tmp_path: Path) -> None:
    fake_exe = tmp_path / "dist" / "TransferTool.exe"
    fake_exe.parent.mkdir(parents=True)
    fake_resource_root = tmp_path / "_MEI12345"
    fake_resource_root.mkdir()
    local_app_data = tmp_path / "AppData" / "Local"

    monkeypatch.setattr(runtime_paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(runtime_paths.sys, "executable", str(fake_exe), raising=False)
    monkeypatch.setattr(runtime_paths.sys, "_MEIPASS", str(fake_resource_root), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))

    paths = runtime_paths.resolve_app_paths()

    assert paths.is_frozen is True
    assert paths.packaged_executable == fake_exe
    assert paths.resource_root == fake_resource_root
    assert paths.runtime_root == local_app_data / "TransferTool"
    assert paths.web_root == fake_resource_root / "web-app"
