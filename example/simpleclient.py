from pydnode import dnode

def output(fn, b):
    print ">>>>", fn, "b", b
    b("hello")
    b("hello 2")
    #fn("Foo", lambda x, y: output(x))

def on_connect():
    print "on connect..."
    client.calldnodemethod("zt", "foo", output)
    client.calldnodemethod("zt", "foo", output)
    client.calldnodemethod("zt", "foo", output)
    #client.calldnodemethod("zt", "foo", output)
    #client.calldnodemethod("zt", "foo", output)


client = dnode.DNodeClient("127.0.0.1", 7070)
client.connect(on_connect=on_connect)

