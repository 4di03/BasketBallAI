

$(document).ready(function () {


    var protocol = window.location.protocol;
    var socket = io.connect(protocol + '//' + document.domain + ':' + location.port);
    

    function displayStdout(msg) {
        $("#stdout").html(msg);

    }

    let menu_btn = document.getElementById("menu-btn");

    menu_btn.addEventListener("click", event => {
        window.returnToMenu(socket, socket.id);
    });

    socket.on('connect', function () {

        window.initGame(socket, "train");

        //socket.on('stdout', displayStdout);


        socket.on('stdout', displayStdout); 


        // var start = new Date();
        // while (true) {
        //     // print time in seconds till start
        //     var now = new Date();
        //     var time = Math.round((now - start) / 1000);
        //     if (time > 0) {
        //         console.log(time ," seconds till start");

        // }
        // }
    });

});
