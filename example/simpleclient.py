from pydnode import dnode
def output(f, remoteCallback):
    print f
    if remoteCallback:
        remoteCallback("Foo", lambda x: output(x, None))

client = dnode.DNodeClient("127.0.0.1", 7070)
client.connect()
client.calldnodemethod("fn", "foo", output)