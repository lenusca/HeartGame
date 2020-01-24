from Player import *
import itertools

suit = ['HEART', 'SPADES', 'DIAMONDS', 'CLUBS']
value = ['TWO ', 'THREE ', 'FOUR ', 'FIVE ', 'SIX ', 'SEVEN ', 'EIGHT ', 'NINE ', 'TEN ', 'JACK ', 'QUEEN ', 'KING ', 'ACE ']

class Game:
    def __init__(self):
       
        self.deck = list(''.join(card) for card in itertools.product(value,suit))
        self.players = []
        self.player_index = 0
        self.guide_card = None
        self.heart_is_broken = False
        self.cards = []
        self.state = "inactive"
        self.players_accept = []
        self.players_accept_with = []

    # adicionar os jogadores ao jogo
    def set_players(self, player):
        if player not in self.players:
            self.players.append(player)

    # 1ºestado        
    def checkStartConditions(self):
        if len(self.players) >= 4:
            #self.players_accept = self.players
            self.state  = "invite"

    def allAcceptGame(self):
        if len(self.players_accept) == 4:
            self.state = "PlayOpponents"
            return True
        return False

    def addAcceptPlayer(self,player):
        if len(self.players_accept) < 4 and player not in self.players_accept:
            # print("Adicionei o player: ",player.name)
            self.players_accept.append(player)
        
    def addAcceptToplayWith(self,player):
        if len(self.players_accept_with) < 4 and player not in self.players_accept_with:
            # print("Adicionei o player: ",player.name)
            self.players_accept_with.append(player)
       
    # 3º estado
    def allAccept(self):
        if len(self.players_accept_with) == 4:
            self.state = "giveDeck"
            print("Todos aceitaram")
            return True
        return False
        
    # saber quem vai começar
    def start_player(self):
        for i in range(len(self.players)):
            player = self.players[i]
            if player.p_card(Card('clubs', '2')):
                return i

    # distribuir o deck por cada jogador
    def p_deck(self):
        while self.deck.get_deck():
            for p in self.players:
                self.give_card(self.deck, p)
    
    # check
    def give_card(self, deck, player):
        card = deck.pop(0)
        player.p_deck(card)

    def game_round(self):
        for i in range(4):
            player = self.players[(i + self.player_index) % 4]
            card = player.play(self.guide_card, self.heart_is_broken)
            print(player.id + " jogou " + str(card))
            
            if i == 0:
                self.guide_card = card

            # Se jogar copas, apartir dai já se pode jogar
            if card.suit.name == 'HEART':
                self.heart_is_broken = True
        
            self.cards.append(card)
        
        bigger_card = None
        bigger_value = 0
        
        for c in self.cards:
            #mudar aqui
            if (self.guide_card.suit.name == c.suit.name) and (bigger_value < int(c.value.value)):
                bigger_value = int(c.value.value)
                bigger_card = c
        
        atual_player = self.players[((self.cards.index(bigger_card) + self.player_index) % 4)]
        
        for c in self.cards:
            if "QUEEN" in c and "SPADES" in c:
                atual_player.points = atual_player.points + 13

            if "HEART" in c:
                atual_player.points = atual_player.points + 1

        print("\n== TABELA DE PONTUAÇÃO ==")
        

        for p in self.players:
            print(p)
        print("")
        # New game
        self.player_index = self.players.index(atual_player)
        self.guide_card = None
        self.cards = []

    def start(self):
        self.p_deck()
        self.player_index = self.start_player()
        end_game = True
        while end_game:
            while self.players[-1].deck:           
                self.game_round()
            for p in self.players:
                if p.points >= 99:
                    end_game = False
            
            self.deck = Deck()
            self.p_deck()
            self.player_index = self.start_player()
            
        for p in self.players:
            print(p)


#game = Game()
#game.start()



        