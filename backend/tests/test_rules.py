from app.application.rules import (
    apply_spark,
    classify_result,
    ending_cost,
    ending_result,
    points_percent,
    target_points,
)


def test_result_thresholds() -> None:
    assert classify_result(6).result == "FAILURE"
    assert classify_result(7).result == "PARTIAL_SUCCESS"
    assert classify_result(9).result == "PARTIAL_SUCCESS"
    assert classify_result(10).result == "SUCCESS"


def test_spark_can_upgrade_or_preserve_result() -> None:
    assert apply_spark(6, True)[1].result == "PARTIAL_SUCCESS"
    assert apply_spark(9, True)[1].result == "SUCCESS"
    assert apply_spark(5, True)[1].result == "FAILURE"
    assert apply_spark(9, False) == (9, classify_result(9))


def test_target_points_supports_every_allowed_game_length() -> None:
    assert target_points(3, 4) == 18
    assert target_points(3, 6) == 30
    assert target_points(3, 8) == 42
    assert target_points(5, 4) == 30


def test_point_percent_rounds_for_display_and_caps_at_100() -> None:
    assert points_percent(0, 18) == 0
    assert points_percent(11, 18) == 61
    assert points_percent(18, 18) == 100
    assert points_percent(20, 18) == 100
    assert points_percent(10, 0) == 0


def test_ending_result_uses_60_and_100_percent_boundaries() -> None:
    assert ending_result(59) == "FAILURE"
    assert ending_result(60) == "PARTIAL_SUCCESS"
    assert ending_result(99) == "PARTIAL_SUCCESS"
    assert ending_result(100) == "FULL_SUCCESS"


def test_ending_cost_uses_40_and_70_percent_boundaries() -> None:
    assert ending_cost(39) == "LOW"
    assert ending_cost(40) == "SIGNIFICANT"
    assert ending_cost(69) == "SIGNIFICANT"
    assert ending_cost(70) == "MAJOR"
