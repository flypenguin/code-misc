#!/usr/bin/env python3

from environs import Env

if __name__ == "__main__":
    env = Env()
    env.read_env()

    print(env.str("FROM_DEFAULT", "this is the default value, yaaay"))
    print(env.str("FROM_FILE", "(file) you should not see this"))
    print(env.str("FROM_ENV", "(env) you should not see this"))
