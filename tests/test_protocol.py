from pydnode import protocol
import unittest
import json
from collections import OrderedDict
from pprint import pprint

class FnWrapper(object):
    """
    this is just a dummy wrapper for remote function callbacks
    """
    def __init__(self, callback_id, path):
        self.callback_id = callback_id
        self.path = path

    def __call__(self):
        pass

class TestProtocol(unittest.TestCase):
    def test_serialize(self):
        def fn():
            return

        expected = json.loads('''{"method":1,"arguments":[{"a":1,"b":"[Function]","c":[1,"[Function]"],"d":{"e":"[Function]"}}],"callbacks":{"0":["0","b"],"1":["0","c","1"],"2":["0","d","e"]},"links":[]}''')

        #arguments = [{'a':1, 'b': fn, 'c':[1, fn], 'd': {'e': fn}}]
        # we use ordered dict just for sake of simplification of keys in callbacks
        o = OrderedDict()
        o['a'] = 1
        o['b'] = fn
        o['c'] = [1, fn]
        o['d'] = OrderedDict(dict(e=fn))

        serializer = protocol.Serializer([o])
        args = serializer.serialize()
        self.assertEqual(args, expected['arguments'])
        self.assertDictEqual(serializer.callbacks, expected['callbacks'])


    o = json.loads('''{"method":1,"arguments":[{"a":1,"b":"[Function]","c":[1,"[Function]"],"d":{"e":"[Function]"}}],"callbacks":{"0":["0","b"],"1":["0","c","1"],"2":["0","d","e"]},"links":[]}''')
    d = protocol.Deserializer(arguments=o['arguments'], callbacks=o['callbacks'], wrap_callback_class=FnWrapper)
    deserialized = d.deserialize()
    assert callable(deserialized[0]['b'])
    assert callable(deserialized[0]['c'][1])
    assert callable(deserialized[0]['d']['e'])

if __name__ == '__main__':
    unittest.main()