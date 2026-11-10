"""Helper: run a web test class against the previous (v0.37.0) web ruleset.

The web default is ``GameConfig.v038c()`` (v0.38.0). Older web tests describe v0.36 / v0.37 behaviour (colour shields,
Glitched Box, Market Leader Bonus at game end only), so they opt in to the legacy ruleset with ``@use_v037_rules``.
"""

from __future__ import annotations

from unittest import mock


def use_v037_rules(cls):
    orig = cls.__dict__.get("setUpClass")

    def setUpClass(klass):  # noqa: N802
        patcher = mock.patch("web.controller.core.WEB_DEFAULT_RULES_VERSION", "v0.37.0")
        patcher.start()
        klass.addClassCleanup(patcher.stop)
        if orig is not None:
            orig.__func__(klass)

    cls.setUpClass = classmethod(setUpClass)
    return cls
