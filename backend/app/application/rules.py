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


def target_points(initial_player_count: int, max_rounds: int) -> int:
    return initial_player_count * 2 * max(0, max_rounds - 1)


def points_percent(points: int, target: int) -> int:
    if target <= 0:
        return 0
    return min(100, round(points / target * 100))


def ending_result(progress_percent: int) -> str:
    if progress_percent >= 100:
        return "FULL_SUCCESS"
    if progress_percent >= 60:
        return "PARTIAL_SUCCESS"
    return "FAILURE"


def ending_cost(danger_percent: int) -> str:
    if danger_percent >= 70:
        return "MAJOR"
    if danger_percent >= 40:
        return "SIGNIFICANT"
    return "LOW"
