import re
import eventlet
eventlet.monkey_patch()
from lib2to3.pytree import generate_matches
from socket import socketpair
import pygame
import os
pygame.font.init()
import neat
import pickle
from model.objects import Ball
from model.Image import Image, Button
from  model.objects import  TICKS_PER_SEC
import json 
import sys 
import random
import time
from flask_socketio import SocketIO
from flask import request, copy_current_request_context
from abc import ABC, abstractmethod
sys.path.append('./model')
from ReportingPopulation import ReportingPopulation
sys.path.append('./util')
from util import ScreenDataEmitter, get_ram_usage, get_max_available_ram
import multiprocessing
import threading

# from application import config_data, create_config_file
#
# import pydevd_pycharm
# pydevd_pycharm.settrace('localhost', port=0, stdoutToServer=True, stderrToServer=True)

socket = None
DEBUG = True
game_controller_map = {}

GAME_FRAMERATE = 80#200
MULTIPROCESS = True
GET_RAM_USAGE = False

CHOSEN_FPS = TICKS_PER_SEC
num_processes = multiprocessing.cpu_count()  # Number of CPU cores available
print("NUM AVAILABLE CPUS:", num_processes)



run_game = set() # set that dictates what games (denoted by clinet id) are running
run_game_lock =threading.Lock()



            
            
            
class Game:
    config_path = "./model/config.txt"


    def __init__(self, custom_config,clientID = "no name", framerate = GAME_FRAMERATE):
        '''
        args:
            framerate: How frequently
            TODO: move custom_config to controller, model should not know if visuals are sent to the view
        '''
        #global socket
        self.clientID = clientID
        self.balls = []
        self.images = []
        self.show_display_options = False
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        self.kill = False
        self.net_type = neat.nn.FeedForwardNetwork
        self.solo = False
        self.max_gens = None
        self.graphics = True
        self.override_winner = False
        if custom_config:
            self.max_gens = int(custom_config["max_gens"])
            if "Feed-Forward NN" in custom_config:
                self.net_type = neat.nn.FeedForwardNetwork
            else: 
                self.net_type = neat.nn.RecurrentNetwork

            self.graphics = (custom_config["graphics_choice"] == "true")
            self.override_winner = custom_config["winner_choice"] == "true"

            self.custom_config = custom_config
        else:
            self.custom_config = None

        self.framerate = framerate

        self.gen = 0


    def move_ball_chunk(self, chunk, nets, ge, dt):
        '''
        Move all balls designated by the indices in chunk
        '''
        for i in chunk:
            ball = self.balls[i]
            ball.move(nets, ge, i, self, dt)
    def move_balls(self, nets, ge, dt):
        '''
        Uses parallel processing to move all balls concurrently.
        '''
        chunk_size = len(self.balls) // num_processes
        chunks = [list(range(start, start + chunk_size)) for start in range(0, len(self.balls), chunk_size)]

        # If there's a remaining chunk, add it to the last process
        if len(chunks[-1]) < chunk_size:
            last_chunk = chunks.pop()
            chunks[-1] += last_chunk

        if MULTIPROCESS:
            with multiprocessing.Pool(processes=num_processes) as pool:
                pool.starmap(self.move_ball_chunk, [(chunk, nets, ge, dt) for chunk in chunks])
        else:
            for chunk in chunks:
                self.move_ball_chunk(chunk, nets, ge, dt)
        

    def run_frame(self, pyClock, nets, ge, last_time = 0):
        '''
        Moves all balls in game in a single frame
        args:
            pyClock: pygame clock object
            nets: list of neural networks
            ge: list of genomes
        '''

        if len(self.balls) == 0:
            self.__init__(self.custom_config, socket)

            return

        pyClock.tick(TICKS_PER_SEC)

        #time since last tick in ticks to base game (250 fps)
        dt = (time.time() - last_time) * TICKS_PER_SEC 

        # print(f"running game for {request.sid}")
    
        
        #self.move_balls(nets, ge, dt)
        i = len(self.balls) - 1
        while i >= 0:

            ball = self.balls[i]

            ball.move(nets, ge , i, self, dt)
            i -= 1

    
class GameController(ABC):
    '''
    Controller for Game object, runs the game , takes input, and runs NEAT after every frame.
    '''
    def __init__(self, game, clientID):
        run_game_lock.acquire() # to make sure only one thread adds to run_game at a time
        run_game.add(game.clientID)
        run_game_lock.release()
        self.game = game
        self.clientID = clientID
        game_controller_map[clientID] = self


    def show_train(self):
        self.train_AI(True)

    def handle_input(self,msg):
        return # by default no user input is supported 

    def quit(self):
        # cleanup for quitting the game
        if self.ge:
            self.ge[0].fitness = sys.maxsize
            self.kill = True
        self.game.balls = [] 
        run_game_lock.acquire()
        run_game.remove(self.clientID)#[self.clientID] = False
        run_game_lock.release()
    @abstractmethod
    def mode(self):
        '''
        Run the game mode for this controller, and get score for best ball.
        '''

        raise NotImplementedError

    def main(self, genomes = [], config = None, socket = None):
        '''
        main method for the game, runs the game loop and emits screen data to client
        '''
        global game_controller_map
        display = self.game.graphics
        ge = [] # list of genomes
        nets = [] # list of neural networks

        for genome_id , g in genomes: # this is so that this function can be used for NEAT training in population.Run
            net = self.game.net_type.create(g, config)
            nets.append(net)
            Ball(self.game)
            g.fitness = 0
            ge.append(g)
        self.ge = ge
        self.nets = nets
        
        b = None
        if len(self.game.balls) == 1:
            b = self.game.balls[0]

        pyClock = pygame.time.Clock()
        
        if len(self.game.balls):
            run_game.add(self.game.clientID)

        tick_ct = 0

        emit_name = 'screen' #if not display else 'screen'


        emitter = ScreenDataEmitter(self.game, name = emit_name)
        #print("L126", run, display)
        last_send_time = time.time()
        while self.game.clientID in run_game:  
            #print(len(self.game.balls))
            if len(self.game.balls) == 0:
                break
            last_time = time.time()
            tick_ct += 1

            self.game.run_frame(pyClock, self.nets , self.ge, last_time = last_time)




            skip_frames = round(TICKS_PER_SEC/self.game.framerate)

            if tick_ct % (TICKS_PER_SEC * 2) == 0 and GET_RAM_USAGE:
                print(f"{round(get_ram_usage())} MB RAM used out of {round(get_max_available_ram())} MB available")

            if (tick_ct % skip_frames) == 0 and display: #only emit data for self.game.framerate frames per second TRYNG THIS
                #tick_ct = 0
                if DEBUG:
                    if tick_ct % (TICKS_PER_SEC * 1) == 0:
                        print(f"{self.clientID} game still running with request sid of : {request.sid}")
                last_send_time = time.time()

                emitter.emit_data(socket= socket) # sends to request.sid which is for client with clientID byu defualt
            
                # socket.emit(emit_name, self.game.graphics, to = request.sid)
                # socket.sleep(0)

            socket.sleep(0)# per https://stackoverflow.com/questions/55503874/flask-socketio-eventlet-error-client-is-gone-closing-socket

        game_controller_map.pop(self.game.clientID)
        return b.score if b is not None else b# end the game if no balls on screen


class SoloGameController(GameController):

    def handle_input(self,msg):
        if msg == "right" and len(self.game.balls) > 0:
            self.game.balls[0].jump(True) # TODO: reduce usage of side effects

        elif msg == "left" and len(self.game.balls) > 0:
            self.game.balls[0].jump(False)
    def mode(self, socket = None):
        Ball(self.game)
        self.game.solo = True
        return self.main(socket = socket)

class TrainGameController(GameController):


    def train_AI(self, socket = None):
        self.game.config_path = "./model/config.txt"

        graphics = self.game.graphics
        config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, 
            neat.DefaultSpeciesSet, neat.DefaultStagnation, self.game.config_path)
        
        #p = neat.Population(config) if self.game.graphics else ReportingPopulation(config, socket) # emit data to client if graphics is true, else emit stdout
        p = ReportingPopulation(config, socket, graphics) # emit data to client if graphics is true, else emit stdout, NOT CULPRIT


        p.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        p.add_reporter(stats)

        # def fast_main(genomes, config):
        #     self.main(genomes,config, framerate = CHOSEN_FPS)

        main = lambda genomes, config : self.main(genomes,config, socket = socket)
        mfunc = main # decides whether to show graphics or not
        winner = p.run(mfunc, self.game.max_gens)


        if self.game.override_winner and not self.game.kill:
            print("overriding local winner")
            with open("model/local_winner.pkl", "wb") as f:
                pickle.dump(winner, f)
                f.close()

            cur_highscore = int(open("model/highscore.txt", mode="rt").read())
            if winner.fitness > cur_highscore:
                with open("model/highscore.txt", mode = "w") as h:
                    h.write(str(winner.fitness))
                
                print("overriding record winner")

                with open("model/best_winner.pkl", "wb") as f:
                    pickle.dump(winner, f)
                    f.close()


        self.game.kill = False



    def mode(self, socket = None):
        self.train_AI(socket = socket)
        return None
    

class WinnerGameController(GameController):


    def replay_genome(self, framerate = TICKS_PER_SEC, genome_path="model/best_winner.pkl", socket = None):
        # Load requried NEAT config
        config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, 
                                    neat.DefaultSpeciesSet, 
                                    neat.DefaultStagnation, 
                                    self.game.config_path)

        # Unpickle saved winner
        with open(genome_path, "rb") as f:
            genome = pickle.load(f)

        # Convert loaded genome into required data structure
        genomes = [(1, genome)]

        # Call game with only the loaded genome
        #print(f"L 314 replaying genome with {genome_path}")
        #self.game.graphics = True
        return self.main(genomes, config, socket = socket)
    def mode(self, socket = None):

        return self.replay_genome(socket = socket)


class LocalGameController(WinnerGameController):


    def replay_local_genome(self):
        return self.replay_genome(genome_path='model/local_winner.pkl')
    
    def mode(self, socket = None):
        return self.replay_local_genome()