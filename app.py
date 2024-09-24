
import eventlet

eventlet.monkey_patch()
# Start with a basic flask app webpage.
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context, request
from random import random
from threading import Thread, Event
from model.Game import Game, GameController, SoloGameController, TrainGameController, WinnerGameController, LocalGameController
from model.objects import WIN_HEIGHT, WIN_WIDTH
import json
import configparser
from flask_cors import CORS
import logging
import time

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

# def randomNumberGenerator():
#     """
#     Generate a random number every 2 seconds and emit to a socketio instance (broadcast)
#     Ideally to be run in a separate thread?
#     """
#     #infinite loop of magical random numbers
#     print("Making random numbers")
#     while not thread_stop_event.isSet():
#         number = round(random()*10, 3)
#         print("number:" + str(number))
#         socketio.emit('newnumber', {'number': number})
#         socketio.sleep(2)


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

    #Start the random number generator thread only if the thread has not been started before.
    # if not thread.is_alive():
    #     print("Not Starting Thread")
        #thread = socketio.start_background_task(randomNumberGenerator)


# @socketio.on('recieve_mode')
# def recieve_mode(mode):
#     global game_mode 

#     print("GOT MODE: " + mode)
#     game_mode = mode

#     socketio.emit("got game", "")


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
    if sid == request.sid: # check if the current request is the same as the one that sent the start message
        #choose the gamemode for the game
        socketio.emit('dimensions', json.dumps([WIN_WIDTH, WIN_HEIGHT]), to= request.sid)

        g = Game(config_data[CONFIG_SECTION_NAME] if CONFIG_SECTION_NAME in config_data else None, socketio, name = request.sid)

        #g.graphics = True # test game.graphics after this point is the culprit
        if game_mode in cmap:
            ctype = cmap[game_mode]
            gc = ctype(g)
            games.append(gc)

            # # print("STARTING GAME FOR " + str(request.sid))
            # mode = None
            # if game_mode == "solo":
            #     mode = gc.play_solo
            # elif game_mode == "train":
            #     mode = gc.train_AI
            # elif game_mode.split("/")[0] == "winner":

            #     if game_mode.split("/")[1] == "record":
            #         mode = gc.replay_genome
            #     else:
            #         mode = gc.replay_local_genome


            start_t = time.time()
            score = gc.mode()

            if game_mode != 'train':
                socketio.emit('game_over', f"Score: {score}", to = request.sid)
            else:
                config_data = {} # reset config after trainign is over
            print("L175, seconds till game end: ", time.time() - start_t)
        else:
            print("Invalid game mode")




@socketio.on('disconnect')
def test_disconnect():
    print(f'Client {request.sid} disconnected')


if __name__ == '__main__':
    socketio.run(app)
    # app.run()