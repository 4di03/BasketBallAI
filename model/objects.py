#from grpc import xds_server_credentials
# from inspect import GEN_CLOSED
# from ipaddress import _IPAddressBase
from faulthandler import dump_traceback
from operator import truediv
import pygame

import random
pygame.font.init()

from model.Image import Image, Button
import math

WIN_WIDTH = 1920 # 800
WIN_HEIGHT = 1080 # 500

TICKS_PER_SEC =  500

BG_IMG = pygame.transform.scale( pygame.image.load("static/assets/bg.jpg"), (WIN_WIDTH, WIN_HEIGHT))

BALL_SIZE = 100
BALL_IMG = pygame.transform.scale(
    pygame.image.load("static/assets/ball.png"), (BALL_SIZE, BALL_SIZE))

BRAIN_BALL_IMG =  pygame.transform.scale(
    pygame.image.load("static/assets/bball_brain.png"), (BALL_SIZE, BALL_SIZE))

BEST_BALL_IMG =  pygame.transform.scale(
    pygame.image.load("static/assets/winner_ball.png"), (BALL_SIZE, BALL_SIZE))

HOOP_SIZE= 200
HOOP_IMG = pygame.transform.scale(
    pygame.image.load("static/assets/hoop2.png"), (HOOP_SIZE, HOOP_SIZE))


STAT_FONT = pygame.font.SysFont("comicsans", 50)

ALLOWED_TIME = 2000#000 # time in ticks

font = pygame.font.SysFont('Comic Sans MS', 10)

AI_MOVE_INTERVAL = 50 # interval between AI moves in ticks

GEN = 0
MIN_VEL = 0.1
BBOX_WIDTH = 10
BBOX_HEIGHT = 10

HORIZONTAL_VEL = 4 * 250/TICKS_PER_SEC # speed per tick
ACC = 0.02 * math.sqrt(250/TICKS_PER_SEC) # acc per tick
Y_VEL = -3 * math.sqrt(HORIZONTAL_VEL)/1.6 # speed per tick
PRINT_GRAVITY_TIME = False
class BBox:
    def __init__(self, x, y, height = BBOX_HEIGHT, width = BBOX_WIDTH, passable = False):
        self.x = x # x of top left corner of hitbox
        self.y = y+2 # y of top left corner of hitbox
        self.width = width
        self.height = height
        self.rect = pygame.Rect((self.x, self.y) , (self.width, self.height))
        self.mask = pygame.mask.Mask((self.width, self.height), True)
        self.passable = passable


    def draw(self, win):
        pygame.draw.rect(win, (0, 255, 0) if not self.passable else (0, 0 , 255), self.rect)

GROUND = BBox(0, WIN_HEIGHT-20, 500, WIN_WIDTH)


class Rim:
    def __init__(self, x, y):
        #left of rim edge
        self.x = x 
        self.y = y
        leftRim =  BBox(self.x , self.y)
        rightRim = BBox((self.x + HOOP_SIZE) if self.x == 0 else self.x + HOOP_SIZE - BBOX_WIDTH, self.y)
        self.goal = BBox(leftRim.x + leftRim.width, self.y, height = 5, width = HOOP_SIZE - leftRim.width, passable = True)
        self.bboxes = [ self.goal, leftRim, rightRim]
        self.drawable = False


    def draw(self, win):
        
        if self.drawable:
            for b in self.bboxes:
                b.draw(win)


class Ball:
    def __init__(self, game):
        self.x = (WIN_WIDTH/2) - BALL_SIZE # x is 0 at left, GAME_WIDTH right
        self.y = (WIN_HEIGHT/2) - BALL_SIZE # y is 0 at top, GAME_HEIGHT at bottom
        self.x_vel = 0
        self.y_vel = 0
        self.y_acc = ACC
        self.hoop = Hoop(game)
        self.time = 0 #time since jump
        self.mask = pygame.mask.from_surface(BALL_IMG)
        self.score = 0
        self.tick = ALLOWED_TIME# time left
        game.balls.append(self) # add ball to game
        self.tick0 = 0 #  time since start
        self.img = Image(BALL_IMG, self.x, self.y, BALL_SIZE, BALL_SIZE, "static/assets/ball.png") # image of ball
        game.images.append(self.img)# add image to game
        self.game = game


    def draw(self, win):
        hpBar = pygame.Rect((self.x, self.y -20) , (BALL_SIZE * (self.tick/ALLOWED_TIME), 15)) # hp bar drawing

        text_surface = font.render('Score: '+ str(self.score), False, (255, 255, 255))
        #text_surface2 = font.render('Hoop at: '+ str(self.hoop.x) + ", " +str(self.hoop.y), False, (255, 255, 255))
        #text_surface2 = font.render('Time: '+ str(self.time) + ", " +str(self.hoop.y), False, (255, 255, 255))

        self.hoop.draw(win)
        self.img.draw(win)
        pygame.draw.rect(win,(0, 255, 0), hpBar)
        win.blit(text_surface, (self.x + BALL_SIZE/2 - 20, self.y+BALL_SIZE/2 - 10)) # draw score

        # generate code to draw text_surface2 on screen just below text_surface
        #win.blit(text_surface2, (self.x + BALL_SIZE/2 - 20, self.y+BALL_SIZE/2 + 5))

    def jump(self, right):
        #print("JUMPING")
        self.y_acc = ACC

        if right:
            self.x_vel = HORIZONTAL_VEL # set x velocity
        else:
            self.x_vel = -HORIZONTAL_VEL # set x velocity

        self.y_vel = Y_VEL
        self.time = 0 # reset time

    
    def is_off_ground(self,ground = GROUND):
        # check if ball is off ground

        bottom = self.y + BALL_SIZE
        ground_top = ground.y

        return bottom < ground_top

    def move(self, nets , ge ,i,game, dt):
        if self.is_off_ground(GROUND):
            self.y_acc = ACC
        self.tick0 += 1
        
        self.tick -= 1

        if self.tick <= 0:
     
            game.balls.pop(i) # remove ball from game

            if nets and ge:
                nets.pop(i) # remove net from game
                ge.pop(i) # remove genome from game

            return


        for bbox in self.hoop.rim.bboxes:
            self.collide(bbox, ge, i, dt)

        self.collide(GROUND,ge , i, dt)

        self.time += .25 
        #if self.tick0 % 60 == 0:
            #print("L153",f"y_vel: {self.y_vel}",f"x_vel:{self.x_vel}", f"y_acc: {self.y_acc}")
        self.x +=  self.x_vel * dt

        if (self.x <= -BALL_SIZE):
            self.x = WIN_WIDTH - BALL_SIZE
        elif(self.x > WIN_WIDTH):
            self.x = 0

        

        #dy =  self.y_vel* dt + (self.y_acc) * (dt ** 2)
        #self.x_vel = self.damp_vel(self.x_vel, 1 - 0.01)
        self.update_y_vel(dt)

        dy =  self.y_vel * dt
        self.y +=  dy

        self.img.update(self.x, self.y)

        if self.y < -200:
            self.y = -200
        if nets and ge:
            if self.tick0 % 50 == 0:

                output = nets[i].activate((self.hoop.x - self.x, self.hoop.y - self.y, 
                    self.x_vel, dy, self.tick/ALLOWED_TIME, self.y+BALL_SIZE > self.hoop.y))

                x = output.index(max(output))

                if x == 0:
                    self.jump(True)
                elif x == 1:
                    self.jump(False)



    def update_y_vel(self, dt):
        '''
        updates y velocity
        '''
        self.y_vel = self.y_vel + self.y_acc * dt

    def damp_vel(self,vel, damping_rate):

        if vel != 0:
            ny_vel = vel * damping_rate

            vel = self.set_vel(vel, ny_vel)

        return vel

        
    def set_vel(self, vel, new_vel):

        if abs(vel) < MIN_VEL:
            vel = 0
        else:
            vel = new_vel
        return vel

    def collide(self, bbox, ge, i, dt):
       col_point = self.mask.overlap(bbox.mask, (bbox.x - self.x, bbox.y-self.y)) 
       if col_point != None: # if collision occured
            
            #print("collision with bbox at ", bbox.x ,bbox.y)
            #self.update_y_vel(dt)
            dy = self.y_vel * dt
            if not bbox.passable:
                
                if self.y < bbox.y: # if ball is above bbox at time of collison
                   # print(self.x_vel)
                    if self.x_vel == 0:
                        self.y_acc = 0
                        self.y_vel = 0
                    else:
                        self.y = bbox.y - BALL_SIZE

                        self.y_vel += 0.55 * Y_VEL  #self.damp_vel(self.y_vel, 0.9999)

                        self.x_vel = self.set_vel(self.x_vel, self.x_vel * 0.75)
                    #self.x_vel *= 0.5#self.x_vel = self.damp_vel(self.x_vel, 0.995)
                elif self.y >= bbox.y + bbox.height * .8: # if ball is below bbox at time of collison
                    self.y = bbox.y + bbox.height
                    self.y_vel = 0
                else:
                    self.x_vel *= -1
                    self.y_vel *= -1
                    self.x += 10 * self.x_vel * dt
                    self.y += 10 * self.y_vel *dt

                self.time = 0


            elif dy > 0:
                self.tick = ALLOWED_TIME
                self.y = bbox.y+bbox.height + 20
                self.score += 1
                if ge:
                    ge[i].fitness += 100
                self.hoop = Hoop(self.game)


    def get_data(self):
        '''
        get JSON data for ball
        '''
        data = {"images":[], "text": [], "rectangles":[]}

        data["images"].append(self.img.to_list())
        data["images"].append(self.hoop.img.to_list())
        data["text"].append([(self.x + BALL_SIZE/2 - (20 * BALL_SIZE/50), self.y+BALL_SIZE/2 - 0 * (BALL_SIZE/50)),"Score: " + str(self.score), (255,255,255),"12px Arial"])

        if PRINT_GRAVITY_TIME:
            data["text"].append([(self.x + BALL_SIZE/2 - 20, self.y+BALL_SIZE/2 + 5),"Time: " + str(self.time), (255,255,255),"12px Arial"])
        data["rectangles"].append([(self.x, self.y -20) , (BALL_SIZE * (self.tick/ALLOWED_TIME), 15), "green"])

        
        return data


class Hoop:
    #global bboxes
    def __init__(self, game):
        self.x = random.randint(0,1) * (WIN_WIDTH - HOOP_SIZE)
        self.y = random.randint(0, WIN_HEIGHT*.75)
        self.img_copy = HOOP_IMG.copy()    

        if self.x == 0:
            self.img= Image(self.img_copy, self.x, self.y, HOOP_SIZE, HOOP_SIZE,"static/assets/hoop2.png")
        else: 
            self.img = Image(pygame.transform.flip(self.img_copy, True, False), self.x, self.y, HOOP_SIZE, HOOP_SIZE,"static/assets/hoop2.png")
            self.img.reversed = True
        
        self.rim = Rim(self.x, self.y)
        game.images.append(self.img)

    def draw(self, win):

        self.img.draw(win)
        self.rim.draw(win)
