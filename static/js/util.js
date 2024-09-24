export function initGame(socket, gameMode){
    console.log("emmting quit to " + socket.id)
    //to quit any previous sessions
    socket.emit("quit", socket.id);

    //let mode = window.location.href.split('#')[-1]

    socket.emit('start', socket.id, gameMode);

    
}

function returnToMenu(socket) {
    console.log("returning to menu")

    socket.emit('quit', socket.id)


    setTimeout(window.location.replace("/"));
}

window.returnToMenu = returnToMenu;

window.initGame = initGame;