"""
Balance strategies: data-loading and computation patterns.

Each strategy batch-loads all required data in O(1) queries,
then computes results in memory. No DB calls inside loops.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class BalanceStrategy(Protocol):
    """
    Protocol for balance computation strategies.

    Strategies own their data-loading patterns and must not call other strategies.
    All required data is batch-loaded once per request.
    """

    def execute(self) -> object:
        """
        Load data, compute balance result, return.

        Must not perform DB calls inside loops.
        """
        ...
