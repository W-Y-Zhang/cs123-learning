
## 环境准备

用 [uv](https://docs.astral.sh/uv/) 管理依赖。在本目录下执行：

```bash
uv sync
```

`uv sync` 会按 `.python-version` 自动准备 Python 3.12，创建 `.venv` 并安装 `pyproject.toml` 里锁定的依赖（mujoco、gymnasium）。

之后用 `uv run` 执行脚本，无需手动激活环境：

```bash
uv run python xxx.py
```

macOS 上跑交互式 viewer 必须用 `mjpython`，Linux / Windows 用 `python` 即可：

```bash
uv run mjpython xxx.py
```

## 运行指南

### 4.quadruped-mjcf

```bash
uv run python 4.quadruped-mjcf/view_pupper_v3_fixed.py
# MacOS
uv run mjpython python 4.quadruped-mjcf/view_pupper_v3_fixed.py
```