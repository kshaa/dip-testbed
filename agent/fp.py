from typing import TypeVar, Generic

# Is this good for performance?
# No. But if I cared about performance, I would've written Rust.

A = TypeVar('A')
B = TypeVar('B')


class Option(Generic[A]):
    value: A
    isDefined: bool

    def __repr__(self):
        return self.displayed()

    def __str__(self):
        return self.displayed()

    def displayed(self):
        if self.isDefined:
            return f"Some({self.value})"
        else:
            return f"None"

    @classmethod
    def as_none(cls) -> 'Option[A]':
        c = cls()
        c.value = None  # type: ignore
        c.isDefined = False
        return c

    @classmethod
    def as_some(cls, value: A) -> 'Option[A]':
        c = cls()
        c.value = value
        c.isDefined = True
        return c


# Can this class accidentally represent both Right and Left at the same time?
# Yes. Can I fix it? Maybe. Will I? Most likely not.
class Either(Generic[A, B]):
    left: A
    isLeft: bool
    right: B
    isRight: bool

    def __repr__(self):
        return self.displayed()

    def __str__(self):
        return self.displayed()

    def displayed(self):
        if self.isLeft:
            return f"Left({self.left})"
        elif self.isRight:
            return f"Right({self.right})"
        else:
            return f"Either::neither"

    @classmethod
    def as_right(cls, value: B) -> 'Either[A, B]':
        c = cls()
        c.left = None  # type: ignore
        c.isLeft = False
        c.right = value
        c.isRight = True
        return c

    @classmethod
    def as_left(cls, value: A) -> 'Either[A, B]':
        c = cls()
        c.left = value
        c.isLeft = True
        c.right = None  # type: ignore
        c.isRight = False
        return c
