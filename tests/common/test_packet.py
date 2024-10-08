import unittest

import six

from socketio_v4 import packet
import pytest


class TestPacket(unittest.TestCase):
    def test_encode_default_packet(self):
        pkt = packet.Packet()
        assert pkt.packet_type == packet.EVENT
        assert pkt.data is None
        assert pkt.namespace is None
        assert pkt.id is None
        assert pkt.attachment_count == 0
        assert pkt.encode() == '2'

    def test_decode_default_packet(self):
        pkt = packet.Packet(encoded_packet='2')
        assert pkt.encode(), '2'

    def test_encode_text_event_packet(self):
        pkt = packet.Packet(
            packet_type=packet.EVENT, data=[six.text_type('foo')]
        )
        assert pkt.packet_type == packet.EVENT
        assert pkt.data == ['foo']
        assert pkt.encode() == '2["foo"]'

    def test_decode_text_event_packet(self):
        pkt = packet.Packet(encoded_packet='2["foo"]')
        assert pkt.packet_type == packet.EVENT
        assert pkt.data == ['foo']
        assert pkt.encode() == '2["foo"]'

    def test_decode_empty_event_packet(self):
        pkt = packet.Packet(encoded_packet='1')
        assert pkt.packet_type == packet.DISCONNECT
        # same thing, but with a numeric payload
        pkt = packet.Packet(encoded_packet=1)
        assert pkt.packet_type == packet.DISCONNECT

    def test_encode_binary_event_packet(self):
        pkt = packet.Packet(packet_type=packet.EVENT, data=b'1234')
        assert pkt.packet_type == packet.BINARY_EVENT
        assert pkt.data == b'1234'
        a = ['51-{"_placeholder":true,"num":0}', b'1234']
        b = ['51-{"num":0,"_placeholder":true}', b'1234']
        encoded_packet = pkt.encode()
        assert encoded_packet == a or encoded_packet == b

    def test_decode_binary_event_packet(self):
        pkt = packet.Packet(encoded_packet='51-{"_placeholder":true,"num":0}')
        assert pkt.add_attachment(b'1234')
        assert pkt.packet_type == packet.BINARY_EVENT
        assert pkt.data == b'1234'

    def test_encode_text_ack_packet(self):
        pkt = packet.Packet(
            packet_type=packet.ACK, data=[six.text_type('foo')]
        )
        assert pkt.packet_type == packet.ACK
        assert pkt.data == ['foo']
        assert pkt.encode() == '3["foo"]'

    def test_decode_text_ack_packet(self):
        pkt = packet.Packet(encoded_packet='3["foo"]')
        assert pkt.packet_type == packet.ACK
        assert pkt.data == ['foo']
        assert pkt.encode() == '3["foo"]'

    def test_encode_binary_ack_packet(self):
        pkt = packet.Packet(packet_type=packet.ACK, data=b'1234')
        assert pkt.packet_type == packet.BINARY_ACK
        assert pkt.data == b'1234'
        a = ['61-{"_placeholder":true,"num":0}', b'1234']
        b = ['61-{"num":0,"_placeholder":true}', b'1234']
        encoded_packet = pkt.encode()
        assert encoded_packet == a or encoded_packet == b

    def test_decode_binary_ack_packet(self):
        pkt = packet.Packet(encoded_packet='61-{"_placeholder":true,"num":0}')
        assert pkt.add_attachment(b'1234')
        assert pkt.packet_type == packet.BINARY_ACK
        assert pkt.data == b'1234'

    def test_invalid_binary_packet(self):
        with pytest.raises(ValueError):
            packet.Packet(packet_type=packet.ERROR, data=b'123')

    def test_encode_namespace(self):
        pkt = packet.Packet(
            packet_type=packet.EVENT,
            data=[six.text_type('foo')],
            namespace='/bar',
        )
        assert pkt.namespace == '/bar'
        assert pkt.encode() == '2/bar,["foo"]'

    def test_decode_namespace(self):
        pkt = packet.Packet(encoded_packet='2/bar,["foo"]')
        assert pkt.namespace == '/bar'
        assert pkt.encode() == '2/bar,["foo"]'

    def test_decode_namespace_with_query_string(self):
        # some Socket.IO clients mistakenly attach the query string to the
        # namespace
        pkt = packet.Packet(encoded_packet='2/bar?a=b,["foo"]')
        assert pkt.namespace == '/bar'
        assert pkt.encode() == '2/bar,["foo"]'

    def test_encode_namespace_no_data(self):
        pkt = packet.Packet(packet_type=packet.EVENT, namespace='/bar')
        assert pkt.encode() == '2/bar'

    def test_decode_namespace_no_data(self):
        pkt = packet.Packet(encoded_packet='2/bar')
        assert pkt.namespace == '/bar'
        assert pkt.encode() == '2/bar'

    def test_encode_namespace_with_hyphens(self):
        pkt = packet.Packet(
            packet_type=packet.EVENT,
            data=[six.text_type('foo')],
            namespace='/b-a-r',
        )
        assert pkt.namespace == '/b-a-r'
        assert pkt.encode() == '2/b-a-r,["foo"]'

    def test_decode_namespace_with_hyphens(self):
        pkt = packet.Packet(encoded_packet='2/b-a-r,["foo"]')
        assert pkt.namespace == '/b-a-r'
        assert pkt.encode() == '2/b-a-r,["foo"]'

    def test_encode_event_with_hyphens(self):
        pkt = packet.Packet(
            packet_type=packet.EVENT, data=[six.text_type('f-o-o')]
        )
        assert pkt.namespace is None
        assert pkt.encode() == '2["f-o-o"]'

    def test_decode_event_with_hyphens(self):
        pkt = packet.Packet(encoded_packet='2["f-o-o"]')
        assert pkt.namespace is None
        assert pkt.encode() == '2["f-o-o"]'

    def test_encode_id(self):
        pkt = packet.Packet(
            packet_type=packet.EVENT, data=[six.text_type('foo')], id=123
        )
        assert pkt.id == 123
        assert pkt.encode() == '2123["foo"]'

    def test_decode_id(self):
        pkt = packet.Packet(encoded_packet='2123["foo"]')
        assert pkt.id == 123
        assert pkt.encode() == '2123["foo"]'

    def test_encode_id_no_data(self):
        pkt = packet.Packet(packet_type=packet.EVENT, id=123)
        assert pkt.id == 123
        assert pkt.data is None
        assert pkt.encode() == '2123'

    def test_decode_id_no_data(self):
        pkt = packet.Packet(encoded_packet='2123')
        assert pkt.id == 123
        assert pkt.data is None
        assert pkt.encode() == '2123'

    def test_encode_namespace_and_id(self):
        pkt = packet.Packet(
            packet_type=packet.EVENT,
            data=[six.text_type('foo')],
            namespace='/bar',
            id=123,
        )
        assert pkt.namespace == '/bar'
        assert pkt.id == 123
        assert pkt.encode() == '2/bar,123["foo"]'

    def test_decode_namespace_and_id(self):
        pkt = packet.Packet(encoded_packet='2/bar,123["foo"]')
        assert pkt.namespace == '/bar'
        assert pkt.id == 123
        assert pkt.encode() == '2/bar,123["foo"]'

    def test_encode_many_binary(self):
        pkt = packet.Packet(
            packet_type=packet.EVENT,
            data={'a': six.text_type('123'), 'b': b'456', 'c': [b'789', 123]},
        )
        assert pkt.packet_type == packet.BINARY_EVENT
        ep = pkt.encode()
        assert len(ep) == 3
        assert b'456' in ep
        assert b'789' in ep

    def test_encode_many_binary_ack(self):
        pkt = packet.Packet(
            packet_type=packet.ACK,
            data={'a': six.text_type('123'), 'b': b'456', 'c': [b'789', 123]},
        )
        assert pkt.packet_type == packet.BINARY_ACK
        ep = pkt.encode()
        assert len(ep) == 3
        assert b'456' in ep
        assert b'789' in ep

    def test_decode_many_binary(self):
        pkt = packet.Packet(
            encoded_packet=(
                '52-{"a":"123","b":{"_placeholder":true,"num":0},'
                '"c":[{"_placeholder":true,"num":1},123]}'
            )
        )
        assert not pkt.add_attachment(b'456')
        assert pkt.add_attachment(b'789')
        assert pkt.packet_type == packet.BINARY_EVENT
        assert pkt.data['a'] == '123'
        assert pkt.data['b'] == b'456'
        assert pkt.data['c'] == [b'789', 123]

    def test_decode_many_binary_ack(self):
        pkt = packet.Packet(
            encoded_packet=(
                '62-{"a":"123","b":{"_placeholder":true,"num":0},'
                '"c":[{"_placeholder":true,"num":1},123]}'
            )
        )
        assert not pkt.add_attachment(b'456')
        assert pkt.add_attachment(b'789')
        assert pkt.packet_type == packet.BINARY_ACK
        assert pkt.data['a'] == '123'
        assert pkt.data['b'] == b'456'
        assert pkt.data['c'] == [b'789', 123]

    def test_decode_too_many_binary_packets(self):
        pkt = packet.Packet(
            encoded_packet=(
                '62-{"a":"123","b":{"_placeholder":true,"num":0},'
                '"c":[{"_placeholder":true,"num":1},123]}'
            )
        )
        assert not pkt.add_attachment(b'456')
        assert pkt.add_attachment(b'789')
        with pytest.raises(ValueError):
            pkt.add_attachment(b'123')

    def test_data_is_binary_list(self):
        pkt = packet.Packet()
        assert not pkt._data_is_binary([six.text_type('foo')])
        assert not pkt._data_is_binary([])
        assert pkt._data_is_binary([b'foo'])
        assert pkt._data_is_binary([six.text_type('foo'), b'bar'])

    def test_data_is_binary_dict(self):
        pkt = packet.Packet()
        assert not pkt._data_is_binary({'a': six.text_type('foo')})
        assert not pkt._data_is_binary({})
        assert pkt._data_is_binary({'a': b'foo'})
        assert pkt._data_is_binary({'a': six.text_type('foo'), 'b': b'bar'})
