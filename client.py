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
		self.handCipher = []
		self.commit = []
		self.cc = None
		self.sec = None
		self.key = ""
		self.keys = []
		self.cheat = False
		self.verifyCheat = False
		self.allverify = ""
		self.pubKey = "" 
	

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
			if(pack["TYPE"] == "REQUEST_PLAY"):
				self.allverify = self.verifyClients(pack)
		msg = pack["payload"]
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

	def sendPlainMsg(self, message, certificate = None, receiver="server", cc = False):
		if receiver is not str:
			receiver = str(receiver)

		if type(message) is list:
			aux = message
			message = ' '.join(map(str, aux)) 
		if cc == True:
			if receiver == "server":
				pack = {	"header": '_'+str(id)+'_', "TYPE": "CC", "CERT": certificate, "SIGNED": base64.b64encode(self.cc.signData(message)).decode('utf-8'),
							"payload": message}
				self.serversocket.send(json.dumps(pack).encode())
			else:
				pack = {	"header": str(id)+"_"+receiver, "TYPE": "CC", "CERT": certificate, "SIGNED": self.cc.signData(message),
							"payload": message}
				self.serversocket.send(json.dumps(pack).encode())
		
		else:	
			if receiver == "server":
				pack = {	"header": '_'+str(id)+'_', "CERT": certificate, "SIGNED": self.sec.sign(message),
							"payload": message}
				self.serversocket.send(json.dumps(pack).encode())
			else:
				pack = {	"header": str(id)+"_"+receiver, "CERT": certificate, "SIGNED": self.sec.sign(message),
							"payload": message}
				self.serversocket.send(json.dumps(pack).encode())
	
	def sendMsgSigned(self, message, bitcommit,certificate):
		if self.cc != None:
			pack = {"header": str(id)+"_server", "CERT": certificate,"BitCommit":bitcommit , "SIGNED": base64.b64encode(self.cc.signData(bitcommit)).decode('utf-8'),
					"payload": message}
		else:
			pack = {"header": str(id)+"_server", "CERT": certificate,"BitCommit":bitcommit , "SIGNED": self.sec.sign(bitcommit),
					"payload": message}
		self.serversocket.send(json.dumps(pack).encode())
	
	def sendMsgSigned2(self, message, certificate):
		if self.cc != None:
			pack = {"header": str(id)+"_server", "CERT": certificate, "SIGNED": base64.b64encode(self.cc.signData(message)).decode('utf-8'),
					"payload": message}
		else:
			pack = {"header": str(id)+"_server", "CERT": certificate, "SIGNED": self.sec.sign(message),
					"payload": message}
		self.serversocket.send(json.dumps(pack).encode())

	# Identificar-se ao server
	def join(self):
		while 1:
			print(colored("\033[1m= Choose Login Type = \n \033[0m ", "red"))
			print("1. Login with username\n")
			print("2. Login with CC\n")
			op = input("Option: ")
			
			# Username
			if op == "1":
				self.name = input("Username: ")
				self.sec = Security()
				keys = self.sec.generateCertClient(self.name)
				self.pubKey = keys["pubKey"]
				# file.read(-1)
				self.sendPlainMsg(self.name,base64.b64encode(keys["pubKey"]).decode("utf-8"))
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
				certificate = self.cc.getCerts()
				self.sendPlainMsg(self.name, base64.b64encode(certificate).decode('utf-8'), "server", True)
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
		self.handCipher = self.hand
		for c in self.hand:
			hash1.update(bytes(c, 'utf-8'))
		hexa = hash1.hexdigest()
		#print('The bit commitment of %s is %s'%(self.id, hexa))
		self.commit = [R1,R2,hexa] 

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
		print(colored("\033[1mMy Cards:\033[0m " + str(self.hand), "red"))
	
	def verifyClients(self,pack):
		keys = ast.literal_eval(pack["KEYS"])
		signData = ast.literal_eval(pack["signData"])
		names = ast.literal_eval(pack["names"])
		count = 0		
		if(pack["CCpos"]=="None"):
			for i in range(0,len(keys)):
				if(keys[i]!="0"):
					if(Security().verifySign(names[i],signData[i],Security().getpubKey(base64.b64decode(keys[i].encode("utf-8"))))): 
						count = count + 1
		else:
			for i in range(0,len(keys)):
				print(pack["CCpos"])
				if(keys[i]!="0" and i != int(pack["CCpos"])-1):
					if(Security().verifySign(names[i],signData[i],Security().getpubKey(base64.b64decode(keys[i].encode("utf-8"))))): 
						count = count + 1
				elif keys[i]!="0" and i == int(pack["CCpos"])-1:
					if(CitizenCard().verifySign(base64.b64decode(keys[i].encode("utf-8")),names[i],base64.b64decode(signData[i].encode("utf-8")))):
						count = count + 1
			
		if(count == 3):
			return True
		else:
			return False



	#######################JOGO#########################
	def getValueNaipe(self, last_card):
		return last_card.split()

	def validationCard(self, deck):
		for card in deck:
			for c in self.hand:
				if card == c:
					print("Someone cheated")
					self.verifyCheat = True

	def playCard(self, last_card):
		possible_card = []
		cheat_card = []
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
			print("Do you want to play or verified if someone cheated?")
			op = input("[0]Play/[1]Cheat: ")
			if op == "0":
				while 1:
					print("Do you want to cheat? ")
					op = input("Y->Yes || N->No          \n")

					if op == "Y" or op == "y":
						self.cheat = True
						# Mostrar ao jogador todas as cartas que são possiveis de ele jogar
						for v in value:
							cheat_card.append(v + last_card[1])

						print(colored("\033[1mWHAT CARD DO YOU WANT TO PLAY ? \033[0m\n"+str(cheat_card), "red"))
						while 1:
							card = int(input("Card(select index):"))
							if card <= len(cheat_card)-1:
								return cheat_card[card]
							else: 
								print("CHOOSE AGAIN, index out of range")
					
					# o jogador tem de jogar o indice onde está a carta
					if op == "N" or op == "n":
						print(colored("\033[1mWHAT CARD DO YOU WANT TO PLAY ? \033[0m\n"+str(possible_card), "red"))
						while 1:
							card = int(input("Card(select index):"))
							if card <= len(possible_card)-1:
								return possible_card[card]
							else: 
								print("CHOOSE AGAIN, index out of range")
			if op == "1":
				self.sendMsg("Verified Cheat")	
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
			print(colored("\n\033[1m" + c.name+"\033[0m", "red"))
			print("Do you accept to play the game ")
			
			op = input("Y->Yes || N->No          \n")
			if str(op) == "Y" or str(op) == "y":
				message = "I " + c.name + " with ID " + str(id) + " accept to play the game."
				c.sendMsg(message)
			if str(op) == "N" or str(op) == "n":
				c.sendMsg("NO")

		elif c.typee == "REQUEST_PLAY":
			if(c.allverify):
				print(colored("\033[1m TODOS OS PLAYERS FORAM VERIFICADOS \033[0m","green"))
				print(colored("\033[1m"+msg+"\033[0m", "red"))
				print("Do you accept to play to this oponnents: ")
				op = input("Y->Yes || N->No          \n")
				if(str(op) == "Y" or str(op) == "y"):
					message = "I " + c.name + " with ID " + str(id) + " accept to play against this player."
					c.sendMsg(message)
				else:
					c.sendMsg("NO")
			else:
				print(colored("Erro, alguem não foi autenticado","red"))
					

		# recebe, baralha e cifra o baralho, e envia o baralho para o servidor
		# envia tambem o bit commitment
		elif c.typee == "DECK":
			print(colored("\033[1m= SHUFFLE =", "red"))
			deck = c.shuffleDeck(msg)
			c.sendDeck(str(deck))
		
		# recebe e tira uma carta, e depois envia para o servidor
		elif c.typee == "CARD":
			print(colored("\033[1m= GET ONE CARD = \033[0m", "red"))
			if(len(c.hand)<13):
				deck = c.getCard(msg)
				c.sendDeck(str(deck))
			else:
				c.sendDeck(str(msg))
		
		# recebe mensagem do servidor a pedir para enviar a key e envia
		elif c.typee == "REQUEST_KEY":
			print("MINHA CHAVE: ", c.key)
			c.commitment()
			lista = [c.commit[0], c.commit[1]]
			if c.cc != None:
				c.sendMsgSigned(base64.b64encode(c.key).decode('utf-8'), str(lista), base64.b64encode(c.cc.getCerts()).decode("utf-8"))
			else:
				c.sendMsgSigned(base64.b64encode(c.key).decode('utf-8'), str(lista), base64.b64encode(c.pubKey).decode("utf-8"))
			#c.sendKey(base64.b64encode(c.key).decode('utf-8'))
			# Enviar o bit commitment, o r1 e C
			
		# receber as chaves
		elif c.typee == "KEYS":
			print(msg)
			msg = ast.literal_eval(msg)
			for i in msg:
				c.keys.append(base64.b64decode(i.encode('utf-8')))
			c.decryptHand(c.keys)
			print(colored("\033[1m= I DECRYPT MY HAND = \033[0m", "red"))
			c.sendMsg("OK")
			c.keys = []
	
	
		elif c.typee == "Askingfor2clubs":
			if "TWO CLUBS" in c.hand:
				c.hand.remove("TWO CLUBS")
				# ASSINAR COM ECC
				if c.cc == None:
					c.sendMsgSigned2("TWO CLUBS", base64.b64encode(c.pubKey).decode("utf-8"))
				
				# ASSINAR COM CC
				else:
					c.sendMsgSigned2("TWO CLUBS", base64.b64encode(c.cc.getCerts()).decode("utf-8"))
				print("EU TENHO ", c.name)
		
		# vê a jogada toda, aqui vai ser a verificação da batota
		elif c.typee == "RecivePlay":
			print(msg)
		
		# ASSINAR AQUI
		elif c.typee =="PLAY":
			print("pronto a jogar")
			card = c.playCard(msg)
			# ASSINADA COM ECC
			if c.cc == None:
				c.sendMsgSigned2(card, base64.b64encode(c.pubKey).decode("utf-8"))
			# ASSINAR COM CC (RSA)
			else:
				c.sendMsgSigned2(card, base64.b64encode(c.cc.getCerts()).decode("utf-8"))
				
			# PERGUNTAR AO DINIS
			if c.cheat == False:
				c.hand.remove(card)
			
		elif c.typee == "wonround":
			print(msg)
			
		elif c.typee == "RoundPoints":
			print("\n#######################################")
			print(colored("\033[1m= POINTS TABLE =\033[0m", "red"))
			print(colored("\033[1m"+msg+"\033[0m", "red"))
			print("#######################################\n")

		#elif c.typee == "REVEAL":
	
		

		elif c.typee == "WON_GAME":
			print("########################END#########################")
			print(msg)
		
			
serversocket.close()