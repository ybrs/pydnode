from pydnode import protocol
import unittest
import json
from collections import OrderedDict

class TestProtocol(unittest.TestCase):
    def test_serialize(self):
        def fn():
            return

        expected = json.loads('''{"method":1,"arguments":[{"a":1,"b":"[Function]","c":[1,"[Function]"],"d":{"e":"[Function]"}}],"callbacks":{"0":["0","b"],"1":["0","c","1"],"2":["0","d","e"]},"links":[]}''')

        #arguments = [{'a':1, 'b': fn, 'c':[1, fn], 'd': {'e': fn}}]
        o = OrderedDict()
        o['a'] = 1
        o['b'] = fn
        o['c'] = [1, fn]
        o['d'] = OrderedDict(dict(e=fn))

        serializer = protocol.Serializer([o])
        args = serializer.serialize()
        self.assertEqual(args, expected['arguments'])
        self.assertDictEqual(serializer.callbacks, expected['callbacks'])


if __name__ == '__main__':
    unittest.main()