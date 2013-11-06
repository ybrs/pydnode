from pydnode import dnode

def output(fn):
    print ">>>>", fn
    #fn("Foo", lambda x, y: output(x))

client = dnode.DNodeClient("127.0.0.1", 7070)
client.connect()

client.calldnodemethod("z1", "foo", output)