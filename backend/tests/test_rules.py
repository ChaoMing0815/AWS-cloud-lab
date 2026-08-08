from app.application.rules import classify_result


def test_result_thresholds() -> None:
    assert classify_result(6).result == "FAILURE"
    assert classify_result(7).result == "PARTIAL_SUCCESS"
    assert classify_result(9).result == "PARTIAL_SUCCESS"
    assert classify_result(10).result == "SUCCESS"
