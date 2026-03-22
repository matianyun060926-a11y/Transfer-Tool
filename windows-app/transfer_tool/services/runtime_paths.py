from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppPaths:
    project_root: Path
    resource_root: Path
    runtime_root: Path
    web_root: Path
    scripts_root: Path
    icon_path: Path
    packaged_executable: Path | None
    is_frozen: bool


def resolve_app_paths() -> AppPaths:
    is_frozen = bool(getattr(sys, "frozen", False))
    if is_frozen:
        executable_path = Path(sys.executable).resolve()
        install_root = executable_path.parent
        resource_root = Path(getattr(sys, "_MEIPASS", install_root))
        return AppPaths(
            project_root=install_root,
            resource_root=resource_root,
            runtime_root=install_root / "runtime_data",
            web_root=resource_root / "web-app",
            scripts_root=install_root / "scripts",
            icon_path=resource_root / "windows-app" / "resources" / "transfer-tool.ico",
            packaged_executable=executable_path,
            is_frozen=True,
        )

    project_root = Path(__file__).resolve().parents[3]
    return AppPaths(
        project_root=project_root,
        resource_root=project_root,
        runtime_root=project_root / "runtime_data",
        web_root=project_root / "web-app",
        scripts_root=project_root / "windows-app" / "scripts",
        icon_path=project_root / "windows-app" / "resources" / "transfer-tool.ico",
        packaged_executable=None,
        is_frozen=False,
    )
