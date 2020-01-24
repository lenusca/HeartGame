from Card import *
import random
# Full deck of cards
class Deck():
    # baralho
    deck = []

    # construtor
    def __init__(self):
        self.deck = self.deck_total(Suit, Value)
        self.deck_destribute()
    # 4(nº dos naipes)*10(nº de valores)
    def deck_total(self, Suit, Value):
        for s in Suit:
            if s.name != "NONE":
                for v in Value:
                    if v.name != "NONE":
                        self.deck.append(Card(s, v))
        return self.deck

    # distribuir o baralho pelos 4 jogadores
    def deck_destribute(self):
        set = self.deck[:]
        new_deck =[]
        random.shuffle(set) 
        for i in range(0, len(set)):
            new_deck.append(set[i]) 
        self.deck = new_deck

    def shuffledeck(self, deck):
        set = deck[:]
        new_deck =[]
        random.shuffle(set) 
        for i in range(0, len(set)):
            new_deck.append(set[i]) 
        return new_deck
        
    # buscar uma carta, para conseguir imprimir as cartas todas
    def get_card(self):
        if self.deck:
            return self.deck.pop()
    
    # tamanho do baralho
    def get_size(self):
        if self.deck:
            return len(self.deck)

    # retornar baralho
    def get_deck(self):
        return self.deck