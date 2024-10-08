import asyncio
import sys
import unittest

import six

if six.PY3:
    from unittest import mock
else:
    import mock

from socketio_v4 import asyncio_manager


def AsyncMock(*args, **kwargs):
    """Return a mock asynchronous function."""
    m = mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


def _run(coro):
    """Run the given coroutine."""
    return asyncio.get_event_loop().run_until_complete(coro)


@unittest.skipIf(sys.version_info < (3, 5), 'only for Python 3.5+')
class TestAsyncManager(unittest.TestCase):
    def setUp(self):
        mock_server = mock.MagicMock()
        mock_server._emit_internal = AsyncMock()
        self.bm = asyncio_manager.AsyncManager()
        self.bm.set_server(mock_server)
        self.bm.initialize()

    def test_connect(self):
        self.bm.connect('123', '/foo')
        assert None in self.bm.rooms['/foo']
        assert '123' in self.bm.rooms['/foo']
        assert '123' in self.bm.rooms['/foo'][None]
        assert '123' in self.bm.rooms['/foo']['123']
        assert self.bm.rooms['/foo'] == {
            None: {'123': True},
            '123': {'123': True},
        }

    def test_pre_disconnect(self):
        self.bm.connect('123', '/foo')
        self.bm.connect('456', '/foo')
        self.bm.pre_disconnect('123', '/foo')
        assert self.bm.pending_disconnect == {'/foo': ['123']}
        assert not self.bm.is_connected('123', '/foo')
        self.bm.pre_disconnect('456', '/foo')
        assert self.bm.pending_disconnect == {'/foo': ['123', '456']}
        assert not self.bm.is_connected('456', '/foo')
        self.bm.disconnect('123', '/foo')
        assert self.bm.pending_disconnect == {'/foo': ['456']}
        self.bm.disconnect('456', '/foo')
        assert self.bm.pending_disconnect == {}

    def test_disconnect(self):
        self.bm.connect('123', '/foo')
        self.bm.connect('456', '/foo')
        self.bm.enter_room('123', '/foo', 'bar')
        self.bm.enter_room('456', '/foo', 'baz')
        self.bm.disconnect('123', '/foo')
        assert self.bm.rooms['/foo'] == {
            None: {'456': True},
            '456': {'456': True},
            'baz': {'456': True},
        }

    def test_disconnect_default_namespace(self):
        self.bm.connect('123', '/')
        self.bm.connect('123', '/foo')
        self.bm.connect('456', '/')
        self.bm.connect('456', '/foo')
        assert self.bm.is_connected('123', '/')
        assert self.bm.is_connected('123', '/foo')
        self.bm.disconnect('123', '/')
        assert not self.bm.is_connected('123', '/')
        assert self.bm.is_connected('123', '/foo')
        self.bm.disconnect('123', '/foo')
        assert not self.bm.is_connected('123', '/foo')
        assert self.bm.rooms['/'] == {
            None: {'456': True},
            '456': {'456': True},
        }
        assert self.bm.rooms['/foo'] == {
            None: {'456': True},
            '456': {'456': True},
        }

    def test_disconnect_twice(self):
        self.bm.connect('123', '/')
        self.bm.connect('123', '/foo')
        self.bm.connect('456', '/')
        self.bm.connect('456', '/foo')
        self.bm.disconnect('123', '/')
        self.bm.disconnect('123', '/foo')
        self.bm.disconnect('123', '/')
        self.bm.disconnect('123', '/foo')
        assert self.bm.rooms['/'] == {
            None: {'456': True},
            '456': {'456': True},
        }
        assert self.bm.rooms['/foo'] == {
            None: {'456': True},
            '456': {'456': True},
        }

    def test_disconnect_all(self):
        self.bm.connect('123', '/foo')
        self.bm.connect('456', '/foo')
        self.bm.enter_room('123', '/foo', 'bar')
        self.bm.enter_room('456', '/foo', 'baz')
        self.bm.disconnect('123', '/foo')
        self.bm.disconnect('456', '/foo')
        assert self.bm.rooms == {}

    def test_disconnect_with_callbacks(self):
        self.bm.connect('123', '/')
        self.bm.connect('123', '/foo')
        self.bm._generate_ack_id('123', '/', 'f')
        self.bm._generate_ack_id('123', '/foo', 'g')
        self.bm.disconnect('123', '/foo')
        assert '/foo' not in self.bm.callbacks['123']
        self.bm.disconnect('123', '/')
        assert '123' not in self.bm.callbacks

    def test_trigger_sync_callback(self):
        self.bm.connect('123', '/')
        self.bm.connect('123', '/foo')
        cb = mock.MagicMock()
        id1 = self.bm._generate_ack_id('123', '/', cb)
        id2 = self.bm._generate_ack_id('123', '/foo', cb)
        _run(self.bm.trigger_callback('123', '/', id1, ['foo']))
        _run(self.bm.trigger_callback('123', '/foo', id2, ['bar', 'baz']))
        assert cb.call_count == 2
        cb.assert_any_call('foo')
        cb.assert_any_call('bar', 'baz')

    def test_trigger_async_callback(self):
        self.bm.connect('123', '/')
        self.bm.connect('123', '/foo')
        cb = AsyncMock()
        id1 = self.bm._generate_ack_id('123', '/', cb)
        id2 = self.bm._generate_ack_id('123', '/foo', cb)
        _run(self.bm.trigger_callback('123', '/', id1, ['foo']))
        _run(self.bm.trigger_callback('123', '/foo', id2, ['bar', 'baz']))
        assert cb.mock.call_count == 2
        cb.mock.assert_any_call('foo')
        cb.mock.assert_any_call('bar', 'baz')

    def test_invalid_callback(self):
        self.bm.connect('123', '/')
        cb = mock.MagicMock()
        id = self.bm._generate_ack_id('123', '/', cb)

        # these should not raise an exception
        _run(self.bm.trigger_callback('124', '/', id, ['foo']))
        _run(self.bm.trigger_callback('123', '/foo', id, ['foo']))
        _run(self.bm.trigger_callback('123', '/', id + 1, ['foo']))
        assert cb.mock.call_count == 0

    def test_get_namespaces(self):
        assert list(self.bm.get_namespaces()) == []
        self.bm.connect('123', '/')
        self.bm.connect('123', '/foo')
        namespaces = list(self.bm.get_namespaces())
        assert len(namespaces) == 2
        assert '/' in namespaces
        assert '/foo' in namespaces

    def test_get_participants(self):
        self.bm.connect('123', '/')
        self.bm.connect('456', '/')
        self.bm.connect('789', '/')
        self.bm.disconnect('789', '/')
        assert '789' not in self.bm.rooms['/'][None]
        participants = list(self.bm.get_participants('/', None))
        assert len(participants) == 2
        assert '789' not in participants

    def test_leave_invalid_room(self):
        self.bm.connect('123', '/foo')
        self.bm.leave_room('123', '/foo', 'baz')
        self.bm.leave_room('123', '/bar', 'baz')

    def test_no_room(self):
        rooms = self.bm.get_rooms('123', '/foo')
        assert [] == rooms

    def test_close_room(self):
        self.bm.connect('123', '/foo')
        self.bm.connect('456', '/foo')
        self.bm.connect('789', '/foo')
        self.bm.enter_room('123', '/foo', 'bar')
        self.bm.enter_room('123', '/foo', 'bar')
        _run(self.bm.close_room('bar', '/foo'))
        assert 'bar' not in self.bm.rooms['/foo']

    def test_close_invalid_room(self):
        self.bm.close_room('bar', '/foo')

    def test_rooms(self):
        self.bm.connect('123', '/foo')
        self.bm.enter_room('123', '/foo', 'bar')
        r = self.bm.get_rooms('123', '/foo')
        assert len(r) == 2
        assert '123' in r
        assert 'bar' in r

    def test_emit_to_sid(self):
        self.bm.connect('123', '/foo')
        self.bm.connect('456', '/foo')
        _run(
            self.bm.emit(
                'my event', {'foo': 'bar'}, namespace='/foo', room='123'
            )
        )
        self.bm.server._emit_internal.mock.assert_called_once_with(
            '123', 'my event', {'foo': 'bar'}, '/foo', None
        )

    def test_emit_to_room(self):
        self.bm.connect('123', '/foo')
        self.bm.enter_room('123', '/foo', 'bar')
        self.bm.connect('456', '/foo')
        self.bm.enter_room('456', '/foo', 'bar')
        self.bm.connect('789', '/foo')
        _run(
            self.bm.emit(
                'my event', {'foo': 'bar'}, namespace='/foo', room='bar'
            )
        )
        assert self.bm.server._emit_internal.mock.call_count == 2
        self.bm.server._emit_internal.mock.assert_any_call(
            '123', 'my event', {'foo': 'bar'}, '/foo', None
        )
        self.bm.server._emit_internal.mock.assert_any_call(
            '456', 'my event', {'foo': 'bar'}, '/foo', None
        )

    def test_emit_to_all(self):
        self.bm.connect('123', '/foo')
        self.bm.enter_room('123', '/foo', 'bar')
        self.bm.connect('456', '/foo')
        self.bm.enter_room('456', '/foo', 'bar')
        self.bm.connect('789', '/foo')
        self.bm.connect('abc', '/bar')
        _run(self.bm.emit('my event', {'foo': 'bar'}, namespace='/foo'))
        assert self.bm.server._emit_internal.mock.call_count == 3
        self.bm.server._emit_internal.mock.assert_any_call(
            '123', 'my event', {'foo': 'bar'}, '/foo', None
        )
        self.bm.server._emit_internal.mock.assert_any_call(
            '456', 'my event', {'foo': 'bar'}, '/foo', None
        )
        self.bm.server._emit_internal.mock.assert_any_call(
            '789', 'my event', {'foo': 'bar'}, '/foo', None
        )

    def test_emit_to_all_skip_one(self):
        self.bm.connect('123', '/foo')
        self.bm.enter_room('123', '/foo', 'bar')
        self.bm.connect('456', '/foo')
        self.bm.enter_room('456', '/foo', 'bar')
        self.bm.connect('789', '/foo')
        self.bm.connect('abc', '/bar')
        _run(
            self.bm.emit(
                'my event', {'foo': 'bar'}, namespace='/foo', skip_sid='456'
            )
        )
        assert self.bm.server._emit_internal.mock.call_count == 2
        self.bm.server._emit_internal.mock.assert_any_call(
            '123', 'my event', {'foo': 'bar'}, '/foo', None
        )
        self.bm.server._emit_internal.mock.assert_any_call(
            '789', 'my event', {'foo': 'bar'}, '/foo', None
        )

    def test_emit_to_all_skip_two(self):
        self.bm.connect('123', '/foo')
        self.bm.enter_room('123', '/foo', 'bar')
        self.bm.connect('456', '/foo')
        self.bm.enter_room('456', '/foo', 'bar')
        self.bm.connect('789', '/foo')
        self.bm.connect('abc', '/bar')
        _run(
            self.bm.emit(
                'my event',
                {'foo': 'bar'},
                namespace='/foo',
                skip_sid=['123', '789'],
            )
        )
        assert self.bm.server._emit_internal.mock.call_count == 1
        self.bm.server._emit_internal.mock.assert_any_call(
            '456', 'my event', {'foo': 'bar'}, '/foo', None
        )

    def test_emit_with_callback(self):
        self.bm.connect('123', '/foo')
        self.bm._generate_ack_id = mock.MagicMock()
        self.bm._generate_ack_id.return_value = 11
        _run(
            self.bm.emit(
                'my event', {'foo': 'bar'}, namespace='/foo', callback='cb'
            )
        )
        self.bm._generate_ack_id.assert_called_once_with('123', '/foo', 'cb')
        self.bm.server._emit_internal.mock.assert_called_once_with(
            '123', 'my event', {'foo': 'bar'}, '/foo', 11
        )

    def test_emit_to_invalid_room(self):
        _run(
            self.bm.emit('my event', {'foo': 'bar'}, namespace='/', room='123')
        )

    def test_emit_to_invalid_namespace(self):
        _run(self.bm.emit('my event', {'foo': 'bar'}, namespace='/foo'))
