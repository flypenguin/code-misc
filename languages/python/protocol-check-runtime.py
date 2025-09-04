from typing import Protocol, runtime_checkable

"""
Very simple example.
"""


@runtime_checkable
class ForReal(Protocol):
    def x(self, arg: int) -> str: ...
    def y(self, arg: int) -> str: ...


class Thing:
    def x(self, arg: int) -> str:
        return f"oh what an int, oh what a number ... ({arg})"


class Thang(Thing):
    def y(self, arg: int) -> str:
        return f"nope, don't like {arg}"


if __name__ == "__main__":
    # should return <False>
    print("is Thing for real? :)  -->  ", isinstance(Thing, ForReal))

    # should return <True>
    print("is Thang for real? :)  -->  ", isinstance(Thang, ForReal))
