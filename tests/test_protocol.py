from pydnode import protocol
import unittest
import json
from collections import OrderedDict
from pprint import pprint
from pydnode.dnode import DNodeFunctionWrapper, CallBackRegistry, RemoteCallbackRegistry

class TestProtocol(unittest.TestCase):
    def test_serialize(self):
        def fn():
            return

        callback_registery = CallBackRegistry()

        expected = json.loads('''{"method":1,"arguments":[{"a":1,"b":"[Function]","c":[1,"[Function]"],"d":{"e":"[Function]"}}],"callbacks":{"0":["0","b"],"1":["0","c","1"],"2":["0","d","e"]},"links":[]}''')

        #arguments = [{'a':1, 'b': fn, 'c':[1, fn], 'd': {'e': fn}}]
        # we use ordered dict just for sake of simplification of keys in callbacks
        o = OrderedDict()
        o['a'] = 1
        o['b'] = fn
        o['c'] = [1, fn]
        o['d'] = OrderedDict(dict(e=fn))

        serializer = protocol.Serializer([o], callback_registery)
        args = serializer.serialize()
        self.assertEqual(args, expected['arguments'])
        self.assertDictEqual(serializer.callbacks, expected['callbacks'])
        #
        remote_callback_registery = RemoteCallbackRegistry()
        o = json.loads('''{"method":1,"arguments":[{"a":1,"b":"[Function]","c":[1,"[Function]"],"d":{"e":"[Function]"}}],"callbacks":{"0":["0","b"],"1":["0","c","1"],"2":["0","d","e"]},"links":[]}''')
        d = protocol.Deserializer(arguments=o['arguments'], callbacks=o['callbacks'],
                                  callback_registery=remote_callback_registery,
                                  wrap_callback_class=DNodeFunctionWrapper)
        deserialized = d.deserialize()
        assert callable(deserialized[0]['b'])
        assert callable(deserialized[0]['c'][1])
        assert callable(deserialized[0]['d']['e'])

if __name__ == '__main__':
    unittest.main()