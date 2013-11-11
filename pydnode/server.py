import sys, os, re
import logging
import json
from tornado.ioloop import IOLoop
from tornado.iostream import IOStream
from tornado.tcpserver import TCPServer
from collections import OrderedDict
from dnode import ProtocolCommands, copyobject, DNodeRemoteFunction
 
logging.basicConfig(level=logging.INFO, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')
 
class DnodeServer(TCPServer):
 
    def __init__(self, rpc_class=None, io_loop=None, ssl_options=None, **kwargs):
        logging.info('a echo tcp server is started')
        assert rpc_class
        self.rpc_class = rpc_class
        TCPServer.__init__(self, io_loop=io_loop, ssl_options=ssl_options, **kwargs)
 
    def handle_stream(self, stream, address):
        DnodeConnection(stream, address, self.rpc_class)


class RpcMethods(object):

    def z1(self, k, fn):
        print "received k", k
        print "fn:", fn
        def mycb(*args):
            print "mycb: >>>>", args
        fn("foo")

    def z2(self, k, fn2, k2, fn3):
        print "calling z2", fn2, fn3
        assert k == 'foo'
        assert k2 == 'bar'
        def somecallback(c, f):
            print ">>>", c, f
            f("baz")

        fn2("foo", somecallback, "bar")

    def z3(self):
        pass

class DnodeConnection(object):
 
    stream_set = set([])
 
    def __init__(self, stream, address, rpc_class):
        logging.info('receive a new connection from %s', address)
        self.stream = stream
        self.address = address
        self.stream_set.add(self.stream)
        self.stream.set_close_callback(self._on_close)

        self.pc = ProtocolCommands()
        self.commander = rpc_class()
        self.remotecallbacks = OrderedDict()
        self.callbacks = OrderedDict()
        self.callbacknumber = 0

        # ???
        self.send_methods()

        self.stream.read_until('\n', self._on_read_line)

    def send_methods(self):
        s = '{"method":"methods", "arguments":[{"z1":"[Function]","z2":"[Function]","z3":"[Function]"}], "callbacks":{"0":["0","z1"],"1":["0","z2"],"2":["0","z3"]},"links":[]}'
        for stream in self.stream_set:
            stream.write("%s\n" % s, self._on_write_complete)

    def _on_read_line(self, data):
        logging.info('read a new line from %s - %s', self.address, data)
        self.parseline(data)

    def write_to_client(self, data):
        for stream in self.stream_set:
            stream.write(data, self._on_write_complete)

    def prepare_our_args(self, obj, callbacks):
        if callable(obj):
            self.callbacks[self.callbacknumber] = obj
            callbacks[self.callbacknumber] = [self.argcallbackcounter]
            self.callbacknumber+=1
            self.argcallbackcounter += 1
            return '[Function]'
        elif isinstance(obj, str) or isinstance(obj, unicode) or isinstance(obj, int) or isinstance(obj, float):
            self.argcallbackcounter += 1
        elif isinstance(obj, dict) or isinstance(obj, list) or isinstance(obj, tuple):
            pass
        else:
            raise Exception("Cant convert to json, unsupported type: " + str(type(obj)) )
        return obj

    def calldnodemethod(self, method, *args, **kwargs):
        self.argcallbackcounter = 0
        callbacks = {}
        args = copyobject(args, self.prepare_our_args, callbacks)
        line = json.dumps({
                    'method': method,
                    'arguments': args,
                    'callbacks': callbacks
                }) + "\n"
        print "Sending to server", line
        self.write_to_client(line)

    def normalize_callbacks(self, callbacks):
        ret = []
        for k,v in callbacks.iteritems():
            ret.append((k, v))
        return ret

    def replace_functions(self, obj, callbacks):
        if obj == '[Function]':
            functionid, functionpath = callbacks.pop(0)
            fn = DNodeRemoteFunction(functionid, functionpath, self)
            if functionid not in self.remotecallbacks:
                self.remotecallbacks[functionid] = fn
                return fn
        return obj

    def traverse_result(self, result, callbacks, obj):
        myobj = copyobject(result, self.replace_functions, callbacks)
        return myobj

    def parseline(self, line):
        try:
            o = json.loads(line)
            if isinstance(o['method'], int):
                callbacks = self.normalize_callbacks(o['callbacks'])
                myobj = self.traverse_result(o['arguments'], callbacks, OrderedDict())
                self.callbacks[o['method']](*myobj)
            else:
                fn = getattr(self.pc, o['method'], None)
                if fn:
                    fn(o)
                else:
                    fn = getattr(self.commander, o['method'], None)
                    if fn:
                        # TODO: dont you think this is spagettiii
                        callbacks = self.normalize_callbacks(o['callbacks'])
                        myobj = self.traverse_result(o['arguments'], callbacks, OrderedDict())
                        fn(*myobj)
                    else:
                        raise Exception("method not found - %s" % o['method'])
        except Exception as e:
            logging.exception("exception at parseline")
            raise

 
    def _on_write_complete(self):
        logging.info('write a line to %s', self.address)
        if not self.stream.reading():
            self.stream.read_until('\n', self._on_read_line)
 
    def _on_close(self):
        logging.info('client quit %s', self.address)
        self.stream_set.remove(self.stream)
 
def main():
    echo_server = DnodeServer(rpc_class=RpcMethods)
    echo_server.listen(7070)
    IOLoop.instance().start()

if __name__ == "__main__":
    main()