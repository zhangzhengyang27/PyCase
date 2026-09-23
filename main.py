"""Python 示例仓库桌面管理器入口。"""

import sys
from pathlib import Path

# 将 desktop-app 目录和仓库根目录添加到 sys.path
# 前者用于导入 app 包，后者用于示例内部导入（示例仓库已并入本项目时两者相同）
APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = (
    APP_DIR
    if all((APP_DIR / d).is_dir() for d in ("topics", "tools", "projects"))
    else APP_DIR.parent
)
sys.path.insert(0, str(APP_DIR))
if REPO_ROOT != APP_DIR:
    sys.path.insert(0, str(REPO_ROOT))

from PyQt6.QtWidgets import QApplication

from app.logger import configure_logging
from app.ui.main_window import MainWindow
from app.ui.theme import global_stylesheet


def main() -> int:
    """应用主入口。"""
    configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("蟒匣 PyCase")
    app.setApplicationDisplayName("蟒匣 PyCase")

    # 设置全局样式
    app.setStyle("Fusion")
    app.setStyleSheet(global_stylesheet())

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
