from enum import *
from random import *
from termcolor import colored


class Suit(Enum):
    HEART = 'hearts'
    SPADES = 'spades'
    DIAMONDS = 'diamonds'
    CLUBS = 'clubs'
    NONE = 'NONE'

class Value(Enum):
    TWO = '2'
    THREE = '3'
    FOUR = '4'
    FIVE = '5'
    SIX = '6'
    SEVEN = '7'
    EIGHT = '8'
    NINE = '9'
    TEN = '10'
    JACK = '11'
    QUEEN = '12'
    KING = '13'
    ACE = '14'
    NONE = 'NONE'
class Card:
    # construtor 
    def __init__(self, suit, value):
        self.suit = Suit(suit)
        self.value = Value(value)

    def less(self, other):
        return (self.value < other.value or (self.value == other.value and self.suit < other.suit))

    # def __str__(self):
    #     if self.suit.name == "HEART" or self.suit.name == "DIAMONDS":
    #         return str(self.value.name) +" "+ colored(str(self.suit.name), 'red')
    #     else:
    #         return str(self.value.name) +" "+ colored(str(self.suit.name), 'blue')
    
    def __str__(self):
        if self.suit.name == "HEART" or self.suit.name == "DIAMONDS":
            return str(self.value.name) +" "+ str(self.suit.name)
        else:
            return str(self.value.name) +" "+ str(self.suit.name) 

