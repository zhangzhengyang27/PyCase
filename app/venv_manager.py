"""虚拟环境管理器：全项目共享一份 .venv，所有示例统一在其中运行。

本项目是一个应用，示例是它的模块——

- 共享 venv 位于仓库根 ``.venv``，首次使用时由真实 Python 自动创建；
- 创建时按**项目级依赖清单**（仓库根 ``requirements.txt``，由
  ``scripts/gen_shared_requirements.py`` 汇总全部示例的依赖声明生成）逐项安装；
  清单缺失时回退到内置的 ``BOOTSTRAP_PACKAGES`` 常用库；
- 示例目录的 ``requirements.txt`` 作为模块级兜底：运行时发现清单外的新依赖
  仍会装入同一份 venv（以内容 hash 记录避免重复安装）。
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
from collections.abc import Iterable
from pathlib import Path

from .logger import get_logger


class VenvManager:
    """管理项目级共享虚拟环境。"""

    VENV_DIR_NAME = ".venv"
    LEGACY_CACHE_DIR_NAME = ".desktop-app-venvs"  # 旧版按示例隔离的 venv 缓存
    MARKER_FILE_NAME = ".installed-requirements.json"
    # 项目级共享依赖清单（仓库根，由 scripts/gen_shared_requirements.py 生成）：
    # 本项目是一个应用，全部示例是它的模块，依赖在此声明一次
    MANIFEST_FILE_NAME = "requirements.txt"

    # 清单缺失时的兜底常用库（开发/测试注入用）
    BOOTSTRAP_PACKAGES = (
        "requests",
        "numpy",
        "matplotlib",
        "pillow",
        "beautifulsoup4",
        "lxml",
        "flask",
        "selenium",
        "scrapy",
        "PyMySQL",
        "opencv-python",
    )

    BOOTSTRAP_TIMEOUT = 600  # 单个包的安装上限（大包如 opencv 下载较慢）
    INSTALL_TIMEOUT = 300
    CREATE_TIMEOUT = 120

    def __init__(
        self,
        repo_root: Path,
        python_exe: str | None = None,
        bootstrap_packages: Iterable[str] | None = None,
        venv_root: Path | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        # venv 可写根可注入：打包模式下 repo_root（Resources）只读，
        # sidecar 会把 userData 传进来；默认与 repo_root 同级（旧行为）
        self.venv_path = (venv_root or self.repo_root) / self.VENV_DIR_NAME
        self.legacy_cache_dir = (venv_root or self.repo_root) / self.LEGACY_CACHE_DIR_NAME
        # PyInstaller 冻结环境中 sys.executable 是 sidecar 自身，须由调用方传入真实 Python
        self.python_exe = python_exe or sys.executable
        # 供测试注入空列表跳过引导安装
        self.bootstrap_packages = (
            tuple(bootstrap_packages) if bootstrap_packages is not None else self.BOOTSTRAP_PACKAGES
        )
        self._lock = threading.Lock()
        self._marker: dict = {}
        self._marker_loaded = False
        # uv 可执行文件路径缓存（None 表示未检测，False 表示不可用）
        self._uv: str | None = None

    def _find_uv(self) -> str | None:
        """检测系统中是否有 uv（极速 Python 包管理器），可用则返回路径，否则返回 None。

        uv 的 pip install 比传统 pip 快 10-50 倍，且并行下载与安装，
        能显著缩短首次启动时 150+ 依赖的安装时间。
        仅检测一次，结果缓存在 self._uv 中。
        """
        if self._uv is not None:
            return self._uv or None
        uv_path = shutil.which("uv")
        self._uv = uv_path or False
        return uv_path

    # ------------------------------------------------------------ 公共接口
    def get_python_executable(self) -> Path:
        """返回共享虚拟环境中的 Python 解释器路径。"""
        if sys.platform == "win32":
            return self.venv_path / "Scripts" / "python.exe"
        return self.venv_path / "bin" / "python"

    def needs_prepare(self) -> bool:
        """共享 venv 是否尚未就绪（不存在或引导安装未完成）。"""
        return not (self.get_python_executable().exists() and self._load_marker().get("bootstrap"))

    def ensure_python(self, file_path: Path) -> tuple[bool, str]:
        """确保共享 venv 可用，并安装示例声明的依赖；返回 (是否可用, 解释器路径)。

        所有示例统一使用共享 venv；仅当 venv 创建失败时才回退到系统 Python。
        涉及 subprocess 的阻塞操作，调用方须放入线程池执行。
        """
        with self._lock:
            if not self._prepare_venv():
                return False, self.python_exe
            self._install_example_requirements(file_path)
            return True, str(self.get_python_executable())

    def prepare(self) -> bool:
        """预热共享 venv（创建 + 引导安装），供 sidecar 启动时后台调用。"""
        with self._lock:
            return self._prepare_venv()

    def find_requirements(self, file_path: Path) -> Path | None:
        """查找示例所在目录的 requirements.txt。"""
        req = file_path.parent / "requirements.txt"
        return req if req.exists() else None

    def install_packages(self, packages: list[str]) -> tuple[list[str], list[str]]:
        """把若干第三方包装进共享 venv（缺依赖修复路径）；返回 (已装, 失败)。

        逐包装、失败即收集：一个坏包不该拖垮其余依赖。调用方须放入线程池。
        """
        installed: list[str] = []
        failed: list[str] = []
        with self._lock:
            if not self._prepare_venv():
                return [], list(packages)
            for pkg in packages:
                if self._pip_install([pkg], timeout=self.BOOTSTRAP_TIMEOUT):
                    installed.append(pkg)
                else:
                    failed.append(pkg)
        return installed, failed

    def clear_all_cache(self) -> int:
        """清理共享 venv 与旧版按示例 venv 缓存，返回清理的目录数量。"""
        with self._lock:  # 与 ensure_python/prepare 互斥：不能并发删除 pip 正在写入的环境
            count = 0
            for d in (self.venv_path, self.legacy_cache_dir):
                if d.exists():
                    shutil.rmtree(d, ignore_errors=True)
                    count += 1
            self._marker = {}
            self._marker_loaded = False
            return count

    # ------------------------------------------------------------ 内部实现
    def _prepare_venv(self) -> bool:
        """确保共享 venv 存在并完成引导安装（须持有锁）。"""
        python_exe = self.get_python_executable()
        if not python_exe.exists():
            get_logger(__name__).info("创建共享虚拟环境: %s", self.venv_path)
            if not self._create_venv():
                return False
        marker = self._load_marker()
        if not marker.get("bootstrap"):
            self._install_bootstrap()
        return True

    def _create_venv(self) -> bool:
        """用真实 Python 创建共享 venv。优先使用 uv venv（速度更快），回退到 python -m venv。"""
        uv = self._find_uv()
        try:
            if uv:
                # uv venv 创建速度比 python -m venv 快 2-3 倍
                result = subprocess.run(
                    [uv, "venv", "--python", self.python_exe, str(self.venv_path)],
                    capture_output=True,
                    text=True,
                    timeout=self.CREATE_TIMEOUT,
                )
                if result.returncode == 0:
                    return True
                get_logger(__name__).warning(
                    "uv venv 创建失败，回退到 python -m venv: %s", (result.stderr or result.stdout or "").strip()[-500:]
                )
            result = subprocess.run(
                [self.python_exe, "-m", "venv", str(self.venv_path)],
                capture_output=True,
                text=True,
                timeout=self.CREATE_TIMEOUT,
            )
            if result.returncode == 0:
                return True
        except (OSError, subprocess.TimeoutExpired):
            pass
        # 创建失败（含超时中断）时清掉残留的半个 venv：python.exe 可能已存在，
        # 残留会让下次直接跳过创建，在残破环境里装包并被永久放行
        shutil.rmtree(self.venv_path, ignore_errors=True)
        return False

    def _install_bootstrap(self) -> None:
        """按项目级清单预装依赖：逐项安装，失败跳过，避免单个包拖垮整个环境。"""
        lines = self._manifest_packages()
        if not lines:
            lines = list(self.bootstrap_packages)
        if not lines:
            marker = self._load_marker()
            marker["bootstrap"] = True
            self._save_marker(marker)
            return
        failed: list[str] = []
        for pkg in lines:
            ok = self._pip_install([pkg], timeout=self.BOOTSTRAP_TIMEOUT)
            if not ok:
                failed.append(pkg)
        if failed:
            get_logger(__name__).warning("引导依赖安装失败（可手动补装）: %s", ", ".join(failed))
        # 全部失败（如离线/网络故障）时不标记完成：下次运行会重试引导，
        # 避免把一个缺所有依赖的空环境永久放行；部分失败仍只做一次（失败包手动补装）
        if len(failed) < len(lines):
            marker = self._load_marker()
            marker["bootstrap"] = True
            self._save_marker(marker)

    def _manifest_packages(self) -> list[str]:
        """读取仓库根的共享依赖清单（requirements.txt），过滤注释与空行。"""
        try:
            lines = (self.repo_root / self.MANIFEST_FILE_NAME).read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return []
        return [line.strip() for line in lines if line.strip() and not line.startswith("#")]

    def _install_example_requirements(self, file_path: Path) -> None:
        """把示例目录的 requirements.txt 安装进共享 venv（按内容 hash 去重）。"""
        requirements = self.find_requirements(file_path)
        if requirements is None:
            return
        try:
            digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
        except OSError:
            return
        if digest in self._load_marker().get("requirements", {}):
            return
        if self._pip_install(["-r", str(requirements)], timeout=self.INSTALL_TIMEOUT):
            marker = self._load_marker()
            marker.setdefault("requirements", {})[digest] = True
            self._save_marker(marker)
        # 安装失败不记录 hash，下次运行该示例时重试

    def _pip_install(self, args: list[str], timeout: int) -> bool:
        """在共享 venv 中执行 pip install，返回是否成功。

        优先使用 uv pip install（并行下载+安装，速度比传统 pip 快 10-50 倍），
        不可用时回退到 python -m pip install。
        """
        uv = self._find_uv()
        venv_python = str(self.get_python_executable())
        try:
            if uv:
                # uv pip install 需要通过 --python 指定目标解释器
                result = subprocess.run(
                    [
                        uv,
                        "pip",
                        "install",
                        "--python",
                        venv_python,
                        "--disable-pip-version-check",
                        *args,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            else:
                result = subprocess.run(
                    [
                        venv_python,
                        "-m",
                        "pip",
                        "install",
                        "--disable-pip-version-check",
                        *args,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
        except (OSError, subprocess.TimeoutExpired) as e:
            get_logger(__name__).error("安装依赖异常: %s", e)
            return False
        if result.returncode != 0:
            get_logger(__name__).error(
                "安装依赖失败: %s", (result.stderr or result.stdout or "未知错误").strip()[-2000:]
            )
        return result.returncode == 0

    def _marker_file(self) -> Path:
        return self.venv_path / self.MARKER_FILE_NAME

    def _load_marker(self) -> dict:
        """读取安装记录（venv 内），缺失或损坏时返回空 dict。"""
        if not self._marker_loaded:
            try:
                self._marker = json.loads(self._marker_file().read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self._marker = {}
            self._marker_loaded = True
        return self._marker

    def _save_marker(self, marker: dict) -> None:
        # 临时文件 + 原子替换：marker 损坏的后果是触发全量重装，不值得冒这个险
        try:
            target = self._marker_file()
            tmp = target.with_name(target.name + ".tmp")
            tmp.write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp, target)
        except OSError:
            pass
        self._marker = marker
        self._marker_loaded = True
