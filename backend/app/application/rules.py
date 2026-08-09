from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Outcome:
    result: str
    progress_delta: int
    danger_delta: int


def classify_result(total: int) -> Outcome:
    if total >= 10:
        return Outcome("SUCCESS", progress_delta=2, danger_delta=0)
    if total >= 7:
        return Outcome("PARTIAL_SUCCESS", progress_delta=1, danger_delta=1)
    return Outcome("FAILURE", progress_delta=0, danger_delta=2)


def apply_spark(base_total: int, use_spark: bool) -> tuple[int, Outcome]:
    final_total = base_total + (1 if use_spark else 0)
    return final_total, classify_result(final_total)
