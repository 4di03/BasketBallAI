// import {Solo, Train, Winner} from "./modes.js";
const CONFIG_SECTION_NAME = "UserConfig";

function loadGame(){


    // document.getElementById("myForm").innerHTML = "";

    document.getElementById("content").innerHTML = "<img src='../static/assets/ball_loader.gif'></img>";

    document.getElementById("content").style.textAlign = "center";
    document.getElementById("content").style.marginTop = "15%";


    

}

function openTextMode(mode, socket){
    console.log("OPENING TEXT MODE")
    //socket.emit("recieve_mode", mode)
    loadGame()


    //waiting for confirmation that mode was recieved
    socket.on("got game", function(msg) {

        setTimeout(
            function(){
                window.location.replace('../text_view'); 
            }, 1000

        );

    });
}

function openCanvas(mode){ // TODO: consolidate into a single function
    console.log("OPENING CANVAS")
    //socket.emit("recieve_mode", mode)
    loadGame()


    setTimeout(
        function(){
            window.location.replace(`../game?gameMode=${mode}`);
        }, 1000

    );

}


$(document).ready(function(){
    var protocol = window.location.protocol;
    var socket = io.connect(protocol+ '//' + document.domain + ':' + location.port);

    let menu_btn = document.getElementById("menu-btn");
    let submit_btn = document.getElementById("submit-btn");
    

    menu_btn.addEventListener("click", event => {
        window.location.replace("/");
    });

    submit_btn.addEventListener("click", event => {


        //get form data

        var elements = [].slice.call(document.getElementsByTagName("config-input"));

        //elements = elements.concat([].slice.call(document.getElementsByTagName("select")))

        var config ={};
        for(var i = 0 ; i < elements.length ; i++){

            let element = elements[i];

            if (element.type == "radio" &&!element.checked){
                    continue;
            }


            let section = $(`config-input#${element.id}`).attr('section')
            
            //console.log($(`config-input#${element.id}`))

            // if (element.type == "radio"){
            // console.log(section)
            // }
            config[section] =  config[section] || {};
            
            //console.log(element)
            let elemval = element.getValue();
            config[section][element.id] = elemval

            //keeps only code customization seettings if config file is already given.
            console.log("L100", element.id, elemval)
            if (element.id == "config-file" && elemval != ""){
                //console.log("GOING iN")
                for(const[key,value] of Object.entries(config)){
                    if(key != CONFIG_SECTION_NAME){
                        delete config[key];
                    }
                }
                break;
            }
 
        }

        //throw new Error("L110", config)

        
        const sleep = ms => new Promise(r => setTimeout(r, ms));
    
        sleep(10000);
        let gc = "graphics_choice"

       //ß config[CONFIG_SECTION_NAME][gc] = 'true'; // trying this, THIS WORKS, MEANING IT IS AN ISSUE WITH PYTHON????

        socket.emit("train_config", JSON.stringify(config));

        //config[CONFIG_SECTION_NAME][gc] = 'true';
        let graphics_mode = config[CONFIG_SECTION_NAME][gc];
        //graphics_mode = 'true';
        socket.on("confirm_config", function(msg){
        if (graphics_mode == "true"){
            console.log(socket)
            openCanvas('train');
        } else{
            console.log(socket)
            openTextMode('train'); 

            //openTextMode('train', socket)
        }
        });
    });

});
