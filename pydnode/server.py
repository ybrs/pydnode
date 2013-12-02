import sys, os, re
import logging
import json
from tornado.ioloop import IOLoop
from tornado.iostream import IOStream
from tornado.tcpserver import TCPServer
from collections import OrderedDict
from dnode import CallBackRegistry, RemoteCallbackRegistry, DNodeFunctionWrapper
from pydnode.protocol import Serializer, Deserializer
import inspect

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')
 
class DnodeServer(TCPServer):
 
    def __init__(self, rpc_class=None, io_loop=None, ssl_options=None, **kwargs):
        logging.info('a echo tcp server is started')
        assert rpc_class
        self.rpc_class = rpc_class
        TCPServer.__init__(self, io_loop=io_loop, ssl_options=ssl_options, **kwargs)
 
    def handle_stream(self, stream, address):
        DnodeConnection(stream, address, self.rpc_class)


class DnodeConnection(object):

    def __init__(self, stream, address, rpc_class):
        logging.info('receive a new connection from %s', address)
        self.conn = stream
        self.address = address
        self.conn.set_close_callback(self._on_close)
        self.commander = rpc_class()
        self.remote_registry = RemoteCallbackRegistry(remote=self)
        self.callback_registry = CallBackRegistry(remote=self)
        self.callback_registry.add_callback(self.methods, "methods")

        self.callbacknumber = 0

        self.send_methods()
        self.conn.read_until('\n', self._on_read_line)

    def get_args_callbacks_(self, *args):
        serializer = Serializer(list(args), self.callback_registry)
        args = serializer.serialize()
        return args, serializer.callbacks

    def methods(self, methods):
        for k, method in methods.iteritems():
            self.remote_registry.add_callback(method, k)

    def send_methods(self):
        methods = inspect.getmembers(self.commander, predicate=inspect.ismethod)

        for name, method in methods:
            self.callback_registry.add_callback(method, name)

        self.call_remote("methods", dict(methods))

    def call_remote(self, method, *args):
        parsedargs, callbacks = self.get_args_callbacks_(*args)

        # dnode/nodejs sends us this,
        #   {"method":1,"arguments":["bar","[Function]"],"callbacks":{"3":["1"]},"links":[]}
        # then expects us to call them
        # with this
        #   {"callbacks": {}, "method": 3, "arguments": ["hello XXXX"]}
        # thats why we have this here.
        try:
            method = int(method)
        except:
            pass

        line = json.dumps({
                    'method': method,
                    'arguments': parsedargs,
                    'callbacks': callbacks,
                    'links': []
                }) + "\n"
        self.conn.write(line)

    def _on_read_line(self, data):
        print "on readline called with", data
        logging.info('read a new line from %s - %s', self.address, data)
        self.parseline(data)

    def write_to_client(self, data):
        self.conn.write(data, self._on_write_complete)

    def get_deserializer(self, arguments, callbacks):
        d = Deserializer(arguments=arguments, callbacks=callbacks,
                     wrap_callback_class=DNodeFunctionWrapper,
                     callback_registery=self.remote_registry)
        return d.deserialize()

    def parseline(self, line):
        o = json.loads(line)
        d = self.get_deserializer(o['arguments'], o['callbacks'])
        fn = self.callback_registry.get_callback(o['method'])
        if fn:
            fn(*d)
        self.conn.read_until("\n", self.parseline)

    def _on_write_complete(self):
        logging.info('write a line to %s', self.address)
        if not self.conn.reading():
            print "on readline...."
            self.conn.read_until("\n", self._on_read_line)
 
    def _on_close(self):
        logging.info('client quit %s', self.address)

def main():

    class RpcMethods(object):
        def dicttest(self, h, callback):
            """
            call with hash
            """
            print "dicttest called !!!"
            callback(h)

        def dicttest2(self, h):
            print "in dicttest2", h
            h['callback']("foo")

        def foo(self, h):
            print "foo called", h


    dnode_server = DnodeServer(rpc_class=RpcMethods)
    dnode_server.listen(7070)
    IOLoop.instance().start()

if __name__ == "__main__":
    main()