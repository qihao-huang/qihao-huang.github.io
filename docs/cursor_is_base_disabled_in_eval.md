# Is base disabled in eval?
_Exported on 2026/7/29 at GMT+8 14:06:51 from Cursor (3.13.10)_

---

**User**

Answer in Simplified Chinese, concise:

User asks: In their lerobot-eval of smolvla_robocasa on RoboCasa, is the mobile base / chassis disabled? Do other leaderboard evals (RoboCasa365, etc.) disable the base?

Check:
1. main/lerobot/src/lerobot/envs/robocasa.py convert_action - all 12 dims including base_motion and control_mode
2. Any code that zeros base actions during eval
3. HybridMobileBase - base is always part of action space
4. Official RoboCasa365 multitask eval - does it use full 12D / base control?
5. Clarify: "base unused in most atomic" ≠ "base turned off"

Also note: RLinf DEFAULT base_mode=-1 is different stack; LeRobot policy outputs full action.

Conclude clearly: 评测是否关掉底盘；榜单是否关掉。

---

**Cursor**

我先核对 LeRobot 的 RoboCasa 动作转换与评测里是否会把底盘动作置零。

发现 `env_utils.py` 里有把 `base_motion` 置零的逻辑，正在核对它是否用于正式评测路径。

## 结论

**LeRobot `smolvla_robocasa` 评测：没有关掉底盘。**  
**RoboCasa365 等官方/榜单评测：同样没有关掉底盘，用的是完整 12D（含 base）。**

---

### 1. LeRobot 路径：12D 原样下发

`convert_action` 把策略输出的 **12 维全部切开**，含 `base_motion(4)` + `control_mode(1)`，没有置零：

```101:112:/home/sany/Documents/Foundation/main/lerobot/src/lerobot/envs/robocasa.py
def convert_action(flat_action: np.ndarray) -> dict[str, Any]:
    """Split a flat (12,) action vector into a RoboCasa action dict.
    Layout: base_motion(4) + control_mode(1) + ee_pos(3) + ee_rot(3) + gripper(1)
    """
    return {
        "action.base_motion": flat_action[0:4],
        "action.control_mode": flat_action[4:5],
        ...
    }
```

`step` → `unmap_action` → `robot0_base` / `robot0_torso` / `robot0_base_mode` → **`HybridMobileBase`**。LeRobot 评测代码里**没有**把 base 清零的逻辑。

唯一清零出现在官方 `run_random_rollouts`（随机动作演示防抖动），**不是** policy eval。

---

### 2. HybridMobileBase：底盘始终在动作空间

`HybridMobileBase` 始终带 base 分片 + 末维 `base_mode`；`base_mode` 只决定臂目标相对「期望/已实现」姿态更新，**不是**关底盘开关。

---

### 3. 榜单 / RoboCasa365：也是全 12D

| 栈 | 证据 |
|---|---|
| 官方 Gym | `deduce_action_space` 含 `base_motion(4)` + `control_mode` |
| GR00T RoboCasa365 | `action.base_motion` + `control_mode`，`_unmap_action` 写入 base/torso/base_mode |
| AlphaBrain 榜单接口 | 显式传 `action.base_motion` / `control_mode` |
| LeRobot 文档 | PandaOmron **12-DOF mobile manipulator**，`Box(..., shape=(12,))` |

---

### 4. 易混点

- **「多数 atomic 演示里底盘几乎不动」** ≠ **「评测关掉了底盘」**。动作空间仍是 12D；策略若输出近零，底盘只是**事实上少动**，硬件/控制器仍可控。
- **RLinf** 另说：`ROBOCASA_DEFAULT_ACTION` 末维 `base_mode=-1`，且可选 `action_space=7d` 只填臂、底盘用默认。那是 RLinf 填充逻辑，**不是** LeRobot `smolvla_robocasa` 评测；后者策略直接出完整 12D。

