from enemies.api import EnemySystem


def test_enemy_system_exposes_separate_health_bar_layer() -> None:
    assert hasattr(EnemySystem, "draw")
    assert hasattr(EnemySystem, "draw_health_bars")
