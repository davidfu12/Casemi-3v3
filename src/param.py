"""Central configuration point for strategy tuning.

This module contains tunable strategy, movement, kicking, and obstacle
avoidance parameters. Existing values were moved here from their original
modules; make future parameter adjustments here first.
"""

from __future__ import annotations

import math


# ======================================================================
# Kick power
# ======================================================================

# Player.kick() clamps power to this range. Unsupported values may cause a fall.
#
# 协议允许 1.0~10.0，但"能发出去"不等于"不摔"。裁判的 INCAPABLE_ROBOT 是
# 摔倒后连续 10 s 起不来（referee: FALLEN_DURATION_MS=10000），踢球与急转是
# 我们能主动控制的摔倒来源，所以软件上限压到 4.0，正常传球用 3.5。
# 改前 5.0 / 上限 10.0，依据见 reports/B-20261112-判罚抑制.md。
KICK_POWER_PROTOCOL_MAX = 10.0   # 协议上限，仅作记录，不参与计算
KICK_POWER_MIN = 1.0
KICK_POWER_MAX = 4.0             # 软件安全上限：再高容易失去平衡

# Kick power during normal play.
KICK_POWER_DEFAULT = 3.5
KICK_POWER_BACKFIELD = 3.5       # 后场解围：宁短勿摔
KICK_POWER_OUR_KICKOFF = 3.0     # 开球轻推即可


# ======================================================================
# Player movement control
# ======================================================================

ARRIVE_DIST = 0.15             # Target arrival threshold (m)
OMNI_DIST = 1.0                # Use omnidirectional control below this distance
TURN_THRESHOLD = 0.5           # Turn in place above this heading error (rad)
# 速度上限同时是"摔倒风险"旋钮：裁判对摔倒的容忍是 10 s（FALLEN_DURATION_MS），
# 一旦起不来就是 INCAPABLE_ROBOT。改前 2.0 / 2.0，实测急转最容易失衡。
MAX_LINEAR = 1.5               # Maximum commanded forward speed (m/s)
MAX_ANGULAR = 1.2              # Maximum commanded angular speed (rad/s)
LINEAR_GAIN = 1.5              # Translation proportional gain
ANGULAR_GAIN = 2.0             # Rotation proportional gain


# ======================================================================
# Player kicking and shot planning
# ======================================================================

KICK_ENTER_M = 2.0             # Enter kicking state below this ball distance
KICK_EXIT_M = 2.5              # Leave kicking state above this ball distance
CHASE_BEHIND_M = 0.35          # Distance behind the ball while chasing


# ======================================================================
# Player skill parameters: guarding and support
# ======================================================================

GUARD_FACE_BALL = True
GUARD_THREAT_ENTER_X = -1.0
GUARD_THREAT_EXIT_X = -0.7

SUPPORT_DIST_M = 3.0

# ======================================================================
# Normal-phase strategy
# ======================================================================

ATTACKER_KEEP_DIST_MARGIN_M = 0.3  # Prevent attacker-selection oscillation

FALLEN_COST = 10.0  # Distance penalty assigned to a fallen player (m)


# ======================================================================
# Kickoff and set-play strategy
# ======================================================================

# Kickoff
KICKOFF_STAGE_M = 2.0
KICKOFF_FRONT_MARGIN = 0.1
KICKOFF_LATERAL_TOL = 0.35

CENTER_LEAVE_DIST_M = 0.15 # Distance from center at which the ball counts as moved

OPP_SET_WALL_DIST_M = 2.0 # Blocking distance during an opponent kickoff


# ======================================================================
# Positioning and avoidance
# ======================================================================

OPPONENT_RESTART_AVOID_M = 1.65
CIRCLE_MARGIN_M = 0.3

# ---- 场地边界（裁判口径） -------------------------------------------------
# referee/rule_model.py:
#   POSITION_TOLERANCE = 0.05   → 出界/越位判定的容差只有 5 cm
#   LEAVING_FIELD_MARGIN = 2.5  → 出界判罚要 2.5 m 外才触发（且默认规则被禁用）
# 所以"贴着边线跑"本身不吃判罚，但会让我们丢球/卡死；统一留 0.3 m 余量，
# 既不牺牲覆盖范围，也保证任何目标点都不会把机器人送出边线。
FIELD_MARGIN_M = 0.3

# ---- 定位球/开球避让（裁判口径） -----------------------------------------
# referee/robot_rules.py:
#   free_kick_avoidance_radius = field.circle_radius - 0.05 = 1.45 m
#     → 对方定位球开球瞬间，非开球方每台机器人离球必须 ≥ 1.45 m，
#       否则 ILLEGAL_POSITIONING（我们 event log 里唯一真实踩到的判罚）。
#   开球时非开球方还必须在中圈外（circle_radius + 0.05 = 1.55 m）且在本方半场。
# 我们一律按"裁判阈值 + 0.2 m 余量"执行，避免真值抖动把 1.46 m 判成 1.44 m。
RESTART_CLEARANCE_M = 1.65          # 对方定位球：全员离球至少这么远
KICKOFF_CLEARANCE_M = 1.95          # 对方开球：离中圈圆心至少这么远（1.55+0.4）
RESTART_HOLD_FAR_GOAL_M = 1.0       # 站位被挤到本方球门线时至少留这么多
# walk_to 的到达阈值是 0.15 m（ARRIVE_DIST），目标点就设在阈值上会导致
# "停在 1.80 m"而不是 1.95 m。所以目标多给 0.2 m，收脚后仍在 clearance 之外。
RESTART_HOLD_OVERSHOOT_M = 0.2

# ---- 犯规纪律分区（不是"零犯规"，是"前场零无谓犯规"） ---------------------
# 需求：允许必要的战术犯规，但前场不要无谓犯规。落地成三段：
#   1) 前场（x >= 0，对方半场）：对方定位球时全员退到 1.65 m 外，一个人都不压
#      ——这里的犯规最没用（对方本来就在自己半场摆球），纯送 30 s 少一人。
#   2) 后场（x < 0）：门将 + 最近一人"贴线合法压迫"（站到 1.65 m 边缘准备
#      抢第二点），保留防守强度，但仍在裁判阈值 1.45 m 之外。
#   3) 已经被判罚过的机器人，20 s 内额外多退 0.2 m（防连续踩同一个坑）。
FOUL_STRICT_ZONE_X_M = 0.0          # x >= 该值 = 前场，执行零无谓犯规
FOUL_CAUTION_AFTER_PENALTY_SEC = 20.0  # 被判罚后保守多少秒
FOUL_CAUTION_EXTRA_M = 0.2          # 保守期内额外退让距离


# ======================================================================
# Kick-target geometry
# ======================================================================

GOAL_TARGET_DEPTH_M = 0.25              # Kick target depth inside the goal (m)

# ======================================================================
# Obstacle geometry
# ======================================================================

BALL_OBSTACLE_RADIUS = 0.5              # Ball obstacle radius (m)
# 对手机器人按"身体半径 + 推挤余量"建模：0.55 只够擦身而过，
# 实际两台 K1 躯干投影约 0.3 m 半径 + 手臂摆动，取 0.65 才能把 PUSHING/互撞
# （以及互撞导致的摔倒 → INCAPABLE_ROBOT）压下去。
OPPONENT_RADIUS = 0.65                  # Opponent robot radius (m)
TEAMMATE_RADIUS = 0.58                  # Teammate robot radius (m)
SAFETY_MARGIN = 0.22                    # General safety margin (m)

GOAL_DEPTH = 0.6                        # Goal depth used for obstacle modeling (m)
POST_RADIUS = 0.18                      # Goal-post radius (m)
NET_RADIUS = 0.20                       # Goal-net sample radius (m)
NET_STEP = 0.35                         # Goal-net sampling interval (m)

START_IGNORE = 0.0                      # Ignore obstacles near the start (m)
TARGET_IGNORE = 0.0                     # Ignore obstacles near the target (m)

# ======================================================================
# Global path planner (A* grid planner)
# ======================================================================

USE_GLOBAL_PATH_PLANNER = True          # Fall back to local VFH when disabled
GLOBAL_GRID_RESOLUTION_M = 0.35         # Grid cell size; smaller is finer (m)
GLOBAL_FIELD_MARGIN_M = 0.25            # Extra field margin for boundary paths (m)
GLOBAL_OBSTACLE_MARGIN_M = 0.10         # Additional obstacle inflation radius (m)
GLOBAL_PATH_LOOKAHEAD_M = 0.9           # Lookahead distance along the path (m)

# ======================================================================
# Local path planner (VFH direction scan)
# ======================================================================

PLAN_LOOKAHEAD = 1.2                    # Forward probe length (m)
PLAN_CLEARANCE = 0.35                   # Minimum clearance for a candidate (m)
PLAN_STEP = math.radians(15)            # Candidate direction scan step (rad)
PLAN_MAX_OFFSET = math.radians(100)     # Maximum offset from target heading (rad)

# ======================================================================
# Visualization
# ======================================================================

KICK_TARGET_MARK_SIZE_M = 0.18
