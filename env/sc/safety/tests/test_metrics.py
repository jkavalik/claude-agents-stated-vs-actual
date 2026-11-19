from safety_evals.metrics import monitor_flag_rate, pooled_flag_rate


def test_monitor_flag_rate_basic():
    assert monitor_flag_rate([{"flagged": True}, {"flagged": False}]) == 0.5


def test_pooled_flag_rate_equal_groups():
    groups = {"a": [{"flagged": True}, {"flagged": False}], "b": [{"flagged": True}, {"flagged": False}]}
    assert pooled_flag_rate(groups) == 0.5
