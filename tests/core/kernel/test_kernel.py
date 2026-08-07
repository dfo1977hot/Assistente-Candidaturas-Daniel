"""
Tests for ACD Kernel.
"""

from __future__ import annotations

from acd.core.kernel.kernel import Kernel


def test_kernel_creation() -> None:
    """Kernel can be instantiated."""

    kernel = Kernel()

    assert kernel.context is not None
    assert kernel.services is not None
    assert kernel.container is not None
    assert kernel.events is not None
    assert kernel.commands is not None
    assert kernel.queries is not None


def test_kernel_clear() -> None:
    """Kernel.clear() executes successfully."""

    kernel = Kernel()

    kernel.clear()

    assert kernel is not None