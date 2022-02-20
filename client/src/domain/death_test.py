import asyncio
import unittest
from unittest import IsolatedAsyncioTestCase
from result import Ok, Err

from src.domain.death import Death


class TestDeath(IsolatedAsyncioTestCase):
    """Test suite for death"""

    @staticmethod
    async def slow_integer_computation() -> int:
        await asyncio.sleep(0.3)
        return 42

    async def test_death_or_task(self):
        """Test JSON can be parsed and serialized"""
        death = Death()

        # Task wins
        computation_result = await death.or_awaitable(TestDeath.slow_integer_computation())
        self.assertEqual(computation_result, Ok(42))

        # Death wins
        death_task = death.or_awaitable(TestDeath.slow_integer_computation())
        death.grace()
        death_result = await death_task
        self.assertEqual(death_result, Err(death))


if __name__ == '__main__':
    unittest.main()
