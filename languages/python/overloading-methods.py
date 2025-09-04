from functools import singledispatchmethod


class Thing:
    @singledispatchmethod
    def x(self, my_arg: int | str) -> str:
        i_got = f"'{my_arg}'" if isinstance(my_arg, str) else my_arg
        return f"I'm the base method, and i got ... -> {i_got} (type: {type(my_arg)})"

    @x.register
    def _(self, my_int: int) -> str:
        rv = Thing.x(self, my_int)
        return f"{rv}\n-> INTermediate python ;)\n"

    @x.register
    def _(self, my_str: str) -> str:
        # you _CAN_ call the "original" method, but you do not _HAVE_ to.
        # purely optional, in case you want to use common code.
        rv = Thing.x(self, my_str)
        return f"{rv}\n-> STRong python skills!! 🦾 ;)\n"


if __name__ == "__main__":
    thing = Thing()
    print(thing.x("a-ha"))
    print(thing.x(42))

    # NOTE: this will work, it just won't use one of the overloaded
    # methods.
    print(thing.x([1, 2]))
