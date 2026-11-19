from sales_dashboard.metrics import conversion_rate, pooled_conversion_rate


def test_conversion_rate_basic():
    assert conversion_rate([{"converted": True}, {"converted": False}]) == 0.5


def test_pooled_conversion_rate_equal_groups():
    groups = {"a": [{"converted": True}, {"converted": False}], "b": [{"converted": True}, {"converted": False}]}
    assert pooled_conversion_rate(groups) == 0.5
