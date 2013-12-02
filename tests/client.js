// var dnode = require('dnode');

// var d = dnode.connect(7070);
// d.on('remote', function (remote) {
//     remote.zt('beep', function (s, cb) {
//         console.log('beep => ' + s, cb);
//         cb("hello....")
//         cb("hello....")
//         // d.end();
//     });
// });


/**
received::: ('127.0.0.1', 61521) {"method":1,"arguments":[{"a":1},"[Function]"],"callbacks":{"0":["1"]},"links":[]}
received::: ('127.0.0.1', 61538) {"callbacks": {"1": [2]}, "method": 1, "arguments": [{"h": "hello"}, "[Function]"]}
**/

var dnode = require('dnode');
var d = dnode.connect(7071);
d.on('remote', function (remote) {
    var fn = function(){}
    remote.foo("hello")
    // remote.dicttest({a:1, b:[1, fn]})
    // remote.dicttest({a:1, b: fn, c:[1, fn], d: {e: fn}})
    // remote.dicttest({a:1}, function (s) {
    // }, {a: [1, function(){}] }, function(){
    //     //
    // });
});