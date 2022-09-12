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
from  model.objects import WIN_HEIGHT, WIN_WIDTH, STAT_FONT, BALL_IMG, BALL_SIZE, BRAIN_BALL_IMG, BEST_BALL_IMG,  BG_IMG
import json 
import sys 
import random
from flask import request, copy_current_request_context
# from application import config_data, create_config_file

kill = False
socket = None


class Game:
    config_path = "./model/config.txt"


    def __init__(self, custom_config, socketio, name = "no name"):
        global socket
        self.name = name
        self.balls = []
        self.images = []
        self.show_display_options = False
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        self.kill = False
        self.net_type = neat.nn.FeedForwardNetwork
        socket = socketio
        if custom_config:
            self.max_gens = int(custom_config["max_gens"])
            if "Feed-Forward NN" in custom_config:
                self.net_type = neat.nn.FeedForwardNetwork
            else: 
                self.net_type = neat.nn.RecurrentNetwork

            self.graphics = custom_config["graphics_choice"] == "on"
            self.override_winner = custom_config["winner_choice"] == "on"
            self.custom_config = custom_config
        else:
            self.custom_config = None



        self.gen = 0

 
    
    def replay_local_genome(self):
        self.replay_genome(genome_path='model/local_winner.pkl')
    
    def replay_genome(self, ticks = 250, genome_path="model/best_winner.pkl"):
        # Load requried NEAT config
        config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, self.config_path)

        # Unpickle saved winner
        with open(genome_path, "rb") as f:
            genome = pickle.load(f)

        # Convert loaded genome into required data structure
        genomes = [(1, genome)]

        # Call game with only the loaded genome
        self.main(genomes, config, ticks,socket)


    

    def show_train(self):
        self.train_AI(True)

    def show_main(self, genomes, config):
        self.main(genomes,config,display= True)


    def train_AI(self, display = False):
        global kill
        self.config_path = "./model/config.txt"
        config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, 
            neat.DefaultSpeciesSet, neat.DefaultStagnation, self.config_path)
        

        p = neat.Population(config)


        p.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        p.add_reporter(stats)

        winner = p.run(self.main, self.max_gens)


        if self.override_winner and not kill:
            print("overriding local winner")
            with open("model/local_winner.pkl", "wb") as f:
                pickle.dump(winner, f)
                f.close()

        kill = False

    def emit_data(self,name, socket):

        balls_data = []
        for ball in self.balls:
            balls_data.append(ball.get_data())

        socket.emit(name,json.dumps(balls_data), to = request.sid)
        socket.sleep(0)


    def play_solo(self):
        print("PLAYING SOLO")
        Ball(self)
        self.main([],None,250)

    #only for solo mode
    def make_move(self, input):
        input,sid= input.split("#")
        if sid == request.sid:
            if input == "right" and len(self.balls) > 0:
                self.balls[0].jump(True)

            elif input == "left" and len(self.balls) > 0:
                self.balls[0].jump(False)

    def main(self, genomes, config, ticks = 250, display = False):
        nets = []
        ge = []


        for genome_id , g in genomes:
            net = self.net_type.create(g, config)
            nets.append(net)
            Ball(self)
            g.fitness = 0
            ge.append(g)

        time = pygame.time.Clock()
            
        run = len(self.balls)
        while run:
            # print(f"running game for {request.sid}")
            # if random.randint(0,100) == 42:
            #     print(self)
            global bboxes
            time.tick(ticks)
            if len(nets) == 0 and len(ge) == 0:
                # @socket.on('input')
                # print(f"move for {request.sid}, {self}")
                socket.on_event('input', self.make_move)



            @socket.on('quit')
            def quit_game(sid):

                print("Quitting for " + sid)
                if sid == request.sid:
                    global kill
                    print("QUITTING", genomes)
                    if ge:
                        print("killing mode")
                        ge[0].fitness = sys.maxsize
                        kill = True
                    self.balls = []


            i = len(self.balls) - 1
            while i >= 0:

                ball = self.balls[i]

                ball.move(nets, ge , i, self)

                i -= 1

            self.emit_data("screen", socket)



            if len(self.balls) == 0:
                self.__init__(self.custom_config, socket)

                return
