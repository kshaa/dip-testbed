"""Synchronization primitive for coroutine-safe process finishing"""


class Death:
    """Coroutine-safe application death boolean"""
    gracing: bool = False

    def grace(self):
        self.gracing = True
