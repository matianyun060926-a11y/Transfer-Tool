from transfer_tool.ui.app_state import AppState
from transfer_tool.ui.main_window import run_app


def main() -> int:
    state = AppState()
    return run_app(state)


if __name__ == "__main__":
    raise SystemExit(main())

