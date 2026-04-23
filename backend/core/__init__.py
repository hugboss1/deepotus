"""$DEEPOTUS backend core package.

Central infrastructure: configuration, DB handle, security helpers,
Pydantic models, transactional email service.

Modular backend layout:
    core/            -> infrastructure, shared by all routers
    routers/         -> domain-scoped FastAPI routers
    server.py        -> ASGI entrypoint (FastAPI factory + lifecycle)
"""
