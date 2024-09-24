// import {Solo, Train, Winner} from "./modes.js";

function loadGame() {


    document.getElementById("btns").innerHTML = "";

    document.getElementById("content").innerHTML = "<img src='static/assets/ball_loader.gif'></img>";




}

function openCanvas(mode) {

    // alert(mode.constructor.name)
    // sessionStorage.setItem('mode', JSON.stringify(mode));
    //socket.emit("recieve_mode", mode)
    loadGame()
    const url = `game?gameMode=${mode}`
    console.log(`replacing locating with : ${url}`)
    setTimeout(
        function () {

            window.location.replace(url);
        }, 1000

    );


}

function openTrainSettings(mode, socket) {



    window.location.replace("train")
}




$(document).ready(function () {
    //connect to the socket server.
    var protocol = window.location.protocol;
    var socket = io.connect(protocol + '//' + document.domain + ':' + location.port);
    var numbers_received = [];

    //receive details from server
    socket.on('newnumber', function (msg) {
        console.log("Received number" + msg.number);
        //maintain a list of ten numbers
        if (numbers_received.length >= 10) {
            numbers_received.shift()
        }
        numbers_received.push(msg.number);
        numbers_string = '';
        for (var i = 0; i < numbers_received.length; i++) {
            numbers_string = numbers_string + '<p>' + numbers_received[i].toString() + '</p>';
        }
        $('#log').html(numbers_string);




        //write other things
    });




    let solo_btn = document.getElementById("solo-btn");
    let train_btn = document.getElementById("train-btn");
    let winner_btn = document.getElementById("winner-btn");




    solo_btn.addEventListener('click', event => {


        openCanvas('solo');
    });


    train_btn.addEventListener('click', event => {

        openTrainSettings('train');
    });

    let model_type = "record";
    $("#dialog").dialog({
        autoOpen: false,
        modal: true,
        show: {
            effect: "fade",
            duration: 1000
        },
        hide: {

            effect: "blind",
            duration: 500
        },
        buttons: [{
            text: "Use Record Model",
            click: function () {
                $("#dialog").dialog("close");
                model_type = "record";
                openCanvas(model_type);
            }
        },
        {
            text: "Use Local Best Model",
            click: function () {
                $("#dialog").dialog("close");

                model_type = "local"
                openCanvas(model_type);
            }
        }
        ],
        minWidth: 600
    });

    winner_btn.addEventListener('click', event => {

        $('#dialog').dialog("open", { modal: true });


    });





});

/*
Todo List:
3. Make text view mode for training
4. Add global and local winner
5. Fix multiple client problem(events overriding eachother) namespaces?
*/