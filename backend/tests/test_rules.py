from app.application.rules import apply_spark, classify_result


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
