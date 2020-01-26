import socket, select, json
from termcolor import colored
from security.security import *
from security.cc import *
import random
import ast
import sys
import secrets
import base64
import hashlib

value = ['TWO ', 'THREE ', 'FOUR ', 'FIVE ', 'SIX ', 'SEVEN ', 'EIGHT ', 'NINE ', 'TEN ', 'JACK ', 'QUEEN ', 'KING ', 'ACE ']

class Client:
	def __init__(self):
		self.host = "127.0.0.1"
		self.port = 23562
		self.id = 0
		self.BUF_SIZE = 30000
		self.name = ""
		self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.inout = []
		self.new_msgs = []
		self.old_msgs = []
		self.typee = "" 
		self.hand = []
		self.cc = None
		self.key = ""
		self.keys = []
		self.cheat = False
	

	def connect(self):
		self.serversocket.connect((self.host, self.port))
		self.inout = [self.serversocket]
		return self.serversocket
		
	def sendMsg(self, message, receiver="server"):
		if receiver is not str:
			receiver = str(receiver)

		if receiver == "server":
			pack = {	"header": str(id)+"_"+receiver,
						"payload": message}
			
			self.serversocket.send(json.dumps(pack).encode())
		else:
			
		
			pack = {	"header": str(id)+"_"+receiver, 
						"payload": message, }
		
			self.serversocket.send(json.dumps(pack).encode())

	def sendDeck(self,deck,receiver="server"):
		if type(deck) is list:
			aux = deck
			deck = ' '.join(map(str, aux)) 
		pack = 	{	"header": str(id)+'_'+receiver,"TYPE": "DECK",
					"payload": deck}
		self.serversocket.send(json.dumps(pack).encode())
	
	def sendKey(self,deck,receiver="server"):
		if type(deck) is list:
			aux = deck
			deck = ' '.join(map(str, aux)) 
		pack = 	{	"header": str(id)+'_'+receiver,"TYPE": "KEY",
					"payload": deck}
		self.serversocket.send(json.dumps(pack).encode())

	def readMsg(self):
		if len(self.new_msgs) > 0:
			msg = self.new_msgs.pop(0)
			self.old_msgs.append(msg)
		else:
			msg = 0
		return msg

	def splitMsgs(self, msg):
		arr = msg.split('"')
		while "" in arr:
			arr.remove("")
		return arr 

	def getMsg(self):
		data = self.serversocket.recv(self.BUF_SIZE).decode()
		pack = json.loads(data)
		if "TYPE" in pack:
			self.typee = pack["TYPE"]
		msg = pack["payload"]
		print(pack)
		if type(msg) is str:
			arr = self.splitMsgs(msg)
			for msg in arr:
				#print(pack["header"].split("_")[0] + ":" + str(msg)) # print message when it receives
				self.new_msgs.append(msg)
		else:
			#print(str(msg)) # print message when it receives		
			self.new_msgs.append(msg)

	def getPlainMsg(self):
		data = self.serversocket.recv(self.BUF_SIZE).decode()
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

	def sendPlainMsg(self, message, receiver="server"):
		if receiver is not str:
			receiver = str(receiver)

		if type(message) is list:
			aux = message
			message = ' '.join(map(str, aux)) 

		if receiver == "server":
			pack = {	"header": '_'+str(id)+'_',
						"payload": message}
			self.serversocket.send(json.dumps(pack).encode())
		else:
			print(colored(message,"blue"))
			pack = {	"header": str(id)+"_"+receiver,
						"payload": message}
			self.serversocket.send(json.dumps(pack).encode())

	# Identificar-se ao server
	def join(self):
		while 1:
			print(colored("\033[1m = Choose Login Type = \n \033[0m ", "green"))
			print("1. Login with username\n")
			print("2. Login with CC\n")
			op = input("Option: ")
			
			# Username
			if op == "1":
				self.name = input("Username: ")
				self.sendPlainMsg(self.name)
				# Wait for answer
				self.getPlainMsg()
				data = self.readMsg()
				try:
					self.id = int(data.split(":")[1])
				except:
					self.id = -1

				return self.id
			# CC, não sei o que é para fazer a seguir	
			elif op == "2":
				self.cc = CitizenCard()
				self.name = self.cc.fullnames[0]
				self.sendPlainMsg(self.name)
				# Wait for answer
				self.getPlainMsg()
				data = self.readMsg()
				try:
					self.id = int(data.split(":")[1])
				except:
					self.id = -1

				return self.id

	#######################SEGURANÇA#########################
	# Criar chave secreta
	def generate_key(self, min, max):
		return secrets.token_bytes(random.randint(min, max))

	# Baralhar e cifrar o baralho que recebeu do servidor 
	def shuffleDeck(self, deck):
		deck_cipher = []
		deck = ast.literal_eval(deck)
		#Cifrar cada carta do baralho
		self.key = self.generate_key(16, 16)
		cipher = Security()
		cipher.generate_secret_key(base64.b64encode(self.key))
		for c in deck:
			deck_cipher.append(cipher.encrypt(c))		
		#Baralhar
		new_deck =[]
		random.shuffle(deck_cipher) 
		for i in range(0, len(deck_cipher)):
			new_deck.append(deck_cipher[i]) 
		return new_deck
	
	# Enviar baralho para o servidor (default server)
	def sendToServer(self, deck):
		sendPlainMsg(deck)

	# Tirar uma carta e enviar ao servidor	
	def getCard(self, deck):
		deck = ast.literal_eval(deck)
		# print("Deck: ",deck)
		# print("TYPE Deck: ",type(deck))
		card = deck.pop(0)
		self.hand.append(card)
		return deck
	
	# Parte do compromisso
	def commitment(self):
		R1 = self.generate_key(16, 16)
		R2 = self.generate_key(16, 16)
		hash1 = hashlib.sha256()
		hash1.update(R1)
		hash1.update(R2)
		for c in self.hand:
			hash1.update(bytes(c, 'utf-8'))
		hexa = hash1.hexdigest()
		print('The bit commitment of %s is %s'%(self.id, hexa))
		# FALTA A PARTE DE ASSINAR, perguntar ao DINIS
		return R1, R2, self.hand

	# Decifrar	
	def decryptHand(self, key):
		decipher_deck = []
		decipher = Security()
		for c in self.hand:	
			decipher.generate_secret_key(base64.b64encode(key[0]))
			decipher_card = decipher.decrypt(c)
			decipher.generate_secret_key(base64.b64encode(key[1]))
			decipher_card = decipher.decrypt(decipher_card)
			decipher.generate_secret_key(base64.b64encode(key[2]))
			decipher_card = decipher.decrypt(decipher_card)
			decipher.generate_secret_key(base64.b64encode(key[3]))
			decipher_card = decipher.decrypt(decipher_card)
			decipher_deck.append(decipher_card)
		self.hand = decipher_deck
		print(colored("My Cards: " + str(self.hand), "blue"))

	#######################JOGO#########################
	def getValueNaipe(self, last_card):
		return last_card.split()

	def playCard(self, last_card):
		possible_card = []
		cheat_card = []
		print("AQUIIIII; ", last_card)
		if last_card == "yourturn":
			possible_card = self.hand
		else:	
			last_card = self.getValueNaipe(last_card)
			card = ""
			# Todas as cartas que são possiveis de jogar
			for c in self.hand:
				if last_card[1] in c:
					possible_card.append(c)
			if len(possible_card) == 0:
				possible_card = self.hand
		
		# Perguntar que carta quer jogar
		while 1:
			print("Do you want to cheat? ")
			op = input("Y->Yes || N->No          \n")

			# eu tive uma ideiaaa !! na batota por exemplo se eu verificasse 
			# que ele jogou dois de copas, eu ia gerr todas as cartas possiveis de copas
			#  e ele depois podia escolher uma delas?? Mesmo que não tenha a carta
			# TER CUIDADO COM O REMOVE LÀ EM BAIXO
			if op == "Y" or op == "y":
				self.cheat = True
				# Mostrar ao jogador todas as cartas que são possiveis de ele jogar
				for v in value:
					cheat_card.append(v + last_card[1])
				print(cheat_card)

				print(colored("WHAT CARD DO YOU WANT TO PLAY ? \n"+str(cheat_card), "red"))
				while 1:
					card = int(input("Card(select index):"))
					if card <= len(cheat_card)-1:
						return cheat_card[card]
					else: 
						print("CHOOSE AGAIN, index out of range")
			
			# o jogador tem de jogar o indice onde está a carta
			if op == "N" or op == "n":
				print(colored("WHAT CARD DO YOU WANT TO PLAY ? \n"+str(possible_card), "red"))
				while 1:
					card = int(input("Card(select index):"))
					if card <= len(possible_card)-1:
						return possible_card[card]
					else: 
						print("CHOOSE AGAIN, index out of range")
	
c = Client()
serversocket = c.connect()
# Join the server
id = c.join()
deck = []

while id > 0:
	infds, outfds, errfds = select.select(c.inout, c.inout, [], 3)
	if infds:
		c.getMsg()
	msg = c.readMsg()
	if type(msg) is not int:
		#print(msg)
		if c.typee == "REQUEST_GAME":
			print(colored("\n" + c.name, "blue"))
			print("Do you accept to play the game ")
			op = input("Y->Yes || N->No          \n")
			if(str(op) == "Y" or str(op) == "y"):
				message = "I " + c.name + " with ID " + str(id) + " accept to play the game."
				c.sendMsg(message)
			else:
				c.sendMsg("NO")
		elif c.typee == "REQUEST_PLAY":
			print(colored(msg, "blue"))
			print("Do you accept to play to this oponnents: ")
			op = input("Y->Yes || N->No          \n")
			if(str(op) == "Y" or str(op) == "y"):
				message = "I " + c.name + " with ID " + str(id) + " accept to play against this player."
				c.sendMsg(message)
			else:
				c.sendMsg("NO")

		# recebe, baralha e cifra o baralho, e envia o baralho para o servidor
		# envia tambem o bit commitment
		elif c.typee == "DECK":
			print(colored("= SHUFFLE =", "blue"))
			deck = c.shuffleDeck(msg)
			c.sendDeck(str(deck))
		
		# recebe e tira uma carta, e depois envia para o servidor
		elif c.typee == "CARD":
			print(colored("= GET ONE CARD = ", "blue"))
			if(len(c.hand)<13):
				deck = c.getCard(msg)
				c.sendDeck(str(deck))
			else:
				c.sendDeck(str(msg))
		
		# recebe mensagem do servidor a pedir para enviar a key e envia
		elif c.typee == "REQUEST_KEY":
			c.sendKey(base64.b64encode(c.key).decode('utf-8'))
		# receber as chaves
		elif c.typee == "KEYS":
			msg = ast.literal_eval(msg)
			for i in msg:
				c.keys.append(base64.b64decode(i.encode('utf-8')))
			c.commitment()
			c.decryptHand(c.keys)
			print(colored("= I DECRYPT MY HAND = ", "blue"))
			c.sendMsg("OK")
		
		elif c.typee == "Askingfor2clubs":
			if "TWO CLUBS" in c.hand:
				c.hand.remove("TWO CLUBS")
				c.sendMsg("TWO CLUBS")
				print("EU TENHO ", c.name)
		
		# vê a jogada toda, aqui vai ser a verificação da batota
		elif c.typee == "RecivePlay":
			print(msg)
			
		elif c.typee =="PLAY":
			card = c.playCard(msg)
			print(card)
			c.sendMsg(card)
			# PERGUNTAR AO DINIS
			if c.cheat == False:
				c.hand.remove(card)
			
		elif c.typee == "wonround":
			print(msg)
			
		elif c.typee == "RoundPoints":
			print(colored("= POINTS TABLE =", "green"))
			print(colored(msg, "green"))
		
		elif c.typee == "WON_GAME":
			print(msg)
		
			
serversocket.close()