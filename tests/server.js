var dnode = require('dnode');


function pfun(x, y){
}

var server = dnode(function (remote, conn) {

    this.z1 = function(foo, callback){
        callback(foo)
    }

    this.z2 = function(foo, f2, bar, callback){
        callback(foo, function(o, cb){
            cb(o);
        }, bar)
    }

    this.z3 = function(o, callback){
        console.log("o >>>>", o, callback)
        callback(function (test, callback2){
            console.log("test >>>", test, callback2)
            callback2(pfun, "OK done")
        })        
    }

});
console.log("starting server on 7070")
server.listen(7070);
