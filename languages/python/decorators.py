#!/usr/bin/env python3

from functools import wraps

"""
Demonstrates usage of decorators.
"""


def wrappy(who):
    """
    A decorator with parameters works _DIFFERENTLY_ than non-parametrized decorators.
    With parameters, the deorator is called _twice_:
        - first call with the parameters ("who", above).
          it should _then_ return the "inner decorator", which is then called ...
        - ... with the function-to-be-decorated.
          on _that_ call it should return the "final" wrapped function.
    """

    def inner_decorator(fn):
        @wraps(fn)
        def inner(*args):
            print(f'I am wrap({who}), calling inner("{who}", *args) ...')
            return fn(who, *args)

        return inner

    return inner_decorator


@wrappy("one")
@wrappy("two")
def printy(*args):
    print("I got this:")
    for idx, arg in enumerate(args):
        print(f"  - arg {idx:02d}: {arg}")


def wrap_one(fn):
    """
    A "simple" (non-parameterized) decorator is called once, and it is assumed
    it returns the wrapped function. It basicalls starts at "step 2" of the
    parameterized decorator.
    """

    @wraps(fn)
    def inner(*args):
        print('I am wrap_one, calling inner("one", *args) ...')
        return fn("one", *args)

    return inner


def wrap_two(fn):
    @wraps(fn)
    def inner(*args):
        print('I am wrap_two, calling inner("two", *args) ...')
        return fn("two", *args)

    return inner


@wrap_one
@wrap_two
def schminty(*args):
    print("I got this:")
    for idx, arg in enumerate(args):
        print(f"  - arg {idx:02d}: {arg}")


if __name__ == "__main__":
    print("PRINTY")
    printy("let's see ...")
    print("\n\nSCHMINTY")
    schminty("let's see ...")
