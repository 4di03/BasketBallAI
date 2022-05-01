#from grpc import xds_server_credentials
from inspect import GEN_CLOSED
from ipaddress import _IPAddressBase
import pygame
import time
import os
import random
pygame.font.init()
import neat
import pickle

balls = []

WIN_WIDTH = 800
WIN_HEIGHT = 500

BG_IMG = pygame.transform.scale( pygame.image.load(os.path.join("assets", "bg.jpg")), (WIN_WIDTH, WIN_HEIGHT))

BALL_SIZE = 50
BALL_IMG = pygame.transform.scale(
    pygame.image.load(os.path.join("assets", "ball.png")), (BALL_SIZE, BALL_SIZE))


HOOP_SIZE= 100
HOOP_IMG = pygame.transform.scale(
    pygame.image.load(os.path.join("assets", "hoop2.png")), (HOOP_SIZE, HOOP_SIZE))


STAT_FONT = pygame.font.SysFont("comicsans", 50)

ALLOWED_TIME = 120000000

#bboxes = []

font = pygame.font.SysFont('Comic Sans MS', 10)

GEN = 0

class BBox:
    #global bboxes
    def __init__(self, x, y, height =20, width = 20, passable = False, ground = False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect((self.x, self.y) , (self.width, self.height))
        self.mask = pygame.mask.Mask((self.width, self.height), True)
        #bboxes.append(self)
        self.passable = passable
        self.ground = ground


    def draw(self, win):
        pygame.draw.rect(win, (0, 255, 0) if not self.passable else (0, 0 , 255), self.rect)

ground = BBox(0, WIN_HEIGHT-20, 500, WIN_WIDTH, ground = True)



class Rim:
    def __init__(self, x, y):
        #left of rim edge
        self.x = x 
        self.y = y
        leftRim =  BBox(self.x , self.y)
        rightRim = BBox((self.x + HOOP_SIZE) if self.x == 0 else self.x + HOOP_SIZE - 20, self.y)
        self.goal = BBox(leftRim.x + leftRim.width, self.y, height = 5, width = HOOP_SIZE - leftRim.width, passable = True)
        self.bboxes = [ self.goal, leftRim, rightRim]


    def draw(self, win):
         
        for b in self.bboxes:
          b.draw(win)


class Ball:
    global balls
    global ground
    def __init__(self):
        self.x = (WIN_WIDTH/2) - BALL_SIZE
        self.y = (WIN_HEIGHT/2) - BALL_SIZE
        self.x_vel = 0
        self.y_vel = 0
        self.y_acc = 0.1
        self.hoop = Hoop()
        self.time = 0
        self.mask = pygame.mask.from_surface(BALL_IMG)
        self.score = 0
        self.tick = ALLOWED_TIME
        balls.append(self)
        self.tick0 = 0

    def draw(self, win):
        hpBar = pygame.Rect((self.x, self.y -20) , (BALL_SIZE * (self.tick/ALLOWED_TIME), 15))

        text_surface = font.render('Score: '+ str(self.score), False, (255, 255, 255))
        text_surface2 = font.render('Hoop at: '+ str(self.hoop.x) + ", " +str(self.hoop.y), False, (255, 255, 255))

   

        self.hoop.draw(win)
        win.blit(BALL_IMG, (self.x, self.y))
        pygame.draw.rect(win,(0, 255, 0), hpBar)
        win.blit(text_surface, (self.x + BALL_SIZE/2 - 20, self.y+BALL_SIZE/2 - 10))
#        win.blit(text_surface2, (self.x + BALL_SIZE/2 - 20, self.y+BALL_SIZE/2))


    def jump(self, right):

        if right:
            self.x_vel = 2
        else:
            self.x_vel = -2

        self.y_vel = -1.3
        self.time = 0

    def move(self ,i):
        self.tick0 += 1
        
        self.tick -= 1

        if self.tick <= 0:
            #ge[i].fitness += .1
            #self.hoop.clear()
            balls.pop(i)
            return

        self.collide(ground , False)

        self.time += .25

        dy =  self.y_vel * self.time + (self.y_acc) * (self.time ** 2)

        for bbox in self.hoop.rim.bboxes:
            self.collide(bbox)


        self.y += dy

        
      
        if self.y < -200:
            self.y = -200


        for bbox in self.hoop.rim.bboxes:
            self.collide(bbox, True)

        self.x += self.x_vel

        if (self.x <= -BALL_SIZE):
            self.x = WIN_WIDTH - BALL_SIZE
        elif(self.x > WIN_WIDTH):
            self.x = 0
        

       

    def collide(self, bbox , ground = False):
       col_point = self.mask.overlap(bbox.mask, (bbox.x - self.x, bbox.y-self.y)) 
       #if horiz: print("lmaessa")
       if col_point != None:
            
           # print("collision with bbox at ", bbox.x ,bbox.y)
            dx = self.x_vel
            dy =  self.y_vel * self.time + (self.y_acc) * (self.time ** 2)

            if not bbox.passable:
                
                if self.y + BALL_SIZE - 30 < bbox.y:
                    self.y = bbox.y - BALL_SIZE
                    self.y_vel *= .65
                    self.x_vel *= 0.5
                elif self.y >= bbox.y + bbox.height * .8:
                    #print("burh")
                    self.y = bbox.y + bbox.height
                    self.y_vel = 0
                else:
                    print(self.y, bbox.y+bbox.height)
                    self.x_vel *= -1
                    self.y_vel *= -1
                    self.x += 5 * self.x_vel
                    self.y += 5 * self.y_vel    

                self.time = 0


            elif dy > 0:
                self.tick = ALLOWED_TIME
                self.y = bbox.y+bbox.height + 20
                self.score += 1
                #self.hoop.clear()
                self.hoop = Hoop()


            #print(self.x, self.y)


           



class Hoop:
    #global bboxes
    def __init__(self):
        self.x = random.randint(0,1) * (WIN_WIDTH - HOOP_SIZE)
        self.y = random.randint(0, WIN_HEIGHT*.75)
        self.img = HOOP_IMG.copy()
        self.img =  self.img if self.x == 0 else pygame.transform.flip(self.img, True, False)
        #print(self.x, self.y)
        self.rim = Rim(self.x, self.y)
        #print(self.rim.x, self.rim.y)

    def draw(self, win):

        win.blit(self.img, (self.x, self.y))
        self.rim.draw(win)



    # def clear(self):
    #     for bbox in self.rim.bboxes:
    #         bboxes.remove(bbox)



def draw_window(win, balls, testBox = None):
    win.blit(BG_IMG, (0,0))
    
    for ball in balls:
        ball.draw(win)
        #if hoop != None: ball.hoop.draw(win)

    

    text = STAT_FONT.render("Generation: " + str(GEN), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH/2 - text.get_width(), 10))
    if testBox != None: testBox.draw(win)    
    pygame.display.update()



def main():
    global GEN
    global balls
     

    Ball()

    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    #run = len(balls) > 0
    time = pygame.time.Clock()
    # Ball()
    # Ball()
    # Ball()
    #balls = [Ball()]
    testBox = BBox(100, 100)
    #bboxes = [ground , hoop.rim.bboxes[0], hoop.rim.bboxes[1], testBox]
    


    run = True
    while run:
        # for bbox in bboxes:
        #     print( "bbox at " , bbox.x ,", " ,bbox.y , end = " ")

        time.tick(250)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    print("restarting")
                    balls = []
                    main()

                if event.key == pygame.K_d:
                        #print("jump right")
                        balls[0].jump(True)
                if event.key == pygame.K_a:
                        #print("jump left")
                        balls[0].jump(False)
        
        # print(len(ge))
        # print(len(balls))
        # print(len(nets))
        i = len(balls) - 1
        while i >= 0:

            ball = balls[i]

            ball.move(i)
            if testBox != None: ball.collide(testBox, i)

            i -= 1

            
            


        
        

        draw_window(win,balls, testBox)

        if len(balls) == 0:
            return





main()