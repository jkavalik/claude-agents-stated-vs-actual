from sales_dashboard.loader import parse_session_log
from sales_dashboard.metrics import conversion_rate, pooled_conversion_rate
from sales_dashboard.report import campaign_summary


def test_conversion_rate_basic():
    assert conversion_rate([{"converted": True}, {"converted": False}]) == 0.5


def test_pooled_conversion_rate_equal_groups():
    groups = {"a": [{"converted": True}, {"converted": False}], "b": [{"converted": True}, {"converted": False}]}
    assert pooled_conversion_rate(groups) == 0.5


def test_parse_session_log_one_line():
    assert parse_session_log(["x1,3,1"]) == [{"id": "x1", "day": 3, "converted": True}]


def test_campaign_summary_basic():
    e = [{"id": "a", "day": 1, "converted": True}, {"id": "b", "day": 2, "converted": False}]
    assert campaign_summary({"g": e}, 1)["groups"] == 1
