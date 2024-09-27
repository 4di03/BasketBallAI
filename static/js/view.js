//import { initGame } from './util.js';

var imageMap = new Map();

const DEBUG = true;
const PROFILE = false;
const GAME_FRAMERATE = 80; // default FPS  TODO: use http request/socket to get this value from server.
var start = new Date();

var messagesRecieved = 0
var frames_drawn = 0

// Function to get URL parameters
function getQueryParam(param) {
    let params = new URLSearchParams(window.location.search);
    return params.get(param);
}
function profileFunction(targetFunction) {
    if (PROFILE) {
        return function (...args) {
            const startTime = performance.now(); // Start timer
            const result = targetFunction.apply(this, args); // Call the original function
            const endTime = performance.now(); // End timer
            const executionTime = endTime - startTime;
            console.log(`Execution time: ${executionTime.toFixed(2)} ms`);
            return result;
        };
    } else {
        return targetFunction;
    }
}
let previousClientID = null; // Variable to store the previous client ID



// TODO: cleanup function parameters
function drawScaled(arguments) {

    var {
        x,
        y,
        ctx,
        width=0,
        height=0,
        image=null,
        text=null,
        rectColor=null,
        scaleByArea=false,
        dimensions=null
    } = arguments;

    areaFactor = Math.sqrt((canvas.width * canvas.height) / dimensions.gameArea);

    if (scaleByArea) {
        widthFactor = areaFactor;
        heightFactor = areaFactor;
    } else {

        widthFactor = canvas.width / dimensions.gameWidth;
        heightFactor = canvas.height / dimensions.gameHeight;
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
function drawQuitButton(rect, ctx) {

    ctx.fillStyle = "red";

    ctx.fillRect(rect.x, rect.y, rect.width, rect.height);
    ctx.fillStyle = 'white';
    ctx.font = "20px Verdana";
    ctx.fillText("(M) Menu", rect.x, rect.y + 30, rect.width)
}
function drawObjects(objects, ctx, dimensions) {
    //The rectangle should have x,y,width,height properties
    var rect = {
        x: canvas.width * .45,
        y: canvas.height * .025,
        width: 100,
        height: 50
    };


    drawQuitButton(rect, ctx)
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

            const drawArgs = {
                x,
                y,
                ctx,
                width,
                height,
                image: imageMap.get(src),
                dimensions
            };
            

            drawScaled(drawArgs)
        }

        texts = object["text"];

        for (j = 0; j < texts.length; j++) {
            text = texts[j];

            pos = text[0]
            word = text[1];
            color = text[2];
            font = (0.0250 * canvas.height).toString() + "px Arial";


            const drawArgs = {
                x: pos[0],
                y: pos[1],
                ctx,
                text: [word, font, color],
                dimensions
            };

            drawScaled(drawArgs)
        }


        rects = object["rectangles"];

        for (j = 0; j < rects.length; j++) {
            rectangle = rects[j];
            pos = rectangle[0];
            dim = rectangle[1];
            color = rectangle[2]

            const drawArgs = {
                x: pos[0],
                y: pos[1],
                ctx,
                width: dim[0],
                height: dim[1],
                rectColor: color,
                dimensions
            };

            drawScaled(drawArgs)
        }

        ctx.font = "30px Bold Arial";
        ctx.fillStyle = "white";


    }


    
}

let prev_update_time = new Date();

function resizeCanvas(ctx) { // also has side effect of clearing canvas
    ctx.canvas.width = window.innerWidth;
    ctx.canvas.height = window.innerHeight;
}

function clearCanvas(ctx) {
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
}
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

var timeOfLastFrame = null;
async function updateCanvas(frames, ctx, dimensions) {

    if (DEBUG) {
        prev_update_time = new Date();
    }
    messagesRecieved += 1
    let secondsElapsed = (new Date() - start) / 1000;

    // reset canvas by resizing it
    resizeCanvas(ctx);
    // console.log(objects)

    frames = JSON.parse(frames);
    // if (DEBUG) {
    //     console.log(`Recieved ${frames.length} frames`);
    // }
    const nFrames = frames.length;//Math.min(1,frames.length);
    for (let j = 0; j < nFrames; j++) { // display each frame
        let objects = frames[j];
        clearCanvas(ctx); // clear canvas before drawing
        var timeSinceLastFrameDrawn = 0;
        if (timeOfLastFrame != null) {
            timeSinceLastFrameDrawn = new Date() - timeOfLastFrame; // record time when objects are drawn.
        }
        timeOfLastFrame = new Date();
        
        drawObjects(objects, ctx, dimensions);
        if (DEBUG) {
            let msg = "Average Messages/s: " + (messagesRecieved / secondsElapsed).toString()
            let avgFramesMsg = "Average Frames/s: " + (frames_drawn / secondsElapsed).toString()
            ctx.fillText(msg, .6 * canvas.width, .1 * canvas.height)
            ctx.fillText(avgFramesMsg, .6 * canvas.width, .2 * canvas.height)
        }


        // sleep time to maintain a max framrate
        // if we want to get N fps, we need at most 1/N seconds between frames
        // so we sleep for 1/N - time taken to draw the frame
        // if the time taken to draw the frame is more than 1/N seconds, we don't sleep to maintain the framerate
        const sleepTime = Math.max(0,(1000/GAME_FRAMERATE) - (timeSinceLastFrameDrawn));
        await sleep(sleepTime);

        

        frames_drawn += 1;
    }


    if (frames_drawn > 100000000 || messagesRecieved > 100000000) {
        // to prevent overflow
        frames_drawn = 0;
        messagesRecieved = 0;
        start = new Date();
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

async function runGame(socket, ctx, dimensions) {

    await updateCanvas(JSON.stringify([]), ctx);

    console.log(dimensions.gameArea, " GAME AREA VALUE")

    // create closure with the canvas context
    const updateFunc = (frames) => profileFunction(updateCanvas)(frames, ctx, dimensions);

    socket.on('screen', updateFunc);

    socket.on('game_over', function (msg) {
        ctx.fillStyle = 'white';
        ctx.font = "20px Verdana";
        ctx.fillText("GAME OVER\n" + `${msg}`, canvas.width * .4, canvas.height * .5)


    });
    socket.on('stdout', function (msg) {

        console.log("recieving at view.js", msg);
    });

    document.addEventListener('keydown', function (event) {
        console.log("Emitting input at ", new Date().getTime()/1000)
        if (event.key == "a") {
            socket.emit("input", "left" );
        } else if (event.key == "d") {
            socket.emit("input", "right");
        } else if (event.key == "m") {

            window.returnToMenu(socket, socket.id)
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
            window.returnToMenu(socket, socket.id)
        }
    }, false);

}

$(document).ready(async function () {

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

        socket.on('dimensions', async function (msg) {
            console.log(msg)
            dims = JSON.parse(msg);
            gameWidth = dims[0];
            gameHeight = dims[1];
            gameArea = gameWidth * gameHeight;
            dimensions = {gameWidth, gameHeight, gameArea}
            console.log("RECIEVED DIMENSIONS")
            await runGame(socket, ctx, dimensions);
        });


    });
});