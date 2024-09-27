
import eventlet

eventlet.monkey_patch()
# Start with a basic flask app webpage.
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context, request
from random import random
from threading import Thread, Event
from model.Game import Game, GameController, SoloGameController, TrainGameController, WinnerGameController, LocalGameController, DEBUG, run_game, game_controller_map
from model.objects import WIN_HEIGHT, WIN_WIDTH
import json
import configparser
from flask_cors import CORS
import logging
import time
from flask_socketio import join_room, leave_room
import sys
SHOW_FLASK_LOGS = False

if not SHOW_FLASK_LOGS:
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

app = Flask(__name__)

#CORS(app)

app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True



config_data = {}

games = []

cfg_parser = configparser.ConfigParser()


cfg_parser.read("model/default_config.txt")


#turn the flask app into a socketio app
socketio = SocketIO(app, async_mode="eventlet", logger=SHOW_FLASK_LOGS, 
                    engineio_logger=SHOW_FLASK_LOGS,cors_allowed_origins="*",
                 pingInterval = 10000, pingTimeout = 600000 * 5)

# #random number Generator Thread
# thread = Thread()
# thread_stop_event = Event()

CONFIG_SECTION_NAME = "UserConfig"


#creates config.txt from config object 
def create_config_file(parser, config_data):
    # print(parser.sections())
    for section in config_data:
        if section != CONFIG_SECTION_NAME:
            for key in config_data[section]:
                parser[section][key] = config_data[section][key]

        
    with open("model/config.txt", mode = "w") as cfg:

        #rewrite config into local file
        if "config-file" in config_data and config_data[CONFIG_SECTION_NAME]["config-file"] != "": #TODO  convert config file to config-input
            parser = configparser.ConfigParser()
            parser.read(config_data[CONFIG_SECTION_NAME]["config-file"])

        parser.write(cfg)

        cfg.close()

@app.route('/')
def index():

    #only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')


@app.route('/game/')
def game():
    #only by sending this page first will the client be connected to the socketio instance
    return render_template('canvas.html')


@app.route('/text_view/')
def text_game():
    #only by sending this page first will the client be connected to the socketio instance
    return render_template('text_view.html') 

@app.route('/train/')
def train_menu():
    return render_template('train.html')


@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)


@socketio.on("train_config")
def send_config(msg):
    global config_data

    config_data = json.loads(msg)

    create_config_file(cfg_parser, config_data)


    socketio.emit("confirm_config", "", to = request.sid)


@socketio.on('connect')
def test_connect():
    # need visibility of the global thread object
    print(f'Client {request.sid} connected')



cmap = {'solo': SoloGameController, 
        'train': TrainGameController, 
        'record': WinnerGameController,
        'local': LocalGameController}

@socketio.on('start')
def prompt_mode(sid, game_mode):
    '''
    args:
        sid: socket/session id of client
    '''
    global games
    global config_data
    # print(f'starting for {sid} with current request.id: {request.sid}')
    if sid != request.sid:
        raise Exception(f"Different sids, {sid} != {request.sid}")

    join_room(sid)

    #choose the gamemode for the game
    socketio.emit('dimensions', json.dumps([WIN_WIDTH, WIN_HEIGHT]), to= sid)

    custom_config = config_data[CONFIG_SECTION_NAME] if CONFIG_SECTION_NAME in config_data else None
    g = Game(custom_config, clientID =sid)

    #g.graphics = True # test game.graphics after this point is the culprit
    if game_mode in cmap:
        ctype = cmap[game_mode]
        game_controller = ctype(game = g, clientID = sid) # initalize game controller
        games.append(game_controller)

        start_t = time.time()
        score = game_controller.mode(socket = socketio)

        if game_mode != 'train':
            socketio.emit('game_over', f"Score: {score}", to = sid)
        else:
            config_data = {} # reset config after trainign is over
            
        if DEBUG:
            print("seconds till game end: ", time.time() - start_t)
        
        leave_room(sid) # leave room after game is over
    else:
        raise Exception("Invalid game mode")




#only for solo mode
def make_move(msg):
    clientID = request.sid
    if clientID in game_controller_map:
        game_controller = game_controller_map[clientID]
        # if clientID != request.sid:
        #     raise Exception(f"Different sids, {clientID} != {request.sid}")
        # if clientID != game_controller.clientID:
        #     raise Exception(f"Different sids, {clientID} != {game_controller.clientID}")
        game_controller.handle_input(msg)
    else:
        print(f"Game not found for {clientID}, not handling input")
            
socketio.on_event('input', make_move) # non-decorator version of socket.on



@socketio.on('quit')
def quit_game(clientID):
    if DEBUG:
        print(f"Quitting for {clientID}")
        #print(game_controller_map[clientID])
    if clientID in game_controller_map:
        game = game_controller_map[clientID]
        game.quit()
    else:
        print(f"Game not found for {clientID}")

@socketio.on('disconnect') # extra disconnect handler in case quit was somehow not called
def handle_disconnect():
    print(f'Client {request.sid} disconnected')
    quit_game(request.sid)
    
    
if __name__ == '__main__':
    print("Starting server")
    socketio.run(app)
    # app.run()