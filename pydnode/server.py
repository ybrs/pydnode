import sys, os, re
import logging
import json
from tornado.ioloop import IOLoop
from tornado.iostream import IOStream
from tornado.tcpserver import TCPServer
from collections import OrderedDict
from dnode import ProtocolCommands, copyobject, DNodeRemoteFunction, DNodeNode
import inspect


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
    """
    this is just an example server
    """
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


class DnodeConnection(DNodeNode):
 
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
        self.send_methods()
        self.stream.read_until('\n', self._on_read_line)

    def send_methods(self):
        methods = inspect.getmembers(self.commander, predicate=inspect.ismethod)
        args = OrderedDict()
        callbacks = OrderedDict()

        for name, method in methods:
            self.callbacks[self.callbacknumber] = method
            self.callbacks[name] = method
            args[self.callbacknumber] = '[Function]'
            callbacks[str(self.callbacknumber)] = ["0", name]
            self.callbacknumber += 1

        methods_header = dict(method='methods',
             arguments=[args],
             callbacks=callbacks,
             links=[])

        for stream in self.stream_set:
            stream.write("%s\n" % json.dumps(methods_header), self._on_write_complete)

    def _on_read_line(self, data):
        logging.info('read a new line from %s - %s', self.address, data)
        self.parseline(data)

    def write_to_client(self, data):
        for stream in self.stream_set:
            stream.write(data, self._on_write_complete)

    def calldnodemethod(self, method, *args, **kwargs):
        line = self.dnode_method_protocol_line(method, *args, **kwargs)
        self.write_to_client(line)

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
    dnode_server = DnodeServer(rpc_class=RpcMethods)
    dnode_server.listen(7070)
    IOLoop.instance().start()

if __name__ == "__main__":
    main()