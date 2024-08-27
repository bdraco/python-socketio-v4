#!/usr/bin/env python
import uvicorn

import socketio_v4

sio = socketio_v4.AsyncServer(async_mode='asgi')
app = socketio_v4.ASGIApp(sio, static_files={
    '/': 'latency.html',
    '/static': 'static',
})


@sio.event
async def ping_from_client(sid):
    await sio.emit('pong_from_server', room=sid)


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=5000)
