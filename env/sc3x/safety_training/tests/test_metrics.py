from safety_evals.loader import parse_transcript_log
from safety_evals.metrics import monitor_flag_rate, pooled_flag_rate
from safety_evals.report import monitor_summary


def test_monitor_flag_rate_basic():
    assert monitor_flag_rate([{"flagged": True}, {"flagged": False}]) == 0.5


def test_pooled_flag_rate_equal_groups():
    groups = {"a": [{"flagged": True}, {"flagged": False}], "b": [{"flagged": True}, {"flagged": False}]}
    assert pooled_flag_rate(groups) == 0.5


def test_parse_transcript_log_one_line():
    assert parse_transcript_log(["x1,3,1"]) == [{"id": "x1", "day": 3, "flagged": True}]


def test_monitor_summary_basic():
    e = [{"id": "a", "day": 1, "flagged": True}, {"id": "b", "day": 2, "flagged": False}]
    assert monitor_summary({"g": e}, 1)["groups"] == 1
