pydnode
-----------------
pydnode is a dnode protocol implementation in python.


install
-----------------
git clone git@github.com:ybrs/pydnode.git

cd pydnode && virtualenv env && ./env/bin/python setup.py develop

why?
-----------------
because there is only one implementation in python, and it requires twisted (which i'm not a fan) and hasn't been updated in two years (not sure if it works)

and beyond the obvious technical motivation, it's exceedingly simple... because I can

pros & cons
-----------------
pros:

* it basically works, though has some missing parts

cons:

* doesn't support and no intention to support links
* some protocol functions are missing, such as cull etc.
* probably has memory leaks
* no dnode server implementation
* no timeouts (use coroutines)
* not production tested 



usage
-----------------

on your server.js:


    var dnode = require('../..');
    var server = dnode(function (remote, conn) {
       this.fn = function(foo, callback){
           callback(foo, function (o, cb){
              console.log(o)
              cb("done")
           })
       }    
    })
    server.listen(7070);


and call it from python

    from pydnode import dnode
    def output(f, remoteCallback):
        print f
        if remoteCallback:
            remoteCallback("Foo", lambda x: output(x, None))

    client = dnode.DNodeClient("127.0.0.1", 7070)
    client.connect()
    client.calldnodemethod("fn", "foo", output)    


