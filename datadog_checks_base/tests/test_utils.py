# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from decimal import ROUND_HALF_DOWN, ROUND_HALF_UP

from datadog_checks.utils.common import pattern_filter, round_value
from datadog_checks.utils.limiter import Limiter


class Item:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return self.name == other.name


class TestPatternFilter:
    def test_no_items(self):
        items = []
        whitelist = ['mock']

        assert pattern_filter(items, whitelist=whitelist) == []

    def test_no_patterns(self):
        items = ['mock']

        assert pattern_filter(items) is items

    def test_multiple_matches_whitelist(self):
        items = ['abc', 'def', 'abcdef', 'ghi']
        whitelist = ['abc', 'def']

        assert pattern_filter(items, whitelist=whitelist) == ['abc', 'def', 'abcdef']

    def test_multiple_matches_blacklist(self):
        items = ['abc', 'def', 'abcdef', 'ghi']
        blacklist = ['abc', 'def']

        assert pattern_filter(items, blacklist=blacklist) == ['ghi']

    def test_whitelist_blacklist(self):
        items = ['abc', 'def', 'abcdef', 'ghi']
        whitelist = ['def']
        blacklist = ['abc']

        assert pattern_filter(items, whitelist=whitelist, blacklist=blacklist) == ['def']

    def test_key_function(self):
        items = [Item('abc'), Item('def'), Item('abcdef'), Item('ghi')]
        whitelist = ['abc', 'def']

        assert pattern_filter(items, whitelist=whitelist, key=lambda item: item.name) == [
            Item('abc'), Item('def'), Item('abcdef')
        ]


class TestLimiter():
    def test_no_uid(self):
        warnings = []
        limiter = Limiter("my_check", "names", 10, warning_func=warnings.append)
        for i in range(0, 10):
            assert limiter.is_reached() is False
        assert limiter.get_status() == (10, 10, False)

        # Reach limit
        assert limiter.is_reached() is True
        assert limiter.get_status() == (11, 10, True)
        assert warnings == ["Check my_check exceeded limit of 10 names, ignoring next ones"]

        # Make sure warning is only sent once
        assert limiter.is_reached() is True
        assert len(warnings) == 1

    def test_with_uid(self):
        warnings = []
        limiter = Limiter("my_check", "names", 10, warning_func=warnings.append)
        for i in range(0, 20):
            assert limiter.is_reached("dummy1") is False
        assert limiter.get_status() == (1, 10, False)

        for i in range(0, 20):
            assert limiter.is_reached("dummy2") is False
        assert limiter.get_status() == (2, 10, False)
        assert len(warnings) == 0

    def test_mixed(self):
        limiter = Limiter("my_check", "names", 10)

        for i in range(0, 20):
            assert limiter.is_reached("dummy1") is False
        assert limiter.get_status() == (1, 10, False)

        for i in range(0, 5):
            assert limiter.is_reached() is False
        assert limiter.get_status() == (6, 10, False)

    def test_reset(self):
        limiter = Limiter("my_check", "names", 10)

        for i in range(1, 20):
            limiter.is_reached("dummy1")
        assert limiter.get_status() == (1, 10, False)

        limiter.reset()
        assert limiter.get_status() == (0, 10, False)
        assert limiter.is_reached("dummy1") is False
        assert limiter.get_status() == (1, 10, False)


class TestRounding():
    def test_round_half_up(self):
        assert round_value(2.555) == 2.560

    def test_round_modify_method(self):
        assert round_value(3.5, sig_digits="1", rounding_method=ROUND_HALF_DOWN) == 3.0

    def test_round_modify_sig_digits(self):
        assert round_value(3.5, sig_digits="1") == 4.0
        assert round_value(2.555, sig_digits="0.01") == 2.560
        assert round_value(4.2345, sig_digits="0.01") == 4.23
        assert round_value(4.2345, sig_digits="0.001", rounding_method=ROUND_HALF_UP) == 4.2350
