"""Define poorly designed functional programming data structures"""

from typing import TypeVar, Generic

A = TypeVar('A')
B = TypeVar('B')


class Option(Generic[A]):
    """Class containing optional value"""
    value: A
    isDefined: bool

    def __repr__(self):
        return self.displayed()

    def __str__(self):
        return self.displayed()

    def displayed(self):
        """Serialize this class instance into a human-readable debugging format"""
        if self.isDefined:
            return f"Some({self.value})"
        else:
            return "None"

    @classmethod
    def as_none(cls) -> 'Option[A]':
        """Construct an Option instance of None i.e. containing no value"""
        c = cls()
        c.value = None  # type: ignore
        c.isDefined = False
        return c

    @classmethod
    def as_some(cls, value: A) -> 'Option[A]':
        """Construct an Option instance of Some i.e. containing some value"""
        c = cls()
        c.value = value
        c.isDefined = True
        return c


# Can this class accidentally represent both Right and Left at the same time?
# Yes. Can I fix it? Maybe. Will I? Most likely not.
class Either(Generic[A, B]):
    """Class containing either value A xor value B"""
    left: A
    isLeft: bool
    right: B
    isRight: bool

    def __repr__(self):
        return self.displayed()

    def __str__(self):
        return self.displayed()

    def displayed(self):
        """Serialize this class instance into a human-readable debugging format"""
        if self.isLeft:
            return f"Left({self.left})"
        elif self.isRight:
            return f"Right({self.right})"
        else:
            return "Either::neither"

    @classmethod
    def as_right(cls, value: B) -> 'Either[A, B]':
        """Construct an Either of Right i.e. containing a desired value"""
        c = cls()
        c.left = None  # type: ignore
        c.isLeft = False
        c.right = value
        c.isRight = True
        return c

    @classmethod
    def as_left(cls, value: A) -> 'Either[A, B]':
        """Construct an Either of Left i.e. containing an undesired value"""
        c = cls()
        c.left = value
        c.isLeft = True
        c.right = None  # type: ignore
        c.isRight = False
        return c
