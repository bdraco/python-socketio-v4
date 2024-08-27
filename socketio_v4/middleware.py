import engineio_v3


class WSGIApp(engineio_v3.WSGIApp):
    """WSGI middleware for Socket.IO.

    This middleware dispatches traffic to a Socket.IO application. It can also
    serve a list of static files to the client, or forward unrelated HTTP
    traffic to another WSGI application.

    :param socketio_v4_app: The Socket.IO server. Must be an instance of the
                         ``socketio_v4.Server`` class.
    :param wsgi_app: The WSGI app that receives all other traffic.
    :param static_files: A dictionary with static file mapping rules. See the
                         documentation for details on this argument.
    :param socketio_v4_path: The endpoint where the Socket.IO application should
                          be installed. The default value is appropriate for
                          most cases.

    Example usage::

        import socketio_v4
        import eventlet
        from . import wsgi_app

        sio = socketio_v4.Server()
        app = socketio_v4.WSGIApp(sio, wsgi_app)
        eventlet.wsgi.server(eventlet.listen(('', 8000)), app)
    """
    def __init__(self, socketio_v4_app, wsgi_app=None, static_files=None,
                 socketio_v4_path='socket.io'):
        super(WSGIApp, self).__init__(socketio_v4_app, wsgi_app,
                                      static_files=static_files,
                                      engineio_v3_path=socketio_v4_path)


class Middleware(WSGIApp):
    """This class has been renamed to WSGIApp and is now deprecated."""
    def __init__(self, socketio_v4_app, wsgi_app=None,
                 socketio_v4_path='socket.io'):
        super(Middleware, self).__init__(socketio_v4_app, wsgi_app,
                                         socketio_v4_path=socketio_v4_path)
