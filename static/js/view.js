

var imageMap = new Map();





$(document).ready(function(){
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    var canvas = document.getElementById("canvas");
    var ctx = canvas.getContext('2d');

    var gameWidth = null;
    var gameHeight = null;

    mode = window.location.href.split('#')[-1]

    socket.emit('start', "");

    socket.on('dimensions', function(msg){
        console.log('dimensions recieved :' + msg);
        dims = JSON.parse(msg);
        gameWidth = dims[0];
        gameHeight = dims[1];

        // ctx.fillStyle = "black";
        // ctx.fillRect(10,10,200,100);

    });

    
function drawScaled(x,y,ctx, width = 0,height = 0, image =null , text =null , rectColor = null){


    widthFactor =  canvas.width/gameWidth;
    heightFactor = canvas.height/gameHeight;
    x = x * widthFactor;
    y = y * heightFactor;
    width = width * widthFactor;
    height = height * heightFactor;


    if (image != null){

    ctx.drawImage(image, x, y, width, height);


    } else if (text != null){
        words = text[0]
        font = text[1]
        color = text[2]

        ctx.fillStyle = `rgb(${color[0]},
            ${color[1]},
            ${color[2]})`;

        ctx.font = font;
        ctx.fillText(text,x,y)
        
    } else if (rectColor != null){
        
        ctx.fillStyle = `rgb(${rectColor[0]},
            ${rectColor[1]},
            ${rectColor[2]})`;

        ctx.fillRect(x,y,width,height)

    }
}


    // alert(gameWidth, gameHeight);
    
    function updateCanvas(objects){

        ctx.canvas.width  = window.innerWidth;
        ctx.canvas.height = window.innerHeight;
        // console.log(objects)

        objects = JSON.parse(objects);
        for (i = 0; i < objects.length ; i += 1){
            object = objects[i];

            images = object["images"]

            for (j = 0; j < images.length; j++){
                image = images[j];
                let width = image[-2];
                let height = image[-1];
                let x = image[1];
                let y = image[2];
                let src = "../" + image[0];
                

                if (!imageMap.has(src)){
                    let img = new Image(width, height);
                    img.src = src;
                    
                    img.onload = function(){

                    imageMap.set(src, img);
                    };
                    
                }

                drawScaled(x,y, ctx, width,height,imageMap.get(src))
                console.log(`drew image at ${x} ${y} with width: ${width} , height: ${height} `)
            }

            texts = object["text"];

            for( j = 0; j<texts.length ; j++){
                text = texts[j];
                
                pos = text[0]
                word = text[1];
                color = text[2];
                font = text[3];

                drawScaled(pos[0], pos[1], ctx, null, null, null, [word, font, color])
            }


            rects = object["rectangles"];

            for( j = 0; j<rects.length ; j++){
                rect = rects[j];
                
                pos = rect[0];
                dim = rect[1];
                color = rect[3]

                drawScaled(pos[0], pos[1], ctx, dim[0], dim[1], null,null, color)
            }




        }
        


    }

    updateCanvas(JSON.stringify([]));


    socket.on('screen', updateCanvas);

});