export function initGame(socket, gameMode){
    // ßconsole.log("emmting quit to " + socket.id)
    // //to quit any previous sessions
    // socket.emit("quit", socket.id);

    //let mode = window.location.href.split('#')[-1]

    socket.emit('start', socket.id, gameMode);

    
}

function returnToMenu(socket,clientID) {
    // clientID is the client's socket.id that is passed to the server

    console.log(`returning to menu using socket: ${socket} and clientID: ${clientID}`)

    socket.emit('quit', clientID)


    setTimeout(window.location.replace("/"));
}

window.returnToMenu = returnToMenu;

window.initGame = initGame;