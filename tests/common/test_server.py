import json
import logging
import unittest

import six

if six.PY3:
    from unittest import mock
else:
    import mock

from socketio_v4 import exceptions
from socketio_v4 import namespace
from socketio_v4 import packet
from socketio_v4 import server
import pytest


@mock.patch('engineio_v3.Server')
class TestServer(unittest.TestCase):
    def tearDown(self):
        # restore JSON encoder, in case a test changed it
        packet.Packet.json = json

    def test_create(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(
            client_manager=mgr, binary=True, async_handlers=True, foo='bar'
        )
        s.handle_request({}, None)
        s.handle_request({}, None)
        eio.assert_called_once_with(**{'foo': 'bar', 'async_handlers': False})
        assert s.manager == mgr
        assert s.eio.on.call_count == 3
        assert s.binary
        assert s.async_handlers

    def test_on_event(self, eio):
        s = server.Server()

        @s.on('connect')
        def foo():
            pass

        def bar():
            pass

        s.on('disconnect', bar)
        s.on('disconnect', bar, namespace='/foo')

        assert s.handlers['/']['connect'] == foo
        assert s.handlers['/']['disconnect'] == bar
        assert s.handlers['/foo']['disconnect'] == bar

    def test_event(self, eio):
        s = server.Server()

        @s.event
        def connect():
            pass

        @s.event
        def foo():
            pass

        @s.event()
        def bar():
            pass

        @s.event(namespace='/foo')
        def disconnect():
            pass

        assert s.handlers['/']['connect'] == connect
        assert s.handlers['/']['foo'] == foo
        assert s.handlers['/']['bar'] == bar
        assert s.handlers['/foo']['disconnect'] == disconnect

    def test_emit(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s.emit(
            'my event',
            {'foo': 'bar'},
            to='room',
            skip_sid='123',
            namespace='/foo',
            callback='cb',
        )
        s.manager.emit.assert_called_once_with(
            'my event',
            {'foo': 'bar'},
            '/foo',
            room='room',
            skip_sid='123',
            callback='cb',
        )
        s.emit(
            'my event',
            {'foo': 'bar'},
            room='room',
            skip_sid='123',
            namespace='/foo',
            callback='cb',
        )
        s.manager.emit.assert_called_with(
            'my event',
            {'foo': 'bar'},
            '/foo',
            room='room',
            skip_sid='123',
            callback='cb',
        )

    def test_emit_default_namespace(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s.emit(
            'my event',
            {'foo': 'bar'},
            to='room',
            skip_sid='123',
            callback='cb',
        )
        s.manager.emit.assert_called_once_with(
            'my event',
            {'foo': 'bar'},
            '/',
            room='room',
            skip_sid='123',
            callback='cb',
        )
        s.emit(
            'my event',
            {'foo': 'bar'},
            room='room',
            skip_sid='123',
            callback='cb',
        )
        s.manager.emit.assert_called_with(
            'my event',
            {'foo': 'bar'},
            '/',
            room='room',
            skip_sid='123',
            callback='cb',
        )

    def test_send(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s.send(
            'foo', to='room', skip_sid='123', namespace='/foo', callback='cb'
        )
        s.manager.emit.assert_called_once_with(
            'message',
            'foo',
            '/foo',
            room='room',
            skip_sid='123',
            callback='cb',
        )
        s.send(
            'foo', room='room', skip_sid='123', namespace='/foo', callback='cb'
        )
        s.manager.emit.assert_called_with(
            'message',
            'foo',
            '/foo',
            room='room',
            skip_sid='123',
            callback='cb',
        )

    def test_call(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)

        def fake_event_wait(timeout=None):
            assert timeout == 60
            s.manager.emit.call_args_list[0][1]['callback']('foo', 321)
            return True

        s.eio.create_event.return_value.wait = fake_event_wait
        assert s.call('foo', sid='123') == ('foo', 321)

    def test_call_with_timeout(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)

        def fake_event_wait(timeout=None):
            assert timeout == 12
            return False

        s.eio.create_event.return_value.wait = fake_event_wait
        with pytest.raises(exceptions.TimeoutError):
            s.call('foo', sid='123', timeout=12)

    def test_call_with_broadcast(self, eio):
        s = server.Server()
        with pytest.raises(ValueError):
            s.call('foo')

    def test_call_without_async_handlers(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr, async_handlers=False)
        with pytest.raises(RuntimeError):
            s.call('foo', sid='123', timeout=12)

    def test_enter_room(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s.enter_room('123', 'room', namespace='/foo')
        s.manager.enter_room.assert_called_once_with('123', '/foo', 'room')

    def test_enter_room_default_namespace(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s.enter_room('123', 'room')
        s.manager.enter_room.assert_called_once_with('123', '/', 'room')

    def test_leave_room(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s.leave_room('123', 'room', namespace='/foo')
        s.manager.leave_room.assert_called_once_with('123', '/foo', 'room')

    def test_leave_room_default_namespace(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s.leave_room('123', 'room')
        s.manager.leave_room.assert_called_once_with('123', '/', 'room')

    def test_close_room(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s.close_room('room', namespace='/foo')
        s.manager.close_room.assert_called_once_with('room', '/foo')

    def test_close_room_default_namespace(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s.close_room('room')
        s.manager.close_room.assert_called_once_with('room', '/')

    def test_rooms(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s.rooms('123', namespace='/foo')
        s.manager.get_rooms.assert_called_once_with('123', '/foo')

    def test_rooms_default_namespace(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s.rooms('123')
        s.manager.get_rooms.assert_called_once_with('123', '/')

    def test_handle_request(self, eio):
        s = server.Server()
        s.handle_request('environ', 'start_response')
        s.eio.handle_request.assert_called_once_with(
            'environ', 'start_response'
        )

    def test_emit_internal(self, eio):
        s = server.Server()
        s._emit_internal('123', 'my event', 'my data', namespace='/foo')
        s.eio.send.assert_called_once_with(
            '123', '2/foo,["my event","my data"]', binary=False
        )

    def test_emit_internal_with_tuple(self, eio):
        s = server.Server()
        s._emit_internal('123', 'my event', ('foo', 'bar'), namespace='/foo')
        s.eio.send.assert_called_once_with(
            '123', '2/foo,["my event","foo","bar"]', binary=False
        )

    def test_emit_internal_with_list(self, eio):
        s = server.Server()
        s._emit_internal('123', 'my event', ['foo', 'bar'], namespace='/foo')
        s.eio.send.assert_called_once_with(
            '123', '2/foo,["my event",["foo","bar"]]', binary=False
        )

    def test_emit_internal_with_none(self, eio):
        s = server.Server()
        s._emit_internal('123', 'my event', None, namespace='/foo')
        s.eio.send.assert_called_once_with(
            '123', '2/foo,["my event"]', binary=False
        )

    def test_emit_internal_with_callback(self, eio):
        s = server.Server()
        id = s.manager._generate_ack_id('123', '/foo', 'cb')
        s._emit_internal('123', 'my event', 'my data', namespace='/foo', id=id)
        s.eio.send.assert_called_once_with(
            '123', '2/foo,1["my event","my data"]', binary=False
        )

    def test_emit_internal_default_namespace(self, eio):
        s = server.Server()
        s._emit_internal('123', 'my event', 'my data')
        s.eio.send.assert_called_once_with(
            '123', '2["my event","my data"]', binary=False
        )

    def test_emit_internal_binary(self, eio):
        s = server.Server(binary=True)
        s._emit_internal('123', u'my event', b'my binary data')
        assert s.eio.send.call_count == 2

    def test_transport(self, eio):
        s = server.Server()
        s.eio.transport = mock.MagicMock(return_value='polling')
        s._handle_eio_connect('foo', 'environ')
        assert s.transport('foo') == 'polling'
        s.eio.transport.assert_called_once_with('foo')

    def test_handle_connect(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        handler = mock.MagicMock()
        s.on('connect', handler)
        s._handle_eio_connect('123', 'environ')
        handler.assert_called_once_with('123', 'environ')
        s.manager.connect.assert_called_once_with('123', '/')
        s.eio.send.assert_called_once_with('123', '0', binary=False)
        assert mgr.initialize.call_count == 1
        s._handle_eio_connect('456', 'environ')
        assert mgr.initialize.call_count == 1

    def test_handle_connect_namespace(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        handler = mock.MagicMock()
        s.on('connect', handler, namespace='/foo')
        s._handle_eio_connect('123', 'environ')
        s._handle_eio_message('123', '0/foo')
        handler.assert_called_once_with('123', 'environ')
        s.manager.connect.assert_any_call('123', '/')
        s.manager.connect.assert_any_call('123', '/foo')
        s.eio.send.assert_any_call('123', '0/foo', binary=False)

    def test_handle_connect_rejected(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        handler = mock.MagicMock(return_value=False)
        s.on('connect', handler)
        ret = s._handle_eio_connect('123', 'environ')
        assert not ret
        handler.assert_called_once_with('123', 'environ')
        assert s.manager.connect.call_count == 1
        assert s.manager.disconnect.call_count == 1
        assert s.environ == {}

    def test_handle_connect_namespace_rejected(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        handler = mock.MagicMock(return_value=False)
        s.on('connect', handler, namespace='/foo')
        ret = s._handle_eio_connect('123', 'environ')
        s._handle_eio_message('123', '0/foo')
        assert ret is None
        assert s.manager.connect.call_count == 2
        assert s.manager.disconnect.call_count == 1
        assert s.environ == {'123': 'environ'}
        s.eio.send.assert_any_call('123', '4/foo', binary=False)

    def test_handle_connect_rejected_always_connect(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr, always_connect=True)
        handler = mock.MagicMock(return_value=False)
        s.on('connect', handler)
        ret = s._handle_eio_connect('123', 'environ')
        assert not ret
        handler.assert_called_once_with('123', 'environ')
        assert s.manager.connect.call_count == 1
        assert s.manager.disconnect.call_count == 1
        assert s.environ == {}
        s.eio.send.assert_any_call('123', '0', binary=False)
        s.eio.send.assert_any_call('123', '1', binary=False)

    def test_handle_connect_namespace_rejected_always_connect(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr, always_connect=True)
        handler = mock.MagicMock(return_value=False)
        s.on('connect', handler, namespace='/foo')
        ret = s._handle_eio_connect('123', 'environ')
        s._handle_eio_message('123', '0/foo')
        assert ret is None
        assert s.manager.connect.call_count == 2
        assert s.manager.disconnect.call_count == 1
        assert s.environ == {'123': 'environ'}
        s.eio.send.assert_any_call('123', '0/foo', binary=False)
        s.eio.send.assert_any_call('123', '1/foo', binary=False)

    def test_handle_connect_rejected_with_exception(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        handler = mock.MagicMock(
            side_effect=exceptions.ConnectionRefusedError('fail_reason')
        )
        s.on('connect', handler)
        ret = s._handle_eio_connect('123', 'environ')
        assert ret == 'fail_reason'
        handler.assert_called_once_with('123', 'environ')
        assert s.manager.connect.call_count == 1
        assert s.manager.disconnect.call_count == 1
        assert s.environ == {}

    def test_handle_connect_rejected_with_empty_exception(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        handler = mock.MagicMock(
            side_effect=exceptions.ConnectionRefusedError()
        )
        s.on('connect', handler)
        ret = s._handle_eio_connect('123', 'environ')
        assert not ret
        handler.assert_called_once_with('123', 'environ')
        assert s.manager.connect.call_count == 1
        assert s.manager.disconnect.call_count == 1
        assert s.environ == {}

    def test_handle_connect_namespace_rejected_with_exception(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        handler = mock.MagicMock(
            side_effect=exceptions.ConnectionRefusedError(u'fail_reason', 1)
        )
        s.on('connect', handler, namespace='/foo')
        ret = s._handle_eio_connect('123', 'environ')
        s._handle_eio_message('123', '0/foo')
        assert ret is None
        assert s.manager.connect.call_count == 2
        assert s.manager.disconnect.call_count == 1
        assert s.environ == {'123': 'environ'}
        s.eio.send.assert_any_call(
            '123', '4/foo,["fail_reason",1]', binary=False
        )

    def test_handle_connect_namespace_rejected_with_empty_exception(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        handler = mock.MagicMock(
            side_effect=exceptions.ConnectionRefusedError()
        )
        s.on('connect', handler, namespace='/foo')
        ret = s._handle_eio_connect('123', 'environ')
        s._handle_eio_message('123', '0/foo')
        assert ret is None
        assert s.manager.connect.call_count == 2
        assert s.manager.disconnect.call_count == 1
        assert s.environ == {'123': 'environ'}
        s.eio.send.assert_any_call('123', '4/foo', binary=False)

    def test_handle_disconnect(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        handler = mock.MagicMock()
        s.on('disconnect', handler)
        s._handle_eio_connect('123', 'environ')
        s._handle_eio_disconnect('123')
        handler.assert_called_once_with('123')
        s.manager.disconnect.assert_called_once_with('123', '/')
        assert s.environ == {}

    def test_handle_disconnect_namespace(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s.manager.get_namespaces = mock.MagicMock(return_value=['/', '/foo'])
        handler = mock.MagicMock()
        s.on('disconnect', handler)
        handler_namespace = mock.MagicMock()
        s.on('disconnect', handler_namespace, namespace='/foo')
        s._handle_eio_connect('123', 'environ')
        s._handle_eio_message('123', '0/foo')
        s._handle_eio_disconnect('123')
        handler.assert_called_once_with('123')
        handler_namespace.assert_called_once_with('123')
        assert s.environ == {}

    def test_handle_disconnect_only_namespace(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s.manager.get_namespaces = mock.MagicMock(return_value=['/', '/foo'])
        handler = mock.MagicMock()
        s.on('disconnect', handler)
        handler_namespace = mock.MagicMock()
        s.on('disconnect', handler_namespace, namespace='/foo')
        s._handle_eio_connect('123', 'environ')
        s._handle_eio_message('123', '0/foo')
        s._handle_eio_message('123', '1/foo')
        assert handler.call_count == 0
        handler_namespace.assert_called_once_with('123')
        assert s.environ == {'123': 'environ'}

    def test_handle_disconnect_unknown_client(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s._handle_eio_disconnect('123')

    def test_handle_event(self, eio):
        s = server.Server(async_handlers=False)
        s.manager.connect('123', '/')
        handler = mock.MagicMock()
        s.on('my message', handler)
        s._handle_eio_message('123', '2["my message","a","b","c"]')
        handler.assert_called_once_with('123', 'a', 'b', 'c')

    def test_handle_event_with_namespace(self, eio):
        s = server.Server(async_handlers=False)
        s.manager.connect('123', '/foo')
        handler = mock.MagicMock()
        s.on('my message', handler, namespace='/foo')
        s._handle_eio_message('123', '2/foo,["my message","a","b","c"]')
        handler.assert_called_once_with('123', 'a', 'b', 'c')

    def test_handle_event_with_disconnected_namespace(self, eio):
        s = server.Server(async_handlers=False)
        s.manager.connect('123', '/foo')
        handler = mock.MagicMock()
        s.on('my message', handler, namespace='/bar')
        s._handle_eio_message('123', '2/bar,["my message","a","b","c"]')
        handler.assert_not_called()

    def test_handle_event_binary(self, eio):
        s = server.Server(async_handlers=False)
        s.manager.connect('123', '/')
        handler = mock.MagicMock()
        s.on('my message', handler)
        s._handle_eio_message(
            '123',
            '52-["my message","a",'
            '{"_placeholder":true,"num":1},'
            '{"_placeholder":true,"num":0}]',
        )
        s._handle_eio_message('123', b'foo')
        s._handle_eio_message('123', b'bar')
        handler.assert_called_once_with('123', 'a', b'bar', b'foo')

    def test_handle_event_binary_ack(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr)
        s._handle_eio_message(
            '123', '61-321["my message","a",' '{"_placeholder":true,"num":0}]'
        )
        s._handle_eio_message('123', b'foo')
        mgr.trigger_callback.assert_called_once_with(
            '123', '/', 321, ['my message', 'a', b'foo']
        )

    def test_handle_event_with_ack(self, eio):
        s = server.Server(async_handlers=False)
        s.manager.connect('123', '/')
        handler = mock.MagicMock(return_value='foo')
        s.on('my message', handler)
        s._handle_eio_message('123', '21000["my message","foo"]')
        handler.assert_called_once_with('123', 'foo')
        s.eio.send.assert_called_once_with('123', '31000["foo"]', binary=False)

    def test_handle_event_with_ack_none(self, eio):
        s = server.Server(async_handlers=False)
        s.manager.connect('123', '/')
        handler = mock.MagicMock(return_value=None)
        s.on('my message', handler)
        s._handle_eio_message('123', '21000["my message","foo"]')
        handler.assert_called_once_with('123', 'foo')
        s.eio.send.assert_called_once_with('123', '31000[]', binary=False)

    def test_handle_event_with_ack_tuple(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr, async_handlers=False)
        handler = mock.MagicMock(return_value=(1, '2', True))
        s.on('my message', handler)
        s._handle_eio_message('123', '21000["my message","a","b","c"]')
        handler.assert_called_once_with('123', 'a', 'b', 'c')
        s.eio.send.assert_called_once_with(
            '123', '31000[1,"2",true]', binary=False
        )

    def test_handle_event_with_ack_list(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(client_manager=mgr, async_handlers=False)
        handler = mock.MagicMock(return_value=[1, '2', True])
        s.on('my message', handler)
        s._handle_eio_message('123', '21000["my message","a","b","c"]')
        handler.assert_called_once_with('123', 'a', 'b', 'c')
        s.eio.send.assert_called_once_with(
            '123', '31000[[1,"2",true]]', binary=False
        )

    def test_handle_event_with_ack_binary(self, eio):
        mgr = mock.MagicMock()
        s = server.Server(
            client_manager=mgr, binary=True, async_handlers=False
        )
        handler = mock.MagicMock(return_value=b'foo')
        s.on('my message', handler)
        s._handle_eio_message('123', '21000["my message","foo"]')
        handler.assert_any_call('123', 'foo')

    def test_handle_error_packet(self, eio):
        s = server.Server()
        with pytest.raises(ValueError):
            s._handle_eio_message('123', '4')

    def test_handle_invalid_packet(self, eio):
        s = server.Server()
        with pytest.raises(ValueError):
            s._handle_eio_message('123', '9')

    def test_send_with_ack(self, eio):
        s = server.Server()
        s._handle_eio_connect('123', 'environ')
        cb = mock.MagicMock()
        id1 = s.manager._generate_ack_id('123', '/', cb)
        id2 = s.manager._generate_ack_id('123', '/', cb)
        s._emit_internal('123', 'my event', ['foo'], id=id1)
        s._emit_internal('123', 'my event', ['bar'], id=id2)
        s._handle_eio_message('123', '31["foo",2]')
        cb.assert_called_once_with('foo', 2)

    def test_send_with_ack_namespace(self, eio):
        s = server.Server()
        s._handle_eio_connect('123', 'environ')
        s._handle_eio_message('123', '0/foo')
        cb = mock.MagicMock()
        id = s.manager._generate_ack_id('123', '/foo', cb)
        s._emit_internal('123', 'my event', ['foo'], namespace='/foo', id=id)
        s._handle_eio_message('123', '3/foo,1["foo",2]')
        cb.assert_called_once_with('foo', 2)

    def test_session(self, eio):
        fake_session = {}

        def fake_get_session(sid):
            return fake_session

        def fake_save_session(sid, session):
            global fake_session
            fake_session = session

        s = server.Server()
        s.eio.get_session = fake_get_session
        s.eio.save_session = fake_save_session
        s._handle_eio_connect('123', 'environ')
        s.save_session('123', {'foo': 'bar'})
        with s.session('123') as session:
            assert session == {'foo': 'bar'}
            session['foo'] = 'baz'
            session['bar'] = 'foo'
        assert s.get_session('123') == {'foo': 'baz', 'bar': 'foo'}
        assert fake_session == {'/': {'foo': 'baz', 'bar': 'foo'}}
        with s.session('123', namespace='/ns') as session:
            assert session == {}
            session['a'] = 'b'
        assert s.get_session('123', namespace='/ns') == {'a': 'b'}
        assert fake_session == {
            '/': {'foo': 'baz', 'bar': 'foo'},
            '/ns': {'a': 'b'},
        }

    def test_disconnect(self, eio):
        s = server.Server()
        s._handle_eio_connect('123', 'environ')
        s.disconnect('123')
        s.eio.send.assert_any_call('123', '1', binary=False)

    def test_disconnect_ignore_queue(self, eio):
        s = server.Server()
        s._handle_eio_connect('123', 'environ')
        s.disconnect('123', ignore_queue=True)
        s.eio.send.assert_any_call('123', '1', binary=False)

    def test_disconnect_namespace(self, eio):
        s = server.Server()
        s._handle_eio_connect('123', 'environ')
        s._handle_eio_message('123', '0/foo')
        s.disconnect('123', namespace='/foo')
        s.eio.send.assert_any_call('123', '1/foo', binary=False)

    def test_disconnect_twice(self, eio):
        s = server.Server()
        s._handle_eio_connect('123', 'environ')
        s.disconnect('123')
        calls = s.eio.send.call_count
        s.disconnect('123')
        assert calls == s.eio.send.call_count

    def test_disconnect_twice_namespace(self, eio):
        s = server.Server()
        s._handle_eio_connect('123', 'environ')
        s._handle_eio_message('123', '0/foo')
        s.disconnect('123', namespace='/foo')
        calls = s.eio.send.call_count
        s.disconnect('123', namespace='/foo')
        assert calls == s.eio.send.call_count

    def test_namespace_handler(self, eio):
        result = {}

        class MyNamespace(namespace.Namespace):
            def on_connect(self, sid, environ):
                result['result'] = (sid, environ)

            def on_disconnect(self, sid):
                result['result'] = ('disconnect', sid)

            def on_foo(self, sid, data):
                result['result'] = (sid, data)

            def on_bar(self, sid):
                result['result'] = 'bar'

            def on_baz(self, sid, data1, data2):
                result['result'] = (data1, data2)

        s = server.Server(async_handlers=False)
        s.register_namespace(MyNamespace('/foo'))
        s._handle_eio_connect('123', 'environ')
        s._handle_eio_message('123', '0/foo')
        assert result['result'] == ('123', 'environ')
        s._handle_eio_message('123', '2/foo,["foo","a"]')
        assert result['result'] == ('123', 'a')
        s._handle_eio_message('123', '2/foo,["bar"]')
        assert result['result'] == 'bar'
        s._handle_eio_message('123', '2/foo,["baz","a","b"]')
        assert result['result'] == ('a', 'b')
        s.disconnect('123', '/foo')
        assert result['result'] == ('disconnect', '123')

    def test_bad_namespace_handler(self, eio):
        class Dummy(object):
            pass

        class AsyncNS(namespace.Namespace):
            def is_asyncio_based(self):
                return True

        s = server.Server()
        with pytest.raises(ValueError):
            s.register_namespace(123)
        with pytest.raises(ValueError):
            s.register_namespace(Dummy)
        with pytest.raises(ValueError):
            s.register_namespace(Dummy())
        with pytest.raises(ValueError):
            s.register_namespace(namespace.Namespace)
        with pytest.raises(ValueError):
            s.register_namespace(AsyncNS())

    def test_logger(self, eio):
        s = server.Server(logger=False)
        assert s.logger.getEffectiveLevel() == logging.ERROR
        s.logger.setLevel(logging.NOTSET)
        s = server.Server(logger=True)
        assert s.logger.getEffectiveLevel() == logging.INFO
        s.logger.setLevel(logging.WARNING)
        s = server.Server(logger=True)
        assert s.logger.getEffectiveLevel() == logging.WARNING
        s.logger.setLevel(logging.NOTSET)
        s = server.Server(logger='foo')
        assert s.logger == 'foo'

    def test_engineio_v3_logger(self, eio):
        server.Server(engineio_v3_logger='foo')
        eio.assert_called_once_with(
            **{'logger': 'foo', 'async_handlers': False}
        )

    def test_custom_json(self, eio):
        # Warning: this test cannot run in parallel with other tests, as it
        # changes the JSON encoding/decoding functions

        class CustomJSON(object):
            @staticmethod
            def dumps(*args, **kwargs):
                return '*** encoded ***'

            @staticmethod
            def loads(*args, **kwargs):
                return '+++ decoded +++'

        server.Server(json=CustomJSON)
        eio.assert_called_once_with(
            **{'json': CustomJSON, 'async_handlers': False}
        )

        pkt = packet.Packet(
            packet_type=packet.EVENT,
            data={six.text_type('foo'): six.text_type('bar')},
        )
        assert pkt.encode() == '2*** encoded ***'
        pkt2 = packet.Packet(encoded_packet=pkt.encode())
        assert pkt2.data == '+++ decoded +++'

        # restore the default JSON module
        packet.Packet.json = json

    def test_async_handlers(self, eio):
        s = server.Server(async_handlers=True)
        s.manager.connect('123', '/')
        s._handle_eio_message('123', '2["my message","a","b","c"]')
        s.eio.start_background_task.assert_called_once_with(
            s._handle_event_internal,
            s,
            '123',
            ['my message', 'a', 'b', 'c'],
            '/',
            None,
        )

    def test_start_background_task(self, eio):
        s = server.Server()
        s.start_background_task('foo', 'bar', baz='baz')
        s.eio.start_background_task.assert_called_once_with(
            'foo', 'bar', baz='baz'
        )

    def test_sleep(self, eio):
        s = server.Server()
        s.sleep(1.23)
        s.eio.sleep.assert_called_once_with(1.23)
