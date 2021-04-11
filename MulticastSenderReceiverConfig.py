#!/usr/bin/env python3

########################################################################

import socket
import argparse
import sys
import threading
import random
import ast

# Read in the config.py file to set various addresses and ports.
from config import *
########################################################################
# Echo Server class
########################################################################

command = {
    'getdir' : 1,
    'deleteroom' : 2,
    'makeroom' : 3,
    'bye' : 4
}
CDR = {}
class Server:

    HOSTNAME = 'localhost'
    PORT = 35000

    RECV_SIZE = 256
    BACKLOG = 10
    
    MSG_ENCODING = "utf-8"



    def __init__(self):
        self.thread_list = []
        self.create_listen_TCP()
        self.process_connections_forever()
        
    # Create the TCP server listen socket in the usual way.
    def create_listen_TCP(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind( (Server.HOSTNAME, Server.PORT) )
            self.socket.listen(Server.BACKLOG)
            print(f"Listening for file sharing connections on port {Server.PORT}")

        except Exception as msg:
            print(msg)
            sys.exit(1)

    def process_connections_forever(self):
        try:
            while True:
                new_client = self.socket.accept()
                new_thread = threading.Thread(target=self.connection_handler, args=(new_client,))
                self.thread_list.append(new_thread)
                new_thread.daemon = True
                new_thread.start()

        except Exception as msg:
            print(msg)
        except KeyboardInterrupt:
            print()
        finally:
            print("Closing tcp server socket ...")
            self.socket.close()
            sys.exit(1)

    def connection_handler(self, client):
        connection, address_port = client
        print("Connection received from {}.".format(address_port))

        while True:
            recvd_bytes = connection.recv(Server.RECV_SIZE)
            
            if len(recvd_bytes) == 0:
                print("Closing {} client connection ... ".format(address_port))
                connection.close()
                break
            recvd_str = recvd_bytes.decode(Server.MSG_ENCODING)
            print("Received: ", recvd_str)

            recvd_str, *recvd_arg = recvd_str.split()

            if(recvd_str == 'getdir'):
                Message = str(CDR)
                connection.sendall(Message.encode(Server.MSG_ENCODING))
                print("Sent: ", Message)
                
            if(recvd_str == 'makeroom'):
                if recvd_arg[0] in CDR:
                    Message = "Duplicated room name is sent"
                    connection.sendall(Message.encode(Server.MSG_ENCODING))
                    print("Sent: ", Message)
                else:
                    if [recvd_arg[1], recvd_arg[2]] in CDR.values():
                        Message = "The chat room IP address/port already exists."
                        connection.sendall(Message.encode(Server.MSG_ENCODING))
                        print("Sent: ", Message)
                    else:
                        CDR[recvd_arg[0]] = [recvd_arg[1], int(recvd_arg[2])]
                        Message = "New room created "
                        connection.sendall(Message.encode(Server.MSG_ENCODING))
                        print("Sent: ", Message)

            if(recvd_str == 'deleteroom'):
                if recvd_arg[0] in CDR:
                    CDR.pop(recvd_arg[0])
                    Message = "Room deleted"
                    connection.sendall(Message.encode(Server.MSG_ENCODING))
                    print("Sent: ", Message)
                else:
                    Message = "No matched room."
                    connection.sendall(Message.encode(Server.MSG_ENCODING))
                    print("Sent: ", Message)

            if(recvd_str == 'bye'):
                print("Closing {} client connection ... ".format(address_port))
                connection.close()
                break

########################################################################
# Echo Client class
########################################################################

class Client:

    SERVER_HOSTNAME = 'localhost'

    RECV_BUFFER_SIZE = 1024
    
    TTL = 1 # Hops
    TTL_SIZE = 1 # Bytes
    TTL_BYTE = TTL.to_bytes(TTL_SIZE, byteorder='big')
    
    def __init__(self):
        self.chat =0 
        self.CDR_Client = {}
        self.name = socket.gethostname()
        self.run()


    def run(self):
        print("Please input your commands here")
        while True:
            if(input("> ") == 'connect'):
                self.get_socket()
                self.connect_to_server()
                self.run_continue()
            else:
                print('Type connect to make a connection first')

    def get_socket(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def connect_to_server(self):
        try:
            self.socket.connect((Client.SERVER_HOSTNAME, Server.PORT))
        except Exception as msg:
            print(msg)
            sys.exit(1)
    
    def run_continue(self):
        while True:
            try:
                self.user_input = input("> ")
                if(self.user_input.startswith('chat')):
                    if len(self.user_input.split())!=2:
                        print('Invalid input. chat <chat room name>')
                    else:
                        if self.user_input.split()[1] in self.CDR_Client:
                            self.chat = 1
                            
                        else:
                            print("Chat room is not found...")
                        
                elif(self.user_input.startswith('name')):
                    if len(self.user_input.split())!=2:
                        print('Invalid input. name <chat name>')
                    else:
                         self.name = self.user_input.split()[1]

                else:#connection
                    if self.user_input.split()[0] in command:
                        self.socket.sendall(self.user_input.encode(Server.MSG_ENCODING))
                        self.connection_receive()
                    
                if(self.chat):
                    self.address = (self.CDR_Client[self.user_input.split()[1]][0],self.CDR_Client[self.user_input.split()[1]][1])
                    print (self.address)
                    new_chat = threading.Thread(target=self.Receive,daemon=True)
                    new_chat.start()
                    self.get_socket_UDP()

            except (KeyboardInterrupt, EOFError):
                print()
                print("Closing server connection ...")
                self.socket.close()
                sys.exit(1)



      


    def get_socket_UDP(self):


        try:
            self.socket_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            self.socket_sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, Client.TTL_BYTE)
            # self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, Client.TTL)  # this works fine too
        except Exception as msg:
            print(msg)
            sys.exit(1)

        while True:
            
            try:
                self.socket_sender.sendto(('\n' + self.name + ': ' + input('Chat mode: ')).encode('utf-8'), self.address)
            except KeyboardInterrupt:
                print("exit chat mode");
                #self.socket_sender.sendto(('end').encode('utf-8'), self.address)
                self.chat = 0

                break


    def Receive(self):
        print (self.address[1])
        RECV_SIZE = 256
        self.socket_rec = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_rec.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        # Bind to an address/port. In multicast, this is viewed as
        # a "filter" that determines what packets make it to the
        # UDP app.
        self.socket_rec.bind((RX_IFACE_ADDRESS, self.address[1]))
        multicast_group_bytes = socket.inet_aton(self.address[0])
        print("Multicast Group: ", self.address)
        # Set up the interface to be used.
        multicast_if_bytes = socket.inet_aton(RX_IFACE_ADDRESS)
        multicast_request = multicast_group_bytes + multicast_if_bytes
        self.socket_rec.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, multicast_request)
        while (self.chat == 1):
            try:
                #self.socket_rec.setblocking(False) 
                if (self.chat == 0):
                    #print("receive exit chat mode"); 
                    break
                else:
                    #print("waiting on recv")
                    data, address_port = self.socket_rec.recvfrom(RECV_SIZE)
                    recvd_bytes_decoded = data.decode("utf-8")
                    if (self.chat == 1):
                        print(recvd_bytes_decoded)
                    if len(data) == 0:
                        print("Closing server connection ... ")
                        self.socket_rec.close()
                        sys.exit(1)
            except KeyboardInterrupt:
                print("receive exit chat mode"); 
                #exit()
                break
            except Exception as msg:
                print(msg)
                sys.exit(1)

        print("receive exit chat mode"); 


    def connection_receive(self):
        try:
        
            recvd_bytes = self.socket.recv(Client.RECV_BUFFER_SIZE)
            recvd_bytes_decoded = recvd_bytes.decode(Server.MSG_ENCODING)
            if len(recvd_bytes) == 0:
                print("Closing server connection ... ")
                self.socket.close()
                sys.exit(1)
                
            if(self.user_input == "getdir"):
                self.CDR_Client = ast.literal_eval(recvd_bytes_decoded)
            print("List of rooms: ", recvd_bytes_decoded)

        except Exception as msg:
            print(msg)
            sys.exit(1)

########################################################################
# Process command line arguments if this module is run directly.
########################################################################

# When the python interpreter runs this module directly (rather than
# importing it into another file) it sets the __name__ variable to a
# value of "__main__". If this file is imported from another module,
# then __name__ will be set to that module's name.

if __name__ == '__main__':
    roles = {'client': Client,'server': Server}
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--role',
                        choices=roles, 
                        help='server or client role',
                        required=True, type=str)

    args = parser.parse_args()
    roles[args.role]()

########################################################################
