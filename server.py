import socket, select, json
from Player import *
from Game import *
from security.cc import *
from security.security import *
import time
import ast
import base64 
import random

numbers = {"TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5, "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10, "JACK": 11, "QUEEN": 12, "KING": 13, "ACE": 14}
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
		self.startingPlayer = 0
		self.PlayToAssist = ""
		self.count = 0
		self.packs = []
		self.validlendeck = 0
		self.sec = Security()
		self.pubKey = self.sec.generateCertServer("Server")["pubKey"]

	def start(self):
		self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.serversocket.bind((self.host, self.port))
		self.serversocket.listen(5)
		self.inputs.append(self.serversocket)
	
	# Troca de mensagens
	def sendMsg(self, player, msg, typee):
		#Verifica se o jogador já está na mesa
		if player.inTable == 0:
			print("Player nº " + str(player.id) + " " + str(msg))
		
		if(typee == "REQUEST_PLAY"):
			keys = [] 
			signData = []
			names = []
			pos_cc = "None"
			for players in self.clients2:
				if(players.id == player.id):
					keys.append("0")
					signData.append("0")
					names.append("0")
					if player.CC == True:
						pos_cc = player.id
				else:
					keys.append(base64.b64encode(players.pubKey).decode("utf-8") )
					signData.append(base64.b64encode(players.aux).decode('utf-8'))
					names.append(players.name)
					if players.CC==True:
						pos_cc = players.id
			if type(msg) is list:
				aux = msg
				msg = ' '.join(map(str, aux)) 
	
			pack = 	{"header": "server_" + str(player.id),"TYPE":typee,"KEYS":str(keys),"signData":str(signData),"names":str(names),
					"payload": msg, "CCpos": pos_cc}

		elif typee == "REQUEST_GAME" or typee == "RoundPoints" or typee == "ReceivePlay" or typee == "Askingfor2clubs" or typee ==  "wonround" or typee == "WON_GAME":
			pack = 	{"header": "server_" + str(player.id),"TYPE":typee,"SIGNED":self.sec.sign(msg),"CERT":base64.b64encode(self.pubKey).decode("utf-8"),
					"payload": msg }
		else:
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
							if "SIGNED" in pack:
								self.packs = pack
							if "VALIDLENDECK" in pack:
								self.validlendeck = int(pack["VALIDLENDECK"])
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
			# AUTENTICAÇÃO COM CC
			if "TYPE" in pack:
				if pack["TYPE"] == "CC":
					if CitizenCard().verifyChainOfTrust(base64.b64decode(pack["CERT"].encode('utf-8'))) and CitizenCard().verifySign(base64.b64decode(pack["CERT"].encode('utf-8')), pack["payload"], base64.b64decode(pack["SIGNED"].encode('utf-8'))):
						print("Chain of trust verified")
						player = self.addPlayer(clientsocket)
						player.CC = True
						player.pubKey = base64.b64decode(pack["CERT"].encode('utf-8'))
						self.sendPlainMsg(player,"Welcome! You're nº: " + str(player.id))
						msg = pack["payload"] 		
						player.name = msg
						player.aux = base64.b64decode(pack["SIGNED"].encode('utf-8'))
						print(player.CC)
						print("ID:" + str(player.id) + " Name: " + player.name + " joined the game")
					
					
			else:
				# print(base64.b64decode(pack["CERT"].encode("utf-8")))
				pubk = Security().getpubKey(base64.b64decode(pack["CERT"].encode("utf-8")))
				# print("Assinatura no server : ",base64.b64decode(pack["SIGNED"].encode("utf-8")))
				if(Security().verifySign(pack["payload"], pack["SIGNED"], pubk)):
					print("ASSINATURA VALIDA")
					player = self.addPlayer(clientsocket)
					# Send the welcome message and inform the id
					self.sendPlainMsg(player,"Welcome! You're nº: " + str(player.id))
					msg = pack["payload"] 		
					player.name = msg
					player.pubKey = base64.b64decode(pack["CERT"].encode("utf-8"))
					player.aux = base64.b64decode(pack["SIGNED"].encode("utf-8"))
					print("ID:" + str(player.id) + " Name: " + player.name + " joined the game")
				else:
					print("Não foi possivel verificar a assinatura")
		else:
			print("Name: " + data + " tried to join but the table is full")
			# Send the welcome message and inform the id
			sendPlainMsg(player,"Sorry! The table is full. Come back later")

		

	def saveMsg(self, player, MSG):
		m = ""
		for message in MSG:
			m+=message

		for i in self.clients2:
			if(i.id==player.id):
				i.msg.append(m)
		

	def requestGame(self, player, game):
		self.sendMsg(player, "ACCEPT THE GAME","REQUEST_GAME")
		#time.sleep(2)
	
	def requestCard(self, player, deck):
		#Verifica se o jogador já está na mesa
		if player.inTable == 0:
			print("Player nº " + str(player.id) + " " + str(msg))
		
		if type(deck) is list:
			aux = deck
			deck = ' '.join(map(str, aux)) 
		pack = 	{	"header": "server_" + str(player.id),"TYPE": "CARD", "VALIDLENDECK": str(self.validlendeck),
					"payload": deck}
		player.socket.send(json.dumps(pack).encode())
		#self.sendMsg(player, deck,"CARD")
		#time.sleep(2)

	def cleanMsg(self):
		for client in self.clients2:
			client.msg.clear()
	
	def constructTablePoints(self):
		msg = ""
		for i in range(0, len(self.clients2)):
			msg = msg + self.clients2[i].name + ":" + str(self.clients2[i].points) + "\n"
		return msg
	
	# Confirmar que se jogou as cartas que tinha na mão originalemnte
	def confirmCommitment(self, R1, B, R2, hand):
		hash1 = hashlib.sha256()
		hash1.update(R1)
		hash1.update(R2)
		


	##########################JOGO##########################
	def newGame(self):
		self.games.append(Game())
		self.validlendeck = len(self.games[0].deck)
		for i in range(4):
			player = self.clients.pop(0)
			player.inTable = len(self.games)
			self.games[len(self.games)-1].set_players(player)
	
	# Saber quem vai ficar com os pontos
	def playerLose(self, deck_round):
		high_value = 0
		index = 0
		startCard_naipe = self.PlayToAssist.split()[1]
		for i in range(0,len(deck_round)):	
			tmpcard_value = deck_round[i].split()[0]
			tmpcard_naipe = deck_round[i].split()[1]

			tmpcard_value = numbers[deck_round[i].split()[0]]
	
			if tmpcard_value > high_value and tmpcard_naipe == startCard_naipe:
				high_value = tmpcard_value
				index = i
		return self.clients2[index]
	
	# Saber com quantos pontos ficou
	def updatePoints(self, deck_round, game):
		self.count = self.count + 1
		tmpcard_naipe = "" 
		tmpcard_value = ""
		player = self.playerLose(deck_round)
		print("Player:", player.name)
		self.sendMsg(player,"you won the hand","wonround")
		self.startingPlayer = player.id-1
		
		# REGRAS
		for card in deck_round:
			tmpcard_value = card.split()[0]
			tmpcard_naipe = card.split()[1]
			if "QUEEN" in tmpcard_value and "SPADES" in tmpcard_naipe:
				player.points = player.points + 13
			elif "HEART" in tmpcard_naipe:
				player.points = player.points + 1
		player.points = player.points

		# MUDAR ISTO PARA 100
		if player.points >= 100:
			game.state = "EndGame"

		# SE FICAREM SEM CARTAS MUDAR PARA O DISTRIBUIR BARALHO
		if self.count == 13:
			new_deck = Game().deck
			self.validlendeck = len(new_deck)
			game.deck = new_deck
			print(game.deck)
			self.keys = []
			self.startingPlayer = 0
			game.state = "BitComVerify"		

	
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
							#time.sleep(0.5)
							game.state = "waitForResponse"
		
		# 4ºestado, manda a mensagem a todos para estes aceitarem com quem qurem jogar uns
		# com os outros e recebem a resposta
		elif game.state == "PlayOpponents":
			if game.allAccept() == False:
				if self.flag2 == False: 
					for i in game.players_accept:
						print("Nomes que aceitaram jogar: ",i.name)
					op = ""
					for p in game.players_accept:
						op = ""
						for pla in game.players_accept:
							if pla.id != p.id:
								op = op + "\n                 " + pla.name
						self.sendMsg(p,"List of the players: " + op,"REQUEST_PLAY")
						#time.sleep(0.5)
					self.flag2 = True
				else:
					for player in game.players_accept:
						if(len(player.msg) > 0 ):
							if("accept to play" in player.msg[0]):
								game.addAcceptToplayWith(player)
								player.msg.pop(0)
								#time.sleep(2)
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
			#time.sleep(0.01)
			self.requestCard(self.clients2[self.givingDeckTo], str(game.deck))
			game.state = "waitforCards"

		# 8ºestado, recebe o baralho com menos cartas e envia para o proximo jogador	
		elif game.state == "waitforCards":
			for player in self.clients2:
				if(len(player.msg) > 0 ):
					#if(player.id == self.givingDeckTo.id):
					if player.id == self.clients2[self.givingDeckTo].id:
						if "end distribuition" in player.msg[0]:
							player.msg.pop(0)	
							self.givingDeckTo = 3 #para pedir as chaves para decifrar o baralho
							game.state = "askKey"
							break
						else:
							self.givingDeckTo = self.givingDeckTo + 1
							if self.givingDeckTo > 3:
								self.givingDeckTo = 0
							game.deck = ast.literal_eval(player.msg[0])
							player.msg.pop(0)
							#self.validlendeck = recebermsg
							game.state = "giveCards"
							break
				else:  
					print("Waiting...")
					#time.sleep(0.5)
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
				if len(player.msg) > 0:
					if player.id == self.givingDeckTo + 1:
						if player.CC == True:
							if CitizenCard().verifySign(base64.b64decode(self.packs["CERT"].encode('utf-8')), self.packs["BitCommit"], base64.b64decode(self.packs["SIGNED"].encode('utf-8'))):
								print("Bit commit was accepted")
								player.bitcom = ast.literal_eval(self.packs["BitCommit"])
								self.keys.append(player.msg[0])
								player.msg.pop(0)
								self.givingDeckTo = self.givingDeckTo - 1
								game.state = "askKey"
								break
							else:
								print("Bit commit was not accepted")
						else:
							#print("verify sign")
							pubk = Security().getpubKey(base64.b64decode(self.packs["CERT"].encode("utf-8")))
							if Security().verifySign(self.packs["BitCommit"], self.packs["SIGNED"], pubk):
								print("Bit commit was accepted")
								player.bitcom = ast.literal_eval(self.packs["BitCommit"])
								self.keys.append(player.msg[0])
								player.msg.pop(0)
								self.givingDeckTo = self.givingDeckTo - 1
								game.state = "askKey"
								break
							else:
								print("Bit commit was not accepted")
				
						# self.keys.append(player.msg[0])
						# player.msg.pop(0)
						# self.givingDeckTo = self.givingDeckTo - 1
						# game.state = "askKey"
						# break
				else:
					print("Waiting...")
					#time.sleep(0.01)

			if len(self.keys) == 4:
				self.givingDeckTo = 0
				game.state = "sendKey" 

		# 11ºestado, manda as keys na ordem que deve decifrar
		elif game.state == "sendKey":
			for player in self.clients2:
				self.sendMsg(player, str(self.keys), "KEYS")
			game.state = "waitConfDecript"

		# 12ºestado espera que seja decifrado		
		elif game.state == "waitConfDecript":
			for player in self.clients2:
				if(len(player.msg) > 0 ):
						if 'OK' in player.msg:
							player.msg.pop(0)
							self.givingDeckTo = self.givingDeckTo + 1
							game.state = "waitConfDecript"
						break
				else:
					print("Waiting...")
					#time.sleep(0.5)
			if self.givingDeckTo == 3:
				game.state = "START"
				self.givingDeckTo = 0
			
		#13ºestado aqui vamos perguntar quem tem o 2 paus para iniciar o jogo com 
		# essa carta
		elif game.state == "START":
			for player in self.clients2:
				self.sendMsg(player, "Do you have two of clubs", "Askingfor2clubs")
			game.state = "waitforstartplayer"
		
		# 14ºestado aqui vamos epera pelo 2 paus e depois começar o jogo enviando para o 
		# PLAY
		elif game.state == "waitforstartplayer":
			for player in self.clients2:
				if(len(player.msg) > 0 ):
						if "TWO CLUBS" in player.msg:
							if player.CC == True:
								if CitizenCard().verifySign(base64.b64decode(self.packs["CERT"].encode('utf-8')), self.packs["payload"], base64.b64decode(self.packs["SIGNED"].encode('utf-8'))):
									print("Card was accept")
									self.cleanMsg()
									game.cardsPlayed[player.id-1] = ("TWO CLUBS")
									self.startingPlayer = player.id - 1
									if(self.startingPlayer == 3):
										self.startingPlayer = 0
									else:
										self.startingPlayer = self.startingPlayer + 1

									self.PlayToAssist = "TWO CLUBS"
									for player in self.clients2:
										self.sendMsg(player, str(game.cardsPlayed), "RecivePlay")
									time.sleep(0.5)
									self.sendMsg(self.clients2[self.startingPlayer],self.PlayToAssist,"PLAY")
									game.state = "waitForPlay"
									break
								else:
									print("Card was not accept")
							else:
								pubk = Security().getpubKey(base64.b64decode(self.packs["CERT"].encode("utf-8")))
								if Security().verifySign(self.packs["payload"], self.packs["SIGNED"], pubk):
									print("Card was accept")
									self.cleanMsg()
									game.cardsPlayed[player.id-1] = ("TWO CLUBS")
									self.startingPlayer = player.id - 1
									if(self.startingPlayer == 3):
										self.startingPlayer = 0
									else:
										self.startingPlayer = self.startingPlayer + 1

									self.PlayToAssist = "TWO CLUBS"
									for player in self.clients2:
										self.sendMsg(player, str(game.cardsPlayed), "RecivePlay")
									time.sleep(0.5)
									self.sendMsg(self.clients2[self.startingPlayer],self.PlayToAssist,"PLAY")
									game.state = "waitForPlay"
									break
								else:
									print("Card was not accept")
				else:
					print("Waiting...")
					#time.sleep(0.5)

		elif game.state == "PLAY":
				#print("Eu Jogo: ",self.clients2[self.startingPlayer].name)
				for player in self.clients2:
					self.sendMsg(player, str(game.cardsPlayed), "RecivePlay")
				time.sleep(0.5)
				#print("Starting player",self.startingPlayer)
				self.sendMsg(self.clients2[self.startingPlayer],self.PlayToAssist,"PLAY")
				game.state = "waitForPlay"
				
		
		elif game.state == "waitForPlay":
			for player in self.clients2:
				if len(player.msg) > 0:
					if player.id == self.clients2[self.startingPlayer].id:
						if player.CC == True:
							if CitizenCard().verifySign(base64.b64decode(self.packs["CERT"].encode('utf-8')), self.packs["payload"], base64.b64decode(self.packs["SIGNED"].encode('utf-8'))):
								#print(type(player.msg[0]), player.msg[0])
								print("Card was accept")
								game.cardsPlayed[player.id-1]=player.msg[0]
								#proximo jogador
								if(self.startingPlayer == 3):
									self.startingPlayer = 0
								else:
									self.startingPlayer = self.startingPlayer + 1
								game.state = "PLAY"
								if(game.cardsPlayed.count(None) == 3):
									for play in game.cardsPlayed:
										if(play != None):
											self.PlayToAssist = play
								player.msg.pop(0)
								if len(game.cardsPlayed) == 4 and None not in game.cardsPlayed:
									for player in self.clients2:
										self.sendMsg(player, str(game.cardsPlayed), "RecivePlay")
									game.state = "verifyWhoWin"
								break
							else:
								print("Card was not accept")
						else:
							pubk = Security().getpubKey(base64.b64decode(self.packs["CERT"].encode("utf-8")))
							if Security().verifySign(self.packs["payload"], self.packs["SIGNED"], pubk):
								print("Card was accept")
								game.cardsPlayed[player.id-1]=player.msg[0]
								#proximo jogador
								if(self.startingPlayer == 3):
									self.startingPlayer = 0
								else:
									self.startingPlayer = self.startingPlayer + 1
								game.state = "PLAY"
								if(game.cardsPlayed.count(None) == 3):
									for play in game.cardsPlayed:
										if(play != None):
											self.PlayToAssist = play
								player.msg.pop(0)
								if len(game.cardsPlayed) == 4 and None not in game.cardsPlayed:
									for player in self.clients2:
										self.sendMsg(player, str(game.cardsPlayed), "RecivePlay")
									game.state = "verifyWhoWin"
								break
							else:
								print("Card was not accept")
				else:
					print("Waiting...")
					#time.sleep(0.5)

		#verifica quem  ganhou as cartas e recomeça o jogo 
		elif game.state == "verifyWhoWin":
			game.state = "PLAY"
			self.updatePoints(game.cardsPlayed, game) 
			# verificar a maior carta, o vencedor e os pontos
			tablePoints = self.constructTablePoints()
			game.cardsPlayed = [None for i in range(4)]
			self.PlayToAssist = "yourturn"
			#enviar pontos 
			for player in self.clients2:
				self.sendMsg(player,tablePoints,"RoundPoints")
		
		elif game.state == "BitComVerify":
			self.sendMsg(self.clients2[self.startingPlayer], )
			game.state = "giveDeck"	
			pass



		# Quem tem menos pontos ganha
		elif game.state == "EndGame":
			win_player = self.clients2[0]
			for player in self.clients2:
				#self.sendMsg(player,game.points)
				if(player.points < win_player.points):
					win_player = player
			print("Winnner: ",win_player.name) #mandar depois os resultadoss todos e a tabela de pontos
			self.sendMsgSigned(win_player,"Winner: "+ win_player.name + " with id " + str(win_player.id),"WON_GAME")
			game.state = "sendResult"
		
		elif game.state == "":
			recibo = "Winner"

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