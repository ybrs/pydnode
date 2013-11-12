var dnode = require('dnode');


function pfun(x, y){
    console.log("------------------------------")
    console.log("pfun called with", x, y)
}

var server = dnode(function (remote, conn) {

    // this.zt = function(foo, callback){
    //     console.log(">>> zt called")
    //     callback("f", function(d){
    //         console.log(">>>> d:", d)
    //     })
    // }

    // this.z1 = function(foo, callback){
    //     console.log("z1 called", callback)
    //     callback(foo)
    // }

    // this.z2 = function(foo, f2, bar, callback){
    //     console.log(">>> z2 called", callback)
    //     f2(foo, function(o, cb){
    //         cb(o);
    //     }, bar)
    // }

    // this.z3 = function(o, callback){
    //     console.log("z3 >>>>", o, callback)
    //     callback(function (test, callback2){
    //         console.log("test >>>", test, callback2)
    //         callback2(pfun, "OK done")
    //     })
    // }

    this.foo = function(){
        console.log("foo called")
    }

    this.dicttest = function(o, fn){
        console.log("dict test called", o, fn)
        fn({a:1})
    }

    this.dicttest2 = function(d){
        d.callback("hello")
    }

});
console.log("starting server on 7071")
server.listen(7070);
