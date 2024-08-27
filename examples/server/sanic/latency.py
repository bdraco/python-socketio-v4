from sanic import Sanic
from sanic.response import html

import socketio_v4

sio = socketio_v4.AsyncServer(async_mode='sanic')
app = Sanic()
sio.attach(app)


@app.route('/')
def index(request):
    with open('latency.html') as f:
        return html(f.read())


@sio.event
async def ping_from_client(sid):
    await sio.emit('pong_from_server', room=sid)

app.static('/static', './static')


if __name__ == '__main__':
    app.run()
