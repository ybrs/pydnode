class Traverser(object):

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

class Serializer(Traverser):
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
            self.callbacks[str(self.callback_cnt)] = map(str, path)
            self.callback_cnt += 1
            return '[Function]'
        else:
            return obj

    def serialize(self):
        return self.traverse(self.obj, self.walk, [], 0)


class Deserializer(Traverser):
    def __init__(self, arguments, callbacks, wrap_callback_class=None):
        self.arguments = arguments
        self.callbacks = callbacks
        self.wrap_callback_class = wrap_callback_class

    def find_path_in_callbacks(self, path):
        for k, p in self.callbacks.iteritems():
            # we convert both to str, because, json from nodejs/dnode
            # sends everything as str/unicode
            if map(str, p) == map(str, path):
                return k, p

    def walk(self, obj, path, key=None):
        fnd = self.find_path_in_callbacks(path)
        if fnd:
            return self.wrap_callback_class(*fnd)
        return obj

    def deserialize(self):
        return self.traverse(self.arguments, self.walk, [], 0)


