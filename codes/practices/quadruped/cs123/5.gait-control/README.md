# 5. 步态控制 · 配套 demo（自包含）

在**真实 Pupper v3**（§4 的 mesh 模型）上跑开环 trot，渲染两个步态 GIF。整个目录自包含：模型、网格、IK、渲染脚本都在这里，只依赖 `mujoco` / `numpy` / `Pillow`，不引用 `exercises/shared`。

## 目录结构

```
5.gait-control/
├── models/
│   ├── pupper_v3.xml            # 真实 Pupper（与 §4 本体一致，meshdir 指向本地 meshes）
│   └── meshes/                  # STL 网格（Git LFS）
├── pupper_ik.py                 # 真实模型的单腿数值 IK / FK + 建仿真模型（加 weld / 调伺服）
├── render_gait_experiment_gifs.py  # 步态时钟 + 足端轨迹 + 渲染两个 GIF
├── pupper_gait_demo.xml         # 旧简化模型，仅供章节正文引用，本 demo 不再使用
└── outputs/                     # 渲染产物（gitignore，可重生成）
```

## 运行

在 `cs123` 目录下：

```bash
uv run python 5.gait-control/render_gait_experiment_gifs.py
```

产出 `outputs/lab5_inplace_trot.gif`（原地踏步）与 `outputs/lab5_forward_trot.gif`（前进 trot）。

## 实现要点

- **数值 IK**：真实模型的关节是「固定 body 四元数 + 局部 z 轴 hinge」、零角=屈膝、左右镜像，解析玩具 IK 套不上。`pupper_ik.py` 用 MuJoCo 自身求解——设角 → `mj_forward` → 读 `foot_site` → `mj_jacSite` 取雅可比 → DLS 迭代。模型精确，四条腿自动正确，脚一定落在真网格上，无 mesh 与 IK 错位。
- **固定基座**：用 `MjSpec` 在运行时给 `base_link` 加一条到世界的 weld，不另写 XML；前进 trot 逐帧平移焊接点（`eq_data` 的 relpose x）制造前进。
- **驱动**：直接写真实模型自带的位置伺服（`data.ctrl` = 目标关节角），并把 `gainprm/biasprm` 调硬一点让踏步跟踪更利落。
- **站高**：真实屈膝几何下 `STAND_HEIGHT ≈ 0.13`（不是玩具的 0.18）。

## 与章节的关系

章节正文 `docs/.../5.gait-control.md` 目前仍讲简化模型 `pupper_gait_demo.xml` 与 `shared` 的教学 IK；本 demo 是把 GIF 换成真实 Pupper 的独立实现。把章节正文、教学代码与嵌入 GIF 一并切到真实模型，是后续单独的一步。
