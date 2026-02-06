"""
Balance engine: orchestrator for balance computation.

No DB access. No loops. Only coordinates strategy execution.
"""

from app.engines.balance.strategy import BalanceStrategy


class BalanceEngine:
    """
    Engine for balance computation.

    Stateless orchestrator. Delegates all work to strategies.
    Does not query the DB, loop over accounts, or loop over dates.
    """

    def calculate(self, strategy: BalanceStrategy) -> object:
        """
        Execute the given strategy and return its result.

        Args:
            strategy: A strategy that batch-loads data and computes the result.

        Returns:
            The result of strategy.execute().
        """
        return strategy.execute()
