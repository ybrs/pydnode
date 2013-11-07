# -*- coding: utf-8 -*-
import unittest
import multiprocessing, subprocess
import time
import sys
import tornado, functools
from Queue import Queue
from pydnode import dnode
import time

"""
in project root, you need to install dnode for tests
$ npm i dnode
then run
$ ./env/bin/python tests/test_basic.py
"""

class TestProtocol(unittest.TestCase):

    def setUp(self):
        self.p = subprocess.Popen(['node', 'tests/server.js'])
        print "sleeping"
        time.sleep(1)

    def testSimple(self):
        # couldnt find a simpler way
        tests = Queue()
        def on_connect():
            print "on connect called..."
            def fn(f):
                assert f == "foo"
                print tests.get(), "OK"
            tests.put("check simple f==foo")
            client.calldnodemethod("z1", "foo", fn)

            def output(o):
                assert o
                print tests.get(), "OK"

            tests.put("check lambda functions")
            client.calldnodemethod("z1", "foo", lambda x: output(x=="foo") )

            def f2(foo, fn, bar):
                assert foo=="foo" and callable(fn) and bar == "bar"
                tests.put("check calling remote function returning a callback")
                fn("baz", lambda x: output(x=="baz"))
                print tests.get(), "OK"


            tests.put("check multiple args with multiple callbacks")
            client.calldnodemethod("z2", "foo", lambda x: x+1, "bar", f2)

            def check_tests():
                assert tests.empty()
                client.close()
                tornado.ioloop.IOLoop.instance().stop()

            from datetime import timedelta
            tornado.ioloop.IOLoop.instance().add_timeout(timedelta(seconds=2), check_tests)

        client = dnode.DNodeClient("127.0.0.1", 7070)
        client.connect(on_connect=on_connect)


    def tearDown(self):
        self.p.terminate()

if __name__ == '__main__':
    unittest.main()        