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

# from application import config_data, create_config_file
#
# import pydevd_pycharm
# pydevd_pycharm.settrace('localhost', port=0, stdoutToServer=True, stderrToServer=True)

socket = None

game_map = {}

GAME_FRAMERATE = 200

GET_RAM_USAGE = False

CHOSEN_FPS = TICKS_PER_SEC
num_processes = multiprocessing.cpu_count()  # Number of CPU cores available
print("NUM AVAILABLE CPUS:", num_processes)
#only for solo mode
def make_move(input):


    msg,sid= input.split("#")
    game = game_map[sid]


    if sid == request.sid and sid == game.name and game.solo:
        if msg == "right" and len(game.balls) > 0:
            game.balls[0].jump(True)

        elif msg == "left" and len(game.balls) > 0:
            game.balls[0].jump(False)


class Game:
    config_path = "./model/config.txt"


    def __init__(self, custom_config, socketio : SocketIO,name = "no name", framerate = GAME_FRAMERATE):
        '''
        args:
            framerate: How frequently
            TODO: move custom_config to controller, model should not know if visuals are sent to the view
        '''
        global socket
        self.name = name
        self.balls = []
        self.images = []
        self.show_display_options = False
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        self.kill = False
        self.net_type = neat.nn.FeedForwardNetwork
        socket = socketio
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

        with multiprocessing.Pool(processes=num_processes) as pool:
            pool.starmap(self.move_ball_chunk, [(chunk, nets, ge, dt) for chunk in chunks])



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
    def __init__(self, game):

        self.game = game


    

    def show_train(self):
        self.train_AI(True)

   

    @abstractmethod
    def mode(self):
        '''
        Run the game mode for this controller, and get score for best ball.
        '''

        raise NotImplementedError

    def main(self, genomes, config):
        '''
        main method for the game, runs the game loop and emits screen data to client
        '''
        global game_map
        nets = [] # list of neural networks
        ge = [] # list of genomes
        display = self.game.graphics


        for genome_id , g in genomes:
            net = self.game.net_type.create(g, config)
            nets.append(net)
            Ball(self.game)
            g.fitness = 0
            ge.append(g)

        b = None
        if len(self.game.balls) == 1:
            b = self.game.balls[0]

        pyClock = pygame.time.Clock()
            
        run = len(self.game.balls)
        self.game.name = request.sid
        game_map[request.sid] = self.game
        tick_ct = 0

        emit_name = 'screen' #if not display else 'screen'


        emitter = ScreenDataEmitter(self.game, name = emit_name)
        #print("L126", run, display)
        while run:  
            #print(len(self.game.balls))
            if len(self.game.balls) == 0:

                return b.score if b is not None else b# end the game if no balls on screen
            last_time = time.time()
            tick_ct += 1

            self.game.run_frame(pyClock, nets , ge, last_time = last_time)
            socket.on_event('input', make_move) # non-decorator version of socket.on

            @socket.on('quit')
            def quit_game(sid):

                if sid in game_map:
                    game = game_map[sid]
                    if sid == request.sid and sid == game.name:
                        # print("Quitting for " + sid +", " + str(self))
                        if ge:
                            ge[0].fitness = sys.maxsize
                            game.kill = True
                        game.balls = []


            skip_frames = round(TICKS_PER_SEC/self.game.framerate)

            if tick_ct % (TICKS_PER_SEC * 2) == 0 and GET_RAM_USAGE:
                print(f"{round(get_ram_usage())} MB RAM used out of {round(get_max_available_ram())} MB available")

            if (tick_ct % skip_frames) == 0 and display: #only emit data for self.game.framerate frames per second TRYNG THIS
                #tick_ct = 0
                emitter.emit_data(socket= socket)
            
                # socket.emit(emit_name, self.game.graphics, to = request.sid)
                # socket.sleep(0)

            socket.sleep(0)# per https://stackoverflow.com/questions/55503874/flask-socketio-eventlet-error-client-is-gone-closing-socket



class SoloGameController(GameController):

    def mode(self):
        Ball(self.game)
        self.game.solo = True
        return self.main([],None)


class TrainGameController(GameController):


    def __init__(self,game):
        super().__init__(game)


    def train_AI(self):
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

        mfunc = self.main # decides whether to show graphics or not
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



    def mode(self):
        self.train_AI()
        return None
    

class WinnerGameController(GameController):


    def replay_genome(self, framerate = TICKS_PER_SEC, genome_path="model/best_winner.pkl"):
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
        return self.main(genomes, config)
    def mode(self):

        return self.replay_genome()


class LocalGameController(WinnerGameController):


    def replay_local_genome(self):
        return self.replay_genome(genome_path='model/local_winner.pkl')
    
    def mode(self):
        return self.replay_local_genome()