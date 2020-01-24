from Deck import *
from Card import *
import random

class Player:
    
    def __init__(self, id, port):
        self.deck = []
        self.id = id
        self.points = 0 #inicio do jogo
        self.inTable = 0 #não está na mesa
        self.socket = port
        self.name = ""
        self.msg = [] # array com as mensagens todas
        
    # mostrar os pontos de cada jogador
    def points(self):
        return self.id + " has " + str(self.points) + " points."
    
    #baralho do jogador
    def p_deck(self, card):
        self.deck.append(card)

    # quem começa o jogo, tem de ter a carta *
    def p_card(self, start_card):
        for d in self.deck:
            if (d.value.name == start_card.value.name) and (d.suit.name == start_card.suit.name):
                return True
        return False

    # quem tiver 2 de paus, começa o jogo
    def play(self, guide_card, hearts_is_broken):
        cards = []
        if self.p_card(Card('clubs', '2')): 
            for c in self.deck:
                if (c.value.name == 'TWO') and (c.suit.name == 'CLUBS'):
                    cards.append(c)

        else:
            if guide_card == None:
                guide_card=Card('NONE', 'NONE')
            for c in self.deck:
                if c.suit.name == guide_card.suit.name:
                    cards.append(c)
            # se não houver possibilidade jogar outra suit sem ser copa, joga a copa
            if cards == []:
                for c in self.deck:
                    if c.suit.name == 'HEART':
                        if guide_card.suit.name == "NONE":
                            if hearts_is_broken:
                                cards.append(c)
                                
                        if (guide_card.suit.name == 'CLUB' and guide_card.value.name == '2'):
                            if hearts_is_broken:
                                cards.append(c)

                        else: cards.append(c)
                    else: cards.append(c)

        while True:
            print(len(cards))
            user = random.randint(0, len(cards)-1)
            try:
                
                card = cards[user]
                break
            except:
                print("Not a valid choice. Try again.")
        self.deck.remove(card)
        return card 
