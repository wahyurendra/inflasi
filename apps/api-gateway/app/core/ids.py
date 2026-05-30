"""Shared CUID2 generator for string primary keys (users, reports, notifications…).

`cuid2.cuid_wrapper()` returns a *generator function*, not an id — you must call
its result to get a string. Passing the function object straight into a column
fails at INSERT ("expected str, got function"). Wrapping it once here removes that
foot-gun and gives every table the same id scheme.
"""

import cuid2

_generate = cuid2.cuid_wrapper()


def new_id() -> str:
    """Return a fresh CUID2 string id."""
    return _generate()
