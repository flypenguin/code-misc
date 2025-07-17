# syntax=docker/dockerfile:1

## SOME NOTES:
##   - We do NOT need an entrypoint -- this is done via the helm chart.
##   - The app is under /app, the venv is situated at /app/.venv
##   - That's it.

ARG PYTHON_BASE="3.12"


## inspired by ...
##    - https://docs.astral.sh/uv/guides/integration/docker/
##    - https://hynek.me/articles/docker-uv/

FROM ghcr.io/astral-sh/uv:python${PYTHON_BASE}-bookworm-slim as builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN mkdir /app

ENV \
    PYTHON_BASE=${PYTHON_BASE} \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app \
    UV_PYTHON=/usr/local/bin/python${PYTHON_BASE} \
    UV_PYTHON_DOWNLOADS=never

# this WILL ...
#    ... create /app and /app/.venv based on the information in pyproject.toml
# note that this will NOT ...
#    ... install a python interpreter
#    ... sync the application itself
# ISSUES:
#    - on mac, we run into this: https://github.com/containers/podman/issues/26020
#      SOLUTION: the comment here: https://github.com/containers/podman/issues/26020#issuecomment-2841447293
#      (add the "relabel= ..." flag, whatever this is)
#    - in python:bookworm, the python executable is in /usr/local/bin. we need to add that
#      to the PATH.
RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=./uv.lock,target=/uv.lock,relabel=shared \
    --mount=type=bind,source=./pyproject.toml,target=/pyproject.toml,relabel=shared \
    echo UV_PYTHON=$UV_PYTHON                                       && \
    uv sync \
    --locked \
    --no-dev \
    --no-install-project

    # Now install the rest from `/src`: The APPLICATION w/o dependencies.
    # `/src` will NOT be copied into the runtime container.
    # LEAVE THIS OUT if your application is NOT a proper Python package.
    COPY ./ /src
    WORKDIR /src
    RUN --mount=type=cache,target=/root/.cache \
    uv sync \
        --locked \
        --no-dev \
        --no-editable


# =================================================================================================


FROM python:${PYTHON_BASE}-bookworm

# Optional: add the application virtualenv to search path.
ENV PATH=/app/bin:$PATH

RUN env | grep PY

RUN <<EOT
groupadd -r app
useradd -r -d /app -g app -N app
EOT

STOPSIGNAL SIGINT

COPY --from=builder --chown=app:app /app /app

# If your application is NOT a proper Python package that got
# pip-installed above, you need to copy your application into
# the container HERE:
# COPY . /app/whereever-your-entrypoint-finds-it

USER app
WORKDIR /app

# Strictly optional, but I like it for introspection of what I've built
# and run a smoke test that the application can, in fact, be imported.
RUN <<EOT
python -V
python -Im site
#python -Ic 'import the_app'
EOT
