from flask import request, copy_current_request_context
from abc import ABC, abstractmethod
import json
import sys
import psutil

def get_ram_usage():
    '''
    returns ram usage in megabytes
    '''
    ram_usage_bytes = psutil.virtual_memory().used
    ram_usage_mb = ram_usage_bytes / (1024 * 1024)  # Convert bytes to megabytes
    return ram_usage_mb
def get_max_available_ram():
    '''
    returns max available ram in megabytes
    '''
    max_available_ram_bytes = psutil.virtual_memory().total
    max_available_ram_mb = max_available_ram_bytes / (1024 * 1024)  # Convert bytes to megabytes
    return max_available_ram_mb

class DataEmitter(ABC):
    '''
    Abstract FunctionObject for emitting json data
    of a certain type from server to client.
    '''

    def __init__(self, name):
        '''
        args:
            game: an instance of Game
            name: name of even to emit to client
        '''
        self.name = name

    @abstractmethod
    def get_data(self):
        '''
        returns json data to emit to client
        args:
            game: an instance of Game
        '''
        raise NotImplementedError

    # def emit_data(self,socket):
    #     '''
    #     emits data to client.
    #     args:
    #         name: name of event to emit to client
    #         socket: SocketIO object
    #         game: Game object
    #     '''
    #     socket.emit(self.name,self.get_data(), to = request.sid)
    #     socket.sleep(0)


class ScreenDataEmitter(DataEmitter):

    def __init__(self, game, name):
        super().__init__(name)
        self.game = game
    def get_data(self):
        '''
        Gets list of balls data to emit to client
        '''
        balls_data = []
        for ball in self.game.balls:
            balls_data.append(ball.get_data())

        return balls_data


class StringDataEmitter(DataEmitter):


    def __init__(self, name , text = None):
        super().__init__(name)
        self.text = text

    def update_text(self, text):
        self.text = text


    def get_data(self):
        '''
        Get data from server stdout as string into json format
        '''

        return self.text


