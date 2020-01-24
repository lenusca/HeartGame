import socket, select, json
from termcolor import colored
import random
import ast
import sys

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
	

	def connect(self):
		self.serversocket.connect((self.host, self.port))
		self.inout = [self.serversocket]
		return self.serversocket

	def menu(self):
		while 1:
			print(colored("= Choose Login Type = \n", red))
			print("1. Login with username\n")
			print("2. Login with CC\n")
			op = input("Option: ")
			if op == 1:
				return
			elif op == 2:
				return

	def sendMsg(self, message, receiver="server"):
		if receiver is not str:
			receiver = str(receiver)

		if receiver == "server":
			pack = {	"header": str(id)+"_"+receiver,
						"payload": message}
			
			self.serversocket.send(json.dumps(pack).encode())
		else:
			
		
			pack = {	"header": str(id)+"_"+receiver,
						"payload": message}
		
			self.serversocket.send(json.dumps(pack).encode())

	def sendDeck(self,deck,receiver="server"):
		if type(deck) is list:
			aux = deck
			deck = ' '.join(map(str, aux)) 
		pack = 	{	"header": str(id)+'_'+receiver,"TYPE": "DECK",
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
		#print("pack receibider: ",pack)
		if("TYPE" in pack):
			self.typee = pack["TYPE"]
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

	def join(self):
		# Introduce yourself to the server
		self.name = sys.argv[1]
		self.sendPlainMsg(self.name)
		# Wait for answer
		self.getPlainMsg()
		data = self.readMsg()
		try:
			id = int(data.split(":")[1])
		except:
			id = -1

		return id

	# Baralhar e cifrar o baralho que recebeu do servidor 
	# VER A PARTE DO RETURN
	def shuffleDeck(self, deck):
		#Cifrar
	
		#Baralhar
		set = ast.literal_eval(deck)
		new_deck =[]
		random.shuffle(set) 
		for i in range(0, len(set)):
			new_deck.append(set[i]) 
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
		print(len(deck))
		return deck
	

c = Client()
serversocket = c.connect()
# Join the server
id = c.join()
bot = 0
# if len(sys.argv) > 2:
# 	if sys.argv[2] == "-b":
# 		bot = 1
deck = []

while id > 0:
	infds, outfds, errfds = select.select(c.inout, c.inout, [], 3)
	if infds:
		c.getMsg()
		
	msg = c.readMsg()
	

	if type(msg) is not int:
		if c.typee == "REQUEST_GAME":
		#if "ACCEPT THE GAME" in msg:
			print("Do you accept to play the game ")
			op = input("Y->Yes || N->No          \n")
			if(str(op) == "Y" or str(op) == "y"):
				message = "I " + sys.argv[1] + " with ID " + str(id) + " accept to play the game."
				c.sendMsg(message)
			else:
				c.sendMsg("NO")
		elif c.typee == "REQUEST_PLAY":
		#elif "ACCEPT TO PLAY" in msg:
			print("Do you accept to play to this oponnents: ")
		
			op = input("Y->Yes || N->No          \n")
			if(str(op) == "Y" or str(op) == "y"):
				message = "I " + sys.argv[1] + " with ID " + str(id) + " accept to play against this player."
				c.sendMsg(message)
			else:
				c.sendMsg("NO")

		# recebe e baralhar as mensagens, envia o baralho para o servidor
		elif c.typee == "DECK":
			#falta cifrar 
			deck = c.shuffleDeck(msg)
			c.sendDeck(str(deck))
		
		# recebe e tira uma carta, e depois envia para o servidor
		elif c.typee == "CARD":
			print(len(c.hand))
			if(len(c.hand)<13):
				deck = c.getCard(msg)
				c.sendDeck(str(deck))
			else:
				c.sendDeck(str(msg))
			

serversocket.close()