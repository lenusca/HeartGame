import socket, select, json
from Player import *
from Game import *
import time
import ast
import random

class Server:
	def __init__(self):
		self.host = ""
		self.port = 23562
		self.BUF_SIZE = 30000
		self.ids = list(range(1, 5))
		self.clients = []
		self.clients2 = []
		self.inputs = [] 
		self.serversocket = None
		self.games = []
		self.flag = True
		self.flag2 = False
		self.tmp_data = []
		self.new_msgs = []
		self.givingDeckTo = 0
		self.keys = []
		self.typee = ""

	def start(self):
		self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.serversocket.bind((self.host, self.port))
		self.serversocket.listen(5)
		self.inputs.append(self.serversocket)

	# Troca de mensagens
	def sendMsg(self,player,msg,typee):
		#Verifica se o jogador já está na mesa
		if player.inTable == 0:
			print("Player nº " + str(player.id) + " " + str(msg))
		
		if type(msg) is list:
			aux = msg
			msg = ' '.join(map(str, aux)) 
		pack = 	{	"header": "server_" + str(player.id),"TYPE":typee,
					"payload": msg}
		player.socket.send(json.dumps(pack).encode())

	def sendDeck(self,player,deck):
		#Verifica se o jogador já está na mesa
		if player.inTable == 0:
			print("Player nº " + str(player.id) + " " + str(msg))
		
		if type(deck) is list:
			aux = deck
			deck = ' '.join(map(str, aux)) 
		pack = 	{	"header": "server_" + str(player.id),"TYPE": "DECK",
					"payload": deck}
		player.socket.send(json.dumps(pack).encode())

	def sendKeys(self,player,key):
		if player.inTable == 0:
			print("Player nº " + str(player.id) + " " + str(msg))
		
		pack = 	{	"header": "server_" + str(player.id),"TYPE": "KEYS",
					"payload": key}
		player.socket.send(json.dumps(pack).encode())

	def readMsg(self, player):
		if len(player.msg) > 0:
			msg = player.msg.pop(0)
		else:
			msg = ""
		return msg

	def receiveMsgs(self):
		ins, _, _ = select.select(self.inputs, self.inputs, [], 3)
		if ins: 
			for in_conn in ins:
				if in_conn is self.serversocket:
					self.newClient(in_conn)
				else:
					talking = '0'
					data = in_conn.recv(self.BUF_SIZE).decode()
				
					pack = json.loads(data)
					#print("Pack: ",pack)
					# print("TYPE: ",type(pack["header"]))
					for player in self.clients2:
						# print(player.id)
						if(player.id == int(pack["header"].split("_")[0])):
							talking=player
							if "TYPE" in pack:
								self.typee = pack["TYPE"]
					# for g in self.games:
					# 	print("GAME	 socket:",g)
					# 	for p in g.players:
					# 		if p.socket is socket:
					# 			talking = p
					# print("talking with ",talking)

					if "server" in pack["header"]:
						msg = pack["payload"]
						self.saveMsg(talking,msg)
			
				  
	def getMsg(self):
		data = self.serversocket.recv(self.BUF_SIZE)
		pack = json.loads(data)

		msg = pack["payload"]

		if type(msg) is str:
			arr = self.splitMsgs(msg)
			for msg in arr:
				#print(pack["header"].split("_")[0] + ":" + str(msg)) # print message when it receives
				self.new_msgs.append(msg)
		else:
			#print(str(msg)) # print message when it receives		
			self.new_msgs.append(msg)

	def forwardMsg(self, pack):
		client = int(pack["header"].split("_")[1])
		if client != 0:
			client.socket.send(json.dumps(pack).encode())

	def addPlayer(self, clientsocket):
		id = self.ids.pop(0)
		player = Player(id, clientsocket)
		self.clients.append(player)
		self.clients2.append(player)
		return player

	def sendPlainMsg(self, player, msg):
		if player.inTable == 0:
			print("ID " + str(player.id) + ": " + str(msg))
		else:
			print("T" + str(player.inTable) + " ID" + str(player.id) + ": " + str(msg))
		
		if type(msg) is list:
			aux = msg
			msg = ' '.join(map(str, aux)) 

		pack = 	{	"header": "server_"+str(player.id),
					"payload": msg}
		player.socket.send(json.dumps(pack).encode())

	def newClient(self, client):
		clientsocket, _ = client.accept()
		self.inputs.append(clientsocket)
		data = clientsocket.recv(self.BUF_SIZE).decode()
		pack = json.loads(data)
		
		if self.ids:
			player = self.addPlayer(clientsocket)
			# Send the welcome message and inform the id
			self.sendPlainMsg(player,"Welcome! You're nº: " + str(player.id))
		else:
			print("Name: " + data + " tried to join but the table is full")
			# Send the welcome message and inform the id
			sendPlainMsg(player,"Sorry! The table is full. Come back later")

		msg = pack["payload"]
		player.name = msg
		print("ID:" + str(player.id) + " Name: " + player.name + " joined the game")


	def saveMsg(self, player, MSG):
		m = ""
		for message in MSG:
			m+=message
		#print("mensagemmm: ",m)
		for i in self.clients2:
			if(i.id==player.id):
				i.msg.append(m)
		#print("player message: ", player.id)
		

	def requestGame(self, player, game):
		self.sendMsg(player, "ACCEPT THE GAME","REQUEST_GAME")
		time.sleep(2)
	
	def requestCard(self, player, deck):
		self.sendMsg(player, deck,"CARD")
		time.sleep(2)

	# JOGO
	def newGame(self):
		self.games.append(Game())
		for i in range(4):
			player = self.clients.pop(0)
			player.inTable = len(self.games)
			self.games[len(self.games)-1].set_players(player)

	def gameManage(self, game):
		# 1ºestado
		if game.state == "inactive":
			game.checkStartConditions()
		
		# 2ºestado, convidar para jogar 
		elif game.state == "invite":
			for player in game.players:
				self.requestGame(player, game)
				#proximo estado
			game.state = "waitForResponse"
		
		# 3º estados, resposta se quer jogar ou não
		elif game.state == "waitForResponse":
			if game.allAcceptGame() == False:
				for player in game.players:
					if(len(player.msg) > 0 ):
						if("accept to play" in player.msg[0]):
							game.addAcceptPlayer(player)
							player.msg.pop(0)	
						else:
							print("Waiting...")
							time.sleep(0.5)
							game.state = "waitForResponse"
		
		# 4ºestado, manda a mensagem a todos para estes aceitarem com quem qurem jogar uns
		# com os outros e recebem a resposta
		elif game.state == "PlayOpponents":
			if game.allAccept() == False:
				if self.flag2 == False: 
					for i in game.players_accept:
						print("Nomes que aceitaram: ",i.name)
					op = ""
					for p in game.players_accept:
						op = ""
						for pla in game.players_accept:
							if pla.id != p.id:
								op = op + "\n                 " + pla.name
						self.sendMsg(p,"List of the players: " + op,"REQUEST_PLAY")
						time.sleep(0.5)
					self.flag2 = True
				else:
					for player in game.players_accept:
						if(len(player.msg) > 0 ):
							if("accept to play" in player.msg[0]):
								game.addAcceptToplayWith(player)
								player.msg.pop(0)
								time.sleep(2)
							else:
								print("Waiting...")
								game.state = "PlayOpponents"

		# 5ºestado, envia o baralho ao cliente 
		elif game.state == "giveDeck":
			if(self.givingDeckTo < 4):
				self.sendDeck(self.clients2[self.givingDeckTo], str(game.deck))
			game.state = "waitDeck"
			

		# 6ºestado, receber o baralho cifrado e baralhado
		elif game.state == "waitDeck":
			if self.givingDeckTo == 4:
				self.givingDeckTo = 0
				game.state = "giveCards"
			else:
				for player in self.clients2:
					if player.id == self.clients2[self.givingDeckTo].id:
						if(len(player.msg) > 0):
							if(len(ast.literal_eval(player.msg[0])) == 52):
								game.deck = ast.literal_eval(player.msg[0])
								self.givingDeckTo +=1
								game.state = "giveDeck"
								player.msg.pop(0)
							else:
								print("Waiting...")
								game.state = "waitDeck"
	
		# 7ºestado, envia para o proximo jogador o baralho atualizado
		elif game.state == "giveCards":
			#random player 
			#self.givingDeckTo = random.choice(self.clients2)
			self.requestCard(self.clients2[self.givingDeckTo], str(game.deck))
			game.state = "waitforCards"

			
		# 8ºestado, recebe o baralho com menos cartas e envia para o proximo jogador	
		elif game.state == "waitforCards":
			for player in self.clients2:
				if(len(player.msg) > 0 ):
					#if(player.id == self.givingDeckTo.id):
					if player.id == self.clients2[self.givingDeckTo].id:	
						self.givingDeckTo = self.givingDeckTo + 1
						if self.givingDeckTo > 3:
							self.givingDeckTo = 0
						game.deck = ast.literal_eval(player.msg[0])
						player.msg.pop(0)
						game.state = "giveCards"
						if len(game.deck) == 0:
							self.givingDeckTo = 3
							game.state = "askKey"
						break
				else:  
					print("Waiting...")
					time.sleep(0.5)
					game.state = "waitforCards"
			

		# 9ºestado, decifrar as cartas de cada um tem na mão
		elif game.state == "askKey":
			#Pedir todas as chaves (asking, ...), quando o cliente receber um asking já sabe que tem de enviar a chave
			# enviar e esperar por recbeer
			self.sendMsg(self.clients2[self.givingDeckTo], "I need your keys", "REQUEST_KEY")
			game.state = "getKey"

		# 10ºestado, receber key
		elif game.state == "getKey":
			for player in self.clients2:
				if(len(player.msg) > 0 ):
					if player.id == self.givingDeckTo + 1:
						self.keys.append(player.msg[0])
						player.msg.pop(0)
						self.givingDeckTo = self.givingDeckTo - 1
						game.state = "askKey"
						break
				else:
					print("Waiting...")
					time.sleep(0.5)

			if len(self.keys) == 4:
				game.state = "sendKey" 
		# 	for player in table.players:
		# 		sendMsg(player, "Deck Commit")
		# 	table.confirmation_players = table.players.copy()
		# 	table.state = "deckCommit"

		elif game.state == "sendKey":
			for player in self.clients2:
				self.sendMsg(player, str(self.keys), "KEYS")
			game.state = "START"
		# 	for player in table.confirmation_players:
		# 		msg = readMsg(player)
		# 		if len(msg) > 0:
		# 			player.deckCommitment = msg
		# 			table.confirmation_players.remove(player)
		# 			table.checkHandCardsEndConditions()

		elif game.state == "START":
			pass
		# 	for player in table.players:
		# 		sendMsg(player,"Let's start the game. Player with the lower ID starts.")
		# 		player.playedCards = []
		# 		table.state = "startGame"

		# elif table.state == "startGame":
		# 	for player in table.confirmation_players:
		# 		msg = readMsg(player)
		# 		if "OK" in msg:
		# 			table.confirmation_players.remove(player)
		# 			table.checkStartGameConditions()

		# elif table.state == "round":
		# 	if table.round < 14: 
		# 		ended = round(table)
		# 		if ended:
		# 			table.state = "endRound"
		# 	else:
		# 		table.state = "endGame"

		# elif table.state == "endRound":
		# 	for player in table.confirmation_players:
		# 		msg = readMsg(player)
		# 		if "OK" in msg:
		# 			table.confirmation_players.remove(player)
		# 	table.checkNewRoundStartConditions()
		
		# elif table.state == "endGame":
		# 	table.gameScore()
		# 	for player in table.players:
		# 		sendMsg(player, "End game: 1."+str(table.players_score[0].name)+" "+str(table.points_score[0])+ "pts 2."+str(table.players_score[1].name)+" "+str(table.points_score[1])+ "pts 3."+str(table.players_score[2].name)+" "+str(table.points_score[2])+ "pts 4."+str(table.players_score[3].name)+" "+str(table.points_score[3])+ "pts")
		# 	table.state = "endGameConfirmation"
		# 	table.confirmation_players = table.players.copy()
		# 	mode = "plain"		
		# elif table.state == "endGameConfirmation":
		# 	for player in table.confirmation_players:
		# 		msg = readMsg(player)
		# 		if player.CC and len(msg) > 0:
		# 			CC.verifySign(msg,"OK",sec.getPubKey(player.id))
		# 			table.confirmation_players.remove(player)
		# 		elif "OK" in msg:
		# 			table.confirmation_players.remove(player)

		# 	if len(table.confirmation_players) == 0:
		# 		mode = ""
		# 		table.state = "init"
		# 		table.confirmation_players = table.players.copy()
	

s = Server()
s.start()
while True:
	s.receiveMsgs()
	## MANAGE NEW PLAYERS ##
	if len(s.clients) >= 4:
		s.newGame()
	# ## MANAGE TABLES ##
	for i in s.games:
		s.gameManage(i)

serversocket.close()