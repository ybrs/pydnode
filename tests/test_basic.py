# -*- coding: utf-8 -*-
import unittest
import multiprocessing, subprocess
import time
import sys

from pydnode import dnode


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
        tests = []

        client = dnode.DNodeClient("127.0.0.1", 7070)
        client.connect()
        def fn(f):
            assert f == "foo"
            print tests.pop(), "OK"
        tests.append("check simple f==foo")
        client.calldnodemethod("z1", "foo", fn)

        def output(o):
            assert o
            print tests.pop(), "OK"

        tests.append("check lambda functions")
        client.calldnodemethod("z1", "foo", lambda x: output(x=="foo") )

        def f2(foo, fn, bar):
            assert foo=="foo" and callable(fn) and bar == "bar"
            tests.append("check calling remote function returning a callback")
            fn("baz", lambda x: output(x=="baz"))
            print tests.pop(), "OK"

        tests.append("check multiple args with multiple callbacks")
        client.calldnodemethod("z2", "foo", lambda x: x+1, "bar", f2)

        assert not tests

    def tearDown(self):
        self.p.terminate()

if __name__ == '__main__':
    unittest.main()        