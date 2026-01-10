import os


def get_app_root():
    """Return the Flask application's root path when available.

    If called outside a Flask application context (for example from a GNURadio
    embedded block), fall back to the project directory containing this file.
    """
    try:
        # import inside the function so importing this module doesn't
        # require Flask or an application context.
        from flask import current_app
        return current_app.root_path
    except Exception:
        return os.path.abspath(os.path.dirname(__file__))


def app_path(*parts):
    """Return a path under the application/project root joined with *parts.

    Works both when called inside Flask (uses `current_app.root_path`) and
    when called from standalone code (uses the project folder).
    """
    return os.path.join(get_app_root(), *parts)


def resolve_storage_path(base_path, *parts):
    """Resolve a storage path that may be absolute, use tilde (~), or be
    relative to the application root.

    - If `base_path` is absolute after expanding `~`, it is used as-is.
    - Otherwise it is interpreted relative to the app/project root.
    Returns an absolute, normalized path.
    """
    if base_path is None:
        base_path = ""

    # Expand ~ and environment variables
    base_path = os.path.expanduser(os.path.expandvars(base_path))

    if os.path.isabs(base_path):
        joined = os.path.join(base_path, *parts)
    else:
        joined = os.path.join(get_app_root(), base_path, *parts)
    return os.path.abspath(joined)
