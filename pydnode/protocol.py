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
    def __init__(self, obj, callback_registery):
        """
            arguments must always be an array or arrayish
        """
        assert hasattr(obj, '__iter__')
        self.obj = list(obj)
        self.callbacks = {}
        self.callback_cnt = 0
        self.callback_registery = callback_registery

    def walk(self, obj, path, key=None):
        if callable(obj):
            callback_id = self.callback_registery.add_callback(obj)
            self.callbacks[str(callback_id)] = map(str, path)
            self.callback_cnt += 1
            return '[Function]'
        else:
            return obj

    def serialize(self):
        return self.traverse(self.obj, self.walk, [], 0)


class Deserializer(Traverser):
    def __init__(self, arguments, callbacks, wrap_callback_class=None, callback_registery=None):
        self.arguments = arguments
        self.callbacks = callbacks
        self.wrap_callback_class = wrap_callback_class
        self.callback_registery = callback_registery

    def find_path_in_callbacks(self, path):
        for k, p in self.callbacks.iteritems():
            # we convert both to str, because, json from nodejs/dnode
            # sends everything as str/unicode
            if map(str, p) == map(str, path):
                return k, p

    def walk(self, obj, path, key=None):
        fnd = self.find_path_in_callbacks(path)
        if fnd:
            callback_id, path = fnd
            fn = self.wrap_callback_class(path=path, callback_id=callback_id)
            self.callback_registery.add_callback(fn)
            return fn
        return obj

    def deserialize(self):
        return self.traverse(self.arguments, self.walk, [], 0)


if __name__ == "__main__":
    import json
    from pydnode.dnode import DNodeRemoteFunction, RemoteCallbackRegistry
    remote_fn_registery = RemoteCallbackRegistry()
    o = json.loads('''{"method":1,"arguments":[{"a":1,"b":"[Function]","c":[1,"[Function]"],"d":{"e":"[Function]"}}],"callbacks":{"0":["0","b"],"1":["0","c","1"],"2":["0","d","e"]},"links":[]}''')
    d = Deserializer(arguments=o['arguments'], callbacks=o['callbacks'],
                     wrap_callback_class=DNodeRemoteFunction,
                     callback_registery=remote_fn_registery)
