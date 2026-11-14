"""Framework layer: platform plumbing that users rarely modify.

Includes the data contract (types), configuration (config), runtime loop
(runtime), SDK wrapper (robot_backend), ROS data source (ros_source),
GameController decoder (game_codec), and agent entry-point mixin (agent).

Import directly from submodules as needed, for example
``from .framework.types import Context``. This module avoids eager imports so
SDK-dependent modules do not break imports on development machines without it.
"""
