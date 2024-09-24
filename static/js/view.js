//import { initGame } from './util.js';

var imageMap = new Map();

const DEBUG = true;
const PROFILE = false;
// consider socket.on('connect', function(){});
// Function to get URL parameters
function getQueryParam(param) {
    let params = new URLSearchParams(window.location.search);
    return params.get(param);
}
function profileFunction(targetFunction) {
    if (PROFILE){
    return function(...args) {
        const startTime = performance.now(); // Start timer
        const result = targetFunction.apply(this, args); // Call the original function
        const endTime = performance.now(); // End timer
        const executionTime = endTime - startTime;
        console.log(`Execution time: ${executionTime.toFixed(2)} ms`);
        return result;
    };
}else{
    return targetFunction;
}
}
$(document).ready(function () {

    var protocol = window.location.protocol;
    var socket = io.connect(protocol + '//' + document.domain + ':' + location.port);
    var canvas = document.getElementById("canvas");
    var ctx = canvas.getContext('2d');


    var gameWidth = null;
    var gameHeight = null;
    var gameArea = null;
    socket.on('connect', function () {
        let gameMode = getQueryParam('gameMode');

        window.initGame(socket, gameMode);
        

        var start = new Date();

        var messagesRecieved = 0


        function drawScaled(x, y, ctx, width = 0, height = 0, image = null, text = null, rectColor = null, scaleByArea = false) {
            areaFactor = Math.sqrt((canvas.width * canvas.height) / gameArea);

            if (scaleByArea) {
                widthFactor = areaFactor;//canvas.width/gameWidth;
                heightFactor = areaFactor;//canvas.height/gameHeight;
            } else {

                widthFactor = canvas.width / gameWidth;
                heightFactor = canvas.height / gameHeight;
            }
            x = x * widthFactor;
            y = y * heightFactor;
            width = width * widthFactor;
            height = height * heightFactor;


            if (image != null) {


                ctx.drawImage(image, x, y, width, height);


            } else if (text != null) {
                words = text[0]
                font = text[1]
                color = text[2]

                ctx.fillStyle = `rgb(${color[0]},
            ${color[1]},
            ${color[2]})`;

                ctx.font = font;
                ctx.fillText(words, x, y)

            } else if (rectColor != null) {

                ctx.fillStyle = rectColor;

                ctx.fillRect(x, y, width, height)

            }
        }

        function displayStdout(msg) {
            console.log("STDOUT MESSAGE RECIEVED")


            $("#stdout").html(msg);
            //$("#dialog").dialog("open");
        }

        function drawScaled(x, y, ctx, width = 0, height = 0, image = null, text = null, rectColor = null, scaleByArea = false) {
            areaFactor = Math.sqrt((canvas.width * canvas.height) / gameArea);

            if (scaleByArea) {
                widthFactor = areaFactor;//canvas.width/gameWidth;
                heightFactor = areaFactor;//canvas.height/gameHeight;
            } else {

                widthFactor = canvas.width / gameWidth;
                heightFactor = canvas.height / gameHeight;
            }
            x = x * widthFactor;
            y = y * heightFactor;
            width = width * widthFactor;
            height = height * heightFactor;


            if (image != null) {


                ctx.drawImage(image, x, y, width, height);


            } else if (text != null) {
                words = text[0]
                font = text[1]
                color = text[2]

                ctx.fillStyle = `rgb(${color[0]},
            ${color[1]},
            ${color[2]})`;

                ctx.font = font;
                ctx.fillText(words, x, y)

            } else if (rectColor != null) {

                ctx.fillStyle = rectColor;

                ctx.fillRect(x, y, width, height)

            }
        }

 
        function drawQuitButton(rect) {


            ctx.fillStyle = "red";

            ctx.fillRect(rect.x, rect.y, rect.width, rect.height);
            ctx.fillStyle = 'white';
            ctx.font = "20px Verdana";
            ctx.fillText("(M) Menu", rect.x, rect.y + 30, rect.width)
        }

        function updateCanvas(objects) {

            messagesRecieved += 1
            let secondsElapsed = (new Date() - start) / 1000;
            

            ctx.canvas.width = window.innerWidth;
            ctx.canvas.height = window.innerHeight;
            // console.log(objects)
 
            objects = JSON.parse(objects);
            for (let i = 0; i < objects.length; i += 1) {
                object = objects[i];

                images = object["images"]

                for (j = 0; j < images.length; j++) {
                    let image = images[j];
                    // console.log(image)
                    let width = image[3];
                    let height = image[4];
                    let x = image[1];
                    let y = image[2];
                    let isReversed = image[5];
                    let img_path = image[0]
                    let src = "";
                    if (isReversed) {
                        img_split = img_path.split("/")
                        imgName = img_split.pop()
                        img_path = img_split.join("/") + "/reverse_" + imgName;

                    }
                    src = "../" + img_path;


                    // console.log(width)

                    if (!imageMap.has(src)) {
                        let img = new Image(width, height);
                        img.src = src;

                        img.onload = function () {

                            imageMap.set(src, img);
                        };

                    }

                    drawScaled(x, y, ctx, width, height, imageMap.get(src))
                }

                texts = object["text"];

                for (j = 0; j < texts.length; j++) {
                    text = texts[j];

                    pos = text[0]
                    word = text[1];
                    color = text[2];
                    font = (0.0250 * canvas.height).toString() + "px Arial";
                    drawScaled(pos[0], pos[1] + 10, ctx, null, null, null, [word, font, color])
                }


                rects = object["rectangles"];

                for (j = 0; j < rects.length; j++) {
                    rectangle = rects[j];
                    pos = rectangle[0];
                    dim = rectangle[1];
                    color = rectangle[2]


                    drawScaled(pos[0], pos[1], ctx, dim[0], dim[1], null, null, color)
                }

                ctx.font = "30px Bold Arial";
                ctx.fillStyle = "white";


            }


            //The rectangle should have x,y,width,height properties
            var rect = {
                x: canvas.width * .45,
                y: canvas.height * .025,
                width: 100,
                height: 50
            };


            drawQuitButton(rect)
            if (DEBUG){
                let msg = "Average messages per seconds: " + (messagesRecieved / secondsElapsed).toString()
                //console.log()
                // ctx.fillStyle = 'white';
                // ctx.font = "20px Verdana";
                ctx.fillText(msg,.6*canvas.width, .1*canvas.height)
                // ctx.fillText(socket.id + ": "  + secondsElapsed,.6*canvas.width, .1*canvas.height);

            }

        }

        //Function to get the mouse position
        function getMousePos(canvas, event) {
            return {
                x: event.clientX,
                y: event.clientY
            };
        }



        //Function to check whether a point is inside a rectangle
        function isInside(pos, rect) {
            console.log(pos, rect)
            return pos.x > rect.x && pos.x < rect.x + rect.width && pos.y < rect.y + rect.height && pos.y > rect.y
        }

        function runGame() {

            // alert(gameWidth, gameHeight);

            updateCanvas(JSON.stringify([]));


            console.log(gameArea, " GAME AREA VALUE")
            socket.on('screen', profileFunction(updateCanvas));

            socket.on('game_over', function (msg) {
                ctx.fillStyle = 'white';
                ctx.font = "20px Verdana";
                ctx.fillText("GAME OVER\n" + `${msg}`, canvas.width * .4, canvas.height * .5)


            });
            socket.on('stdout', function (msg) {

                console.log("recieving at view.js", msg);
            });

            document.addEventListener('keydown', function (event) {
                if (event.key == "a") {
                    socket.emit("input", "left#" + socket.id);
                } else if (event.key == "d") {
                    socket.emit("input", "right#" + socket.id);
                } else if (event.key == "m") {

                    window.returnToMenu(socket)
                }
            });

            //Binding the click event on the canvas
            document.addEventListener('click', function (evt) {
                var mousePos = getMousePos(canvas, evt);


                //The rectangle should have x,y,width,height properties
                var rect = {
                    x: canvas.width * .45,
                    y: canvas.height * .025,
                    width: 100,
                    height: 50
                };
                if (isInside(mousePos, rect)) {
                    window.returnToMenu(socket)
                }
            }, false);

        }
        
        socket.on('dimensions', function (msg) {
            console.log(msg)
            dims = JSON.parse(msg);
            gameWidth = dims[0];
            gameHeight = dims[1];
            gameArea = gameWidth * gameHeight;

            // ctx.fillStyle = "black";
            // ctx.fillRect(10,10,200,100);
            console.log("RECIEVED DIMENSIONS")
            runGame();
        });


    });
});