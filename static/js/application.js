// import {Solo, Train, Winner} from "./modes.js";

function openCanvas(mode, socket){

    // alert(mode.constructor.name)
    // sessionStorage.setItem('mode', JSON.stringify(mode));
    socket.emit("recieve_mode", mode)
    window.location.replace('game');

}




$(document).ready(function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/menu');
    var numbers_received = [];

    //receive details from server
    socket.on('newnumber', function(msg) {
        console.log("Received number" + msg.number);
        //maintain a list of ten numbers
        if (numbers_received.length >= 10){
            numbers_received.shift()
        }            
        numbers_received.push(msg.number);
        numbers_string = '';
        for (var i = 0; i < numbers_received.length; i++){
            numbers_string = numbers_string + '<p>' + numbers_received[i].toString() + '</p>';
        }
        $('#log').html(numbers_string);

        


        //write other things
    });

    document.addEventListener('keydown', function(event) {
        if(event.key == "a") {
           socket.send("left was pressed");
        }
        else if(event.key == "d") {
            socket.send("right was pressed");
        }
    });


    let solo_btn = document.getElementById("solo-btn");
    let train_btn = document.getElementById("train-btn");
    let winner_btn = document.getElementById("winner-btn");
    



    solo_btn.addEventListener('click', event =>{

        
        openCanvas('solo', socket);
    });


    train_btn.addEventListener('click', event =>{

        openCanvas('train', socket);
    });


    winner_btn.addEventListener('click', event =>{


        openCanvas('winner', socket);
    });


});