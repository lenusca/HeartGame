import socket, select, json
from termcolor import colored
from security.security import *
from security.cc import *
import random
from random import randint
import ast
import sys
import secrets
import base64
import hashlib
import time
from collections import defaultdict


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
		self.peopleCheat = []
		self.verifyCheat = ""
		self.allverify = ""
		self.pubKey = "" 
		self.validLenDeck = 0
		self.ServerVerify = False
		self.DiffiePublic = []
		self.cheat = False
		self.count = 0
	

	def connect(self):
		self.serversocket.connect((self.host, self.port))
		self.inout = [self.serversocket]
		return self.serversocket
		
	def sendMsg(self, message, receiver="server",typee="default"):
		if receiver is not str:
			receiver = str(receiver)

		if receiver == "server":
			pack = {	"header": str(id)+"_"+receiver,
						"payload": message}
			
			self.serversocket.send(json.dumps(pack).encode())
		else:
			pack = {	"header": str(id)+"_"+receiver, "TYPE":typee,
						"payload": message }
			
			self.serversocket.send(json.dumps(pack).encode())

	def sendDeck(self,deck,receiver="server"):
		if type(deck) is list:
			aux = deck
			deck = ' '.join(map(str, aux)) 
		pack = 	{	"header": str(id)+'_'+receiver,"TYPE": "DECK", "VALIDLENDECK": str(self.validLenDeck),
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
			if(pack["TYPE"] == "SendingReques_diffie"):
				id_client_recebido = int(pack["header"].split("_")[1])
				self.DiffiePublic = (pack["payload"])

		if "VALIDLENDECK" in pack:
			self.validLenDeck = int(pack["VALIDLENDECK"])
		if "CERT" in pack: 
			self.verifyautServer(pack["SIGNED"], pack["payload"], pack["CERT"])
			
		
		if pack["TYPE"] == "WON_GAME":
			if self.ServerVerify == True:
				if self.cc == None:
					signed = self.sec.sign(pack["SIGNED"])
					self.sendMsgSigned2(pack["SIGNED"], base64.b64encode(self.pubKey).decode("utf-8"))
				else:
					signed = base64.b64encode(self.cc.signData(pack["SIGNED"])).decode('utf-8')
					self.sendMsgSigned2(pack["SIGNED"], base64.b64encode(self.cc.getCerts()).decode("utf-8"))

			else:
				print(colored("Server not autheticated ", "red"))

		msg = pack["payload"]
		if type(msg) is str:
			arr = self.splitMsgs(msg)
			for msg in arr:
				self.new_msgs.append(msg)
		else:		
			self.new_msgs.append(msg)

	def getPlainMsg(self):
		data = self.serversocket.recv(self.BUF_SIZE).decode()
		pack = json.loads(data)
		msg = pack["payload"]

		if type(msg) is str:
			arr = self.splitMsgs(msg)
			for msg in arr:
				self.new_msgs.append(msg)
		else:	
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
	
	# Para enviar o bitcommit assinado
	def sendMsgSigned(self, message, bitcommit,certificate):
		if self.cc != None:
			pack = {"header": str(id)+"_server", "CERT": certificate,"BitCommit":bitcommit , "SIGNED": base64.b64encode(self.cc.signData(bitcommit)).decode('utf-8'),
					"payload": message}
		else:
			pack = {"header": str(id)+"_server", "CERT": certificate,"BitCommit":bitcommit , "SIGNED": self.sec.sign(bitcommit),
					"payload": message}
		self.serversocket.send(json.dumps(pack).encode())
	
	# Mensagens normais assinadas
	def sendMsgSigned2(self, message, certificate):
		if self.cc != None:
			pack = {"header": str(id)+"_server", "CERT": certificate, "SIGNED": base64.b64encode(self.cc.signData(message)).decode('utf-8'),
					"payload": message}
		else:
			pack = {"header": str(id)+"_server", "CERT": certificate, "SIGNED": self.sec.sign(message), 
					"payload": message}
			
		self.serversocket.send(json.dumps(pack).encode())

	# Ligar-se ao servidor
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

	# Verificar assinaturas do server
	def verifyautServer(self, Signature, original, cert):
		pub = Security().getpubKey(base64.b64decode(cert.encode('utf-8')))
		self.ServerVerify = Security().verifySign(original, Signature, pub)
		if self.ServerVerify == True:
			print(colored("\nServer signature verified", "green"))
		else:
			print(colored("\nServer signature not valid", "red")) 

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
		self.validLenDeck = len(deck) 
		return new_deck
	
	# Enviar baralho para o servidor (default server)
	def sendToServer(self, deck):
		sendPlainMsg(deck)

	# Tirar uma carta e enviar ao servidor	
	def getCard(self, deck, valid):
		deck = ast.literal_eval(deck)
		index = random.randint(0, valid-1)
		card = deck.pop(index)
		deck.append("0")
		self.validLenDeck = self.validLenDeck - 1 
		self.hand.append(card)
		return deck
	
	# Parte do compromisso, onde envia o R1 e o B para o servidor
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
		self.commit = [R1,R2,hexa] 
	
	# Verificar compromisso, recebo um dicionario com o id das várias pessoas e o commit de cada[R1, b, R2, c]
	def verifyCommitment(self, commit):
		for i in commit:
			commit[i] =  ast.literal_eval(commit[i])
			# print(i, commit[i])
			R1 = commit[i][0]
			R2 = commit[i][2]
			hash1 = hashlib.sha256() 
			hash1.update(R1)
			hash1.update(R2)
			for card in commit[i][3]:
				hash1.update(bytes(card, 'utf-8'))
			b = hash1.hexdigest()
			if b != commit[i][1]:
				self.peopleCheat.append(i)

	# Verificar compromisso, recebo um dicionario com o 
	# id das várias pessoas e o commit de cada[R1, b, R2, c, cartaacusada]
	# Jogado sempre 
	def verifyPlayerCommitment(self, commit):
		# print(commit.replace('\r','\\r').replace('\n','\\n'))
		# print(type(commit))
		commit = ast.literal_eval(commit)
		R1 = commit[0]
		R2 = commit[2]
		hash1 = hashlib.sha256() 
		hash1.update(R1)
		hash1.update(R2)
		for card in commit[3]:
			hash1.update(bytes(card, 'utf-8'))
		b = hash1.hexdigest()
		if b == commit[1]:
			tet = self.verifyCommitmentCheat(commit[3], commit[4])
			return tet
		else:
			print(colored("Bit Commitment Incorrect", "red"))
			return False

	#Decifrar e verificar se a carta existe naquele baralho decifrado
	def verifyCommitmentCheat(self, hand, card ):
		
		decipher_deck = []
		# print(card)
		decipher = Security()
		for c in hand:	 
			decipher.generate_secret_key(base64.b64encode(self.keys[0]))
			decipher_card = decipher.decrypt(c)
			decipher.generate_secret_key(base64.b64encode(self.keys[1]))
			decipher_card = decipher.decrypt(decipher_card)
			decipher.generate_secret_key(base64.b64encode(self.keys[2]))
			decipher_card = decipher.decrypt(decipher_card)
			decipher.generate_secret_key(base64.b64encode(self.keys[3]))
			decipher_card = decipher.decrypt(decipher_card)
			decipher_deck.append(decipher_card)
		# print("AQUI: ", decipher_deck)
		for c in decipher_deck:
			# se for verdade houve batota
			if str(c) == str(card):
				return True
			# se não, não houve
		
		return False 

	# Decifrar	
	def decryptHand(self, key):
		self.keys = key
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
		
		
	# Verificar a autenticação de todos os clientes
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
		deck = ast.literal_eval(deck)
		for card in deck:
			for c in self.hand:
				if card == c:
					print(colored("SOMEONE PLAYED MY CARD", "red"))
					self.verifyCheat = c
	
	# Trocar de cartas com o deck que recebe
	def swapCard(self, deck, validCards):
		if validCards < len(self.hand):
			numcards = random.randint(0, validCards-1)
		else:
			numcards = random.randint(0, len(self.hand)-1)
		deck = ast.literal_eval(deck)
		for i in range(0,numcards):
			indexcard = random.randint(0, validCards-1)
			indexmycard = random.randint(0, len(self.hand)-1)
			# guardar cartas
			card = deck[indexcard]
			mycard = self.hand[indexmycard]
			# trocar as cartas
			deck[indexcard] = mycard
			self.hand[indexmycard] = card
		return deck

	
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
				
c = Client()
serversocket = c.connect()

# # Join the server
# while 1 :
# 	print(colored("\n\033[1m-----  ----- ----- ------ -----", "red"))
# 	print(colored("\n\033[1m|      |   | |   | |    | |    ", "red"))
# 	print(colored("\n\033[1m|      |   |  ---- |----|  ----", "red"))
# 	print(colored("\n\033[1m|      |   | |     |    |      |", "red"))
# 	print(colored("\n\033[1m-----  ----- |     |    |  -----", "red"))
# 	print("0. LOGIN\n")
# 	print("1. HISTORIC\n")
# 	op = input("Option: \n")
# 	if op == "0":
id = c.join()
	# if op == "1":
	# 	file = open("Games/Game0.txt", "r")
	# 	print(file.read())
	# 	file.close()
deck = []
flag = False
while id > 0:
	infds, outfds, errfds = select.select(c.inout, c.inout, [], 3)
	if infds:
		c.getMsg()
	msg = c.readMsg()
	

	if type(msg) is not int:
		# if flag == True:
		# 	flag = False
		# 	#perguntar quando é melhor fazer esta troca
		# 	for i in range(0,4):
		# 		if i != c.id:
		# 			c.sendMsg(base64.b64encode(c.sec.pubKeyDH).decode("utf-8"), i, "public_keys")
			
		#print(msg)
		if c.typee == "REQUEST_GAME":
			if c.ServerVerify == True:
				print(colored("\n\033[1m" + c.name+"\033[0m", "red"))
				print("Do you accept to play the game ")
				flag = True
				op = input("Y->Yes || N->No          \n")
				if str(op) == "Y" or str(op) == "y":
					message = "I " + c.name + " with ID " + str(id) + " accept to play the game."
					c.sendMsg(message)
				if str(op) == "N" or str(op) == "n":
					c.sendMsg("NO")
			else:
				print("Server not autheticated")

		elif c.typee == "REQUEST_PLAY":
			if(c.allverify):
				print(colored("\nAll clients were verified\n","green"))
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
				
###########			DIFFIE	####################################			
		# elif c.typee == "Reques_diffie":
		# 	c.sendMsg(base64.b64encode(c.sec.pubkeyDH).decode("utf-8"), "server" ,"Diffiepublic_keys")
			
		# elif c.typee == "SendingReques_diffie":
		# 	print("Guardei as chaves diffie")
		# 	for k in c.DiffiePublic:
		# 		pub = c.sec.getpubDHKey(base64.b64decode(k.encode('utf-8')))
		# 		c.sec.gensharedKey(pub)

		# recebe, baralha e cifra o baralho, e envia o baralho para o servidor
		# envia tambem o bit commitment
		elif c.typee == "DECK":
			print(colored("\033[1m= SHUFFLE =", "red"))
			deck = c.shuffleDeck(msg)
			c.sendDeck(str(deck))
		
		# recebe e tira uma carta, e depois envia para o servidor
		elif c.typee == "CARD":		
			if c.validLenDeck != 0:
				# pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[c.id-1].encode('utf-8')))
				# print("pub",pub)
				# print("MENSAGEM:",msg)
				# msg = c.sec.decrypt_DH(pub,base64.b64decode(msg.encode('utf-8')),c.sec.shared_key[c.id-1])
				
				percentagem = randint(0, 100)
				# print(c.id)
				if percentagem <= 5:
					if(len(c.hand)<13):
						deck = c.getCard(msg, c.validLenDeck)
						print(colored("\033[1m= GET ONE CARD = \033[0m", "red"))
						# if(c.id+1 == 5):
						# 	pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[0].encode('utf-8')))
						# else:
						# 	pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[c.id].encode('utf-8')))
						# c.sendDeck(base64.b64encode(c.sec.encrypt_DH(pub,str(deck),c.sec.shared_key[c.id])).decode("utf-8"))
						c.sendDeck(str(deck))
					else:
						c.sendDeck(str(msg))
						# if(c.id+1 == 5):
						# 	pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[0].encode('utf-8')))
						# else:
						# 	pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[c.id].encode('utf-8')))						
						# c.sendDeck(base64.b64encode(c.sec.encrypt_DH(pub,str(msg),c.sec.shared_key[c.id])).decode("utf-8"))
						
				if percentagem > 5:
					if percentagem > 50:
						print(colored("\033[1m= PASS DECK = \033[0m", "red"))
						# if(c.id+1 == 5):
						# 	pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[0].encode('utf-8')))
						# else:
						# 	pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[c.id].encode('utf-8')))
						# c.sendDeck(base64.b64encode(c.sec.encrypt_DH(pub,str(msg),c.sec.shared_key[c.id])).decode("utf-8"))
						c.sendDeck(str(msg))
					elif len(c.hand) != 0: 
						if percentagem <= 50:
							print(colored("\033[1m= SWAP CARD = \033[0m", "red"))
							# print(c.validLenDeck)
							# deck = c.swapCard(msg, c.validLenDeck)
							# if(c.id+1 ==5):
							# 	pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[0].encode('utf-8')))
							# else:
							# 	pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[c.id].encode('utf-8')))
							# c.sendDeck(base64.b64encode(c.sec.encrypt_DH(pub,str(deck),c.sec.shared_key[c.id]).decode("utf-8")))
							deck = c.swapCard(msg, c.validLenDeck)
							c.sendDeck(str(deck))
					else: 
						print(colored("\033[1m= PASS DECK = \033[0m", "red"))
						# if(c.id+1 == 5):
						# 	pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[0].encode('utf-8')))
						# else:
						# 	pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[c.id].encode('utf-8')))
						# c.sendDeck(base64.b64encode(c.sec.encrypt_DH(pub,str(msg),c.sec.shared_key[0])).decode("utf-8"))
						
						c.sendDeck(str(msg))
						
			else:
				c.sendMsg("end distribuition")
				# print("envio o fim da dist")

		# elif c.typee == "CARD2":		
		# 	if c.validLenDeck != 0:

		# 		# pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[c.id-1].encode('utf-8')))
		# 		# msg = c.sec.decrypt_DH(pub,base64.b64decode(msg.encode('utf-8')))
		# 		print("MENSAGEM:",msg)
		# 		percentagem = randint(0, 100)
		# 		print(c.id)
		# 		if percentagem <= 5:
		# 			if(len(c.hand)<13):
		# 				deck = c.getCard(msg, c.validLenDeck)
		# 				print(colored("\033[1m= GET ONE CARD = \033[0m", "red"))
		# 				if(c.id+1 == 5):
		# 					pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[0].encode('utf-8')))
		# 				else:
		# 					pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[c.id].encode('utf-8')))
		# 				c.sendDeck(base64.b64encode(c.sec.encrypt_DH(pub,str(deck),c.sec.shared_key[c.id])).decode("utf-8"))
		# 			else:
		# 				#c.sendDeck(str(msg))
		# 				if(c.id+1 == 5):
		# 					pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[0].encode('utf-8')))
		# 				else:
		# 					pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[c.id].encode('utf-8')))						
		# 				c.sendDeck(base64.b64encode(c.sec.encrypt_DH(pub,str(msg),c.sec.shared_key[c.id])).decode("utf-8"))
		# 		if percentagem > 5:
		# 			if percentagem > 50:
		# 				print(colored("\033[1m= PASS DECK = \033[0m", "red"))
		# 				if(c.id+1 == 5):
		# 					pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[0].encode('utf-8')))
		# 				else:
		# 					pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[c.id].encode('utf-8')))
		# 				c.sendDeck(base64.b64encode(c.sec.encrypt_DH(pub,str(msg),c.sec.shared_key[c.id])).decode("utf-8"))
		# 				# c.sendDeck(str(msg))
		# 			elif len(c.hand) != 0: 
		# 				if percentagem <= 50:
		# 					print(colored("\033[1m= SWAP CARD = \033[0m", "red"))
		# 					print(c.validLenDeck)
		# 					deck = c.swapCard(msg, c.validLenDeck)
		# 					if(c.id+1 ==5):
		# 						pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[0].encode('utf-8')))
		# 					else:
		# 						pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[c.id].encode('utf-8')))
		# 					c.sendDeck(base64.b64encode(c.sec.encrypt_DH(pub,str(deck),c.sec.shared_key[c.id]).decode("utf-8")))
		# 					# c.sendDeck(str(deck))
		# 			else: 
		# 				print(colored("\033[1m= PASS DECK = \033[0m", "red"))
		# 				if(c.id+1 == 5):
		# 					pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[0].encode('utf-8')))
		# 				else:
		# 					pub = c.sec.getpubDHKey(base64.b64decode(c.DiffiePublic[c.id].encode('utf-8')))
		# 				c.sendDeck(base64.b64encode(c.sec.encrypt_DH(pub,str(msg),c.sec.shared_key[0])).decode("utf-8"))
		# 				# c.sendDeck(str(msg))
						
		# 	else:
		# 		c.sendMsg("end distribuition")
		# 		print("envio o fim da dist")
			
		
		# recebe mensagem do servidor a pedir para enviar a key e envia
		elif c.typee == "REQUEST_KEY":
			#print("MINHA CHAVE: ", c.key)
			c.commitment()
			# R1 e o Hexa
			lista = [c.commit[0],c.commit[2]]
			if c.cc != None:
				c.sendMsgSigned(base64.b64encode(c.key).decode('utf-8'), str(lista), base64.b64encode(c.cc.getCerts()).decode("utf-8"))
			else:
				c.sendMsgSigned(base64.b64encode(c.key).decode('utf-8'), str(lista), base64.b64encode(c.pubKey).decode("utf-8"))
			#c.sendKey(base64.b64encode(c.key).decode('utf-8'))
			# Enviar o bit commitment, o r1 e C
			
		# receber as chaves
		elif c.typee == "KEYS":
			# print(msg) #inprime as chaves
			msg = ast.literal_eval(msg)
			for i in msg:
				c.keys.append(base64.b64decode(i.encode('utf-8')))
			c.decryptHand(c.keys)
			print(colored("\033[1m= I DECRYPT MY HAND = \033[0m", "red"))
			c.sendMsg("OK")
			#c.keys = []
			
	
		elif c.typee == "Askingfor2clubs":
			if c.ServerVerify == True:
				if "TWO CLUBS" in c.hand:
					c.hand.remove("TWO CLUBS")
					# ASSINAR COM ECC
					if c.cc == None:
						c.sendMsgSigned2("TWO CLUBS", base64.b64encode(c.pubKey).decode("utf-8"))
					# ASSINAR COM CC
					else:
						c.sendMsgSigned2("TWO CLUBS", base64.b64encode(c.cc.getCerts()).decode("utf-8"))
					print(colored("\n\033[1mI have the Two Clubs \033[0m", "red"), str(c.name))
			else:
				print("Server not autheticated")
		
		# vê a jogada toda, aqui vai ser a verificação da batota
		elif c.typee == "RecivePlay":
			if c.ServerVerify == True:
				c.validationCard(msg)
				print(colored("\n\033[1mTable: "+msg+"\033[0m\n", "magenta"))
			else:
				print(colored("Server not autheticated", "red"))
		# ASSINAR AQUI
		elif c.typee =="PLAY":
			print(colored("\033[1mMy Cards:\033[0m " + str(c.hand), "red"))
			card = c.playCard(msg)
			# ASSINADA COM ECC
			if c.cc == None:
				c.sendMsgSigned2(card, base64.b64encode(c.pubKey).decode("utf-8"))
			# ASSINAR COM CC (RSA)
			else:
				c.sendMsgSigned2(card, base64.b64encode(c.cc.getCerts()).decode("utf-8"))
			
			if c.cheat == False:
				c.hand.remove(card)
			else:
				c.hand.pop(0)
			
		elif c.typee == "wonround":
			if c.ServerVerify == True:
				print(colored("\n"+ msg + "\n" ,"red"))
				
			else:
				print(colored("Server not autheticated", "red"))
			
		elif c.typee == "RoundPoints":
			if c.ServerVerify == True:
				print("\n#######################################")
				print(colored("\033[1m= POINTS TABLE =\033[0m", "red"))
				print(colored("\033[1m"+msg+"\033[0m", "red"))
				print("#######################################\n")
				if c.verifyCheat != "":
				# # [R2, c, cartaacusada]	
					lista = [c.commit[1], c.handCipher, c.verifyCheat]
					c.sendMsg(str(lista), "server", "CHEATED")	
					
				else:
					c.sendMsg("ALL OK", "server", "CHEATED")
				
			else:
				print("Server not autheticated")
		
		elif c.typee == "REVEALCHEAT":	
			if c.verifyCheat != "" or c.verifyPlayerCommitment(msg) == True:
				c.sendMsg("falhou")
				time.sleep(0.5)
				c.hand = []
				c.handCipher = []
				c.keys = [] 

			else:
				c.sendMsg("all oasdasdasdasdasdask")
				time.sleep(0.5)


		elif c.typee == "ASKINGFORBITCOMMITMENT":
			# enviar o R2, deck cifrado e carta acusada
			lista = [c.commit[1], c.handCipher]	
			if c.cc != None:
				c.sendMsgSigned2(str(lista), base64.b64encode(c.cc.getCerts()).decode("utf-8"))
			else:
				c.sendMsgSigned2(str(lista), base64.b64encode(c.pubKey).decode("utf-8"))
		
		elif c.typee == "end13rounds":
			c.hand = []
			print(msg)

		elif c.typee == "REVEAL":
			c.verifyCommitment(msg)
			if c.peopleCheat == []:
			
				c.sendMsg("tudo ok")
			else:
				c.sendMsg("falhou")

		elif c.typee == "WON_GAME":
			print(colored("\n\033[1m"+ msg + "\033[0m\n" ,"red"))
			
		
		elif c.typee == "LOADFILE":
			print(colored("\n\033[1m _____  _____   _____   _____   ____       * *   * * \033[0m", "red"))
			print(colored("\n\033[1m|      |     | |     | |     | |         *     *     * \033[0m", "red"))
			print(colored("\n\033[1m|      |     | |_____| |_____| |____     *           * \033[0m", "red"))
			print(colored("\n\033[1m|      |     | |       |     |      |      *       *   \033[0m", "red"))
			print(colored("\n\033[1m|_____ |_____| |       |     |  ____|        *   *  \033[0m", "red"))
			print(colored("\n\033[1m                                               *   \033[0m", "red"))
 
			file = open("Games/Game0.txt", "r")
			print(file.read())
			file.close()
			print(colored("\n\033[1mBYE BYE CROUPIER\033[0m", "red"))
			sys.exit(0)
		
		elif c.typee == "public_keys":
			print(c.DiffiePublic)
	
			
serversocket.close()