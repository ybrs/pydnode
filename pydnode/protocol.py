from pprint import pprint

class Serializer(object):
    """
    traverses an array/map structure, replaces callbacks,
    and serialize it.
    """
    def __init__(self, obj):
        """
            arguments must always be an array or arrayish
        """
        assert hasattr(obj, '__iter__')
        self.obj = obj
        self.callbacks = {}
        self.callback_cnt = 0

    def walk(self, obj, path, key=None):
        if callable(obj):
            self.callbacks[self.callback_cnt] = path
            self.callback_cnt += 1
            return '[Function]'
        else:
            return obj

    def traverse(self, obj, walk, path, cnt, key=None):
        obj = walk(obj, path, key)
        if isinstance(obj, dict):
            cnt += 1
            n = {}
            for k, v in obj.iteritems():
                n[k] = self.traverse(v, walk, path + [k], cnt, k)
            return n
        elif hasattr(obj, '__iter__'):
            cnt = 0
            n = type(obj)()
            for v in obj:
                v = self.traverse(v, walk, path + [cnt], cnt)
                n.append(v)
                cnt += 1
            return n
        else:
            cnt += 1
        return obj

    def serialize(self):
        return self.traverse(self.obj, self.walk, [], 0)

if __name__ == "__main__":

    path = []

    def fn():
        return

    def fn2():
        return

    obj = [{
        'a': {'b': fn},
        'c': {'d': [2323, fn2]}
    }]

    #obj = ['a', 'b', [1, fn]]

    s = Serializer(obj)
    o = s.serialize()
    pprint(s.callbacks)
    print "------------------"
    pprint(o)


