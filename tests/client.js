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

var dnode = require('dnode');

var d = dnode.connect(7071);
d.on('remote', function (remote) {
    console.log("calling remote - foo")
    remote.foo()
    // console.log("calling remote dict test")
    // remote.dicttest({a:1}, function (s) {
    //     console.log('beep => ' + s);
    //     d.end();
    // });
});