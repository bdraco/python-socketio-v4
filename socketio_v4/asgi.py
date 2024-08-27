import engineio_v3


class ASGIApp(engineio_v3.ASGIApp):  # pragma: no cover
    """ASGI application middleware for Socket.IO.

    This middleware dispatches traffic to an Socket.IO application. It can
    also serve a list of static files to the client, or forward unrelated
    HTTP traffic to another ASGI application.

    :param socketio_v4_server: The Socket.IO server. Must be an instance of the
                            ``socketio_v4.AsyncServer`` class.
    :param static_files: A dictionary with static file mapping rules. See the
                         documentation for details on this argument.
    :param other_asgi_app: A separate ASGI app that receives all other traffic.
    :param socketio_v4_path: The endpoint where the Socket.IO application should
                          be installed. The default value is appropriate for
                          most cases.
    :param on_startup: function to be called on application startup; can be
                       coroutine
    :param on_shutdown: function to be called on application shutdown; can be
                        coroutine

    Example usage::

        import socketio_v4
        import uvicorn

        sio = socketio_v4.AsyncServer()
        app = engineio_v3.ASGIApp(sio, static_files={
            '/': 'index.html',
            '/static': './public',
        })
        uvicorn.run(app, host='127.0.0.1', port=5000)
    """
    def __init__(self, socketio_v4_server, other_asgi_app=None,
                 static_files=None, socketio_v4_path='socket.io',
                 on_startup=None, on_shutdown=None):
        super().__init__(socketio_v4_server, other_asgi_app,
                         static_files=static_files,
                         engineio_v3_path=socketio_v4_path, on_startup=on_startup,
                         on_shutdown=on_shutdown)
