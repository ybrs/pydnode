# -*- coding: utf-8 -*-
import unittest
import multiprocessing, subprocess
import time
import sys
import tornado, functools
from Queue import Queue
from pydnode import dnode
import time
from pydnode import server

"""
in project root, you need to install dnode for tests
$ npm i dnode
then run
$ ./env/bin/python tests/test_basic.py
"""



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

    def dicttest(self, h, callback):
        """
        call with hash
        """
        callback(h)

    def dicttest2(self, h):
        print "in dicttest2", h
        h['callback']("foo")


class TestProtocol(unittest.TestCase):

    def setUp(self):
        dnode_server = server.DnodeServer(rpc_class=RpcMethods)
        dnode_server.listen(7070)
        # couldnt find a simpler way
        self.tests = Queue()

    def test_simple(self):
        self.client = dnode.DNodeClient("127.0.0.1", 7070)
        self.client.connect(on_connect=self.on_connect)

    def on_connect(self):
        print "connected !!!"
        tests = self.tests
        print "on connect called..."
        def fn(f):
            assert f == "foo"
            print tests.get(), "OK"


        tests.put("check simple f==foo")
        print "calling remote z1"
        self.client.calldnodemethod("z1", "foo", fn)

        tests.put("check simple f==foo")
        self.client.calldnodemethod("z1", "foo", fn)

        tests.put("check simple with remote notation f==foo")
        self.client.remote.z1("foo", fn)

        def output(o):
            assert o
            print tests.get(), "OK"

        tests.put("check lambda functions")
        self.client.calldnodemethod("z1", "foo", lambda x: output(x=="foo") )

        def fn2(foo, fn, bar):
            print "Calling fn2"
            assert foo=="foo" and callable(fn) and bar == "bar"
            tests.put("check calling remote function returning a callback")
            fn("baz", lambda x: output(x=="baz"))
            print tests.get(), "OK"
            print tests.empty(), tests.qsize()

        def fn3(x):
            print "f3 called"

        tests.put("check multiple args with multiple callbacks")
        self.client.calldnodemethod("z2", "foo", fn2, "bar", fn3)

        tests.put("dict test")
        self.client.remote.dicttest({'h': "hello"}, output)

        def fn4(x):
            print "called fn4 with x", x
            print tests.get(), "OK"

        tests.put("dict test with callable")
        self.client.remote.dicttest2({'h': 'hello', 'callback': fn4, 'h2': ('foo')})


        def check_tests():
            print "check tests called...."
            try:
                assert tests.empty()
            except Exception as e:
                raise
            finally:
                self.client.close()
                tornado.ioloop.IOLoop.instance().stop()

        from datetime import timedelta
        tornado.ioloop.IOLoop.instance().add_timeout(timedelta(seconds=2), check_tests)




class TestProtocolWithNodejsServer(unittest.TestCase):
    def setUp(self):
        print "starting server - nodejs - 7071"
        #self.p = subprocess.Popen(['node', 'tests/server.js'])
        time.sleep(1)
        print "started server"
        self.tests = Queue()


    def on_connect(self):
        print "connected !!!"
        tests = self.tests
        print "on connect called..."
        def fn(f):
            assert f == "foo"
            print tests.get(), "OK"


        tests.put("check simple f==foo")
        print "calling remote z1"
        self.client.calldnodemethod("z1", "foo", fn)

        tests.put("check simple f==foo")
        self.client.calldnodemethod("z1", "foo", fn)

        tests.put("check simple with remote notation f==foo")
        self.client.remote.z1("foo", fn)

        def output(o):
            assert o
            print tests.get(), "OK"

        tests.put("check lambda functions")
        self.client.calldnodemethod("z1", "foo", lambda x: output(x=="foo") )

        def fn2(foo, fn, bar):
            print "Calling fn2"
            assert foo=="foo" and callable(fn) and bar == "bar"
            tests.put("check calling remote function returning a callback")
            fn("baz", lambda x: output(x=="baz"))
            print tests.get(), "OK"
            print tests.empty(), tests.qsize()

        def fn3(x):
            print "f3 called"

        tests.put("check multiple args with multiple callbacks")
        self.client.calldnodemethod("z2", "foo", fn2, "bar", fn3)

        tests.put("dict test")
        self.client.remote.dicttest({'h': "hello"}, output)

        def fn4(x):
            print "called fn4 with x", x
            print tests.get(), "OK"

        tests.put("dict test with callable")
        self.client.remote.dicttest2({'h': 'hello', 'callback': fn4, 'h2': ('foo')})


        def check_tests():
            print "check tests called...."
            try:
                assert tests.empty()
            except Exception as e:
                raise
            finally:
                self.client.close()
                tornado.ioloop.IOLoop.instance().stop()

        from datetime import timedelta
        tornado.ioloop.IOLoop.instance().add_timeout(timedelta(seconds=2), check_tests)

    def test_simple(self):
        print "connecting to server"
        self.client = dnode.DNodeClient("127.0.0.1", 7071)
        self.client.connect(on_connect=self.on_connect)


    def tearDown(self):
        pass
        #self.p.terminate()

if __name__ == '__main__':
    unittest.main()        