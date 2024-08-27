import sys
if sys.version_info >= (3, 5):
    try:
        from engineio_v3.async_drivers.tornado import get_tornado_handler as \
            get_engineio_v3_handler
    except ImportError:  # pragma: no cover
        get_engineio_v3_handler = None


def get_tornado_handler(socketio_v4_server):  # pragma: no cover
    return get_engineio_v3_handler(socketio_v4_server.eio)
