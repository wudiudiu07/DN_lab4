import socket
import argparse
import sys
import time
import struct
import threading
########################################################################

# Read in the config.py file to set various addresses and ports.
from config import *

########################################################################
# Broadcast Server class
########################################################################
command = {
    'getdir' : 1,
    'deleteroom' : 2,
    'makeroom' : 3,
    'bye' : 4
}
class Sender:

    # HOSTNAME = socket.gethostbyname('')
    HOSTNAME = 'localhost'
    PORT=35000

    TIMEOUT = 2
    RECV_SIZE = 1024
    BACKLOG = 5
    
    MSG_ENCODING = "utf-8"
    # MESSAGE =  HOSTNAME + "multicast beacon: "
    MESSAGE = "Hello from " 
    MESSAGE_ENCODED = MESSAGE.encode('utf-8')

    TTL = 1 # Hops
    TTL_SIZE = 1 # Bytes
    TTL_BYTE = TTL.to_bytes(TTL_SIZE, byteorder='big')
    # OR: TTL_BYTE = struct.pack('B', TTL)

    def __init__(self):
        self.create_listen_socket()
        self.send_messages_forever()
        self.chatroom = []
        self.thread_list = []
        

    def create_listen_socket(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, Sender.TTL_BYTE)
            # self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, Sender.TTL)  # this works fine too
            self.socket.bind(("0.0.0.0", 0))  # This line may be needed.
            print(f"Listening for connections")
        except Exception as msg:
            print(msg)
            sys.exit()

    def send_messages_forever(self):
        try:
            while True:
                #print("Sending multicast packet (address, port): ", MULTICAST_ADDRESS_PORT)
                #self.socket.sendto(Sender.MESSAGE_ENCODED, MULTICAST_ADDRESS_PORT)
                #print("flag")  
                new_client = self.socket.recvfrom(1024)            
                new_thread = threading.Thread(target=self.connection_handler,args=(new_client,))
                #self.discovery_thread = threading.Thread(target=self.service_announcement)
                self.thread_list.append(new_thread)
                # Start the new thread running.
                print("Starting serving thread: ", new_thread.name)
                new_thread.daemon = True
                new_thread.start()
                
                #time.sleep(Sender.TIMEOUT)
                
                
        except Exception as msg:
            print(msg)
        except KeyboardInterrupt:
            print()
        finally:
            self.socket.close()
            sys.exit()
    
    def connection_handler(self, receiver):
        connection, address_port = receiver
        print("Connection received from {}.".format(address_port))

        while True:
            recvd_bytes,address = connection.recvfrom(Sender.RECV_SIZE)
            if len(recvd_bytes) == 0:
                print("Closing {} client connection ... ".format(address_port))
                connection.close()
                break
            recvd_str = recvd_bytes.decode(Sender.MSG_ENCODING)
            print("Received: ", recvd_str)
            
            recvd_str, *recvd_arg = recvd_str.split()

            if(recvd_str == 'getdir'):
                CDR = []
                for entry in self.chatroom:
                    CDR.append(entry)
                current_list = json.dumps(CDR)
            # Send the received bytes back to the receiver.
                self.socket.sendto(current_list.encode('utf-8'),address)
                print("Sent: ", current_list)

            elif(recvd_str == 'makeroom'):
                if recvd_arg[0] in self.chatroom:
                    Message = "Room already existed"
                    self.socket.sendto(Message.encode('utf-8'),address)
                    print("Room already existed: ", Message)
                else:
                    for entry in self.chatroom:
                        if (recvd_arg[1]==entry[1] && (int(recvd_arg[2])==entry[2]):
                        Message = "The chat room IP address/port already exists. Please use another name"
                        self.socket.sendto(Message.encode('utf-8'),address)
                        print("Sent: ", Message)
                    else:
                        self.chatroom.append(recvd_arg[0],recvd_arg[1],int(recvd_arg[2])
                        Message = "The chat room is created"
                        self.socket.sendto(Message.encode('utf-8'),address)
                        print("Sent: ", Message)


            elif(recvd_str == 'deleteroom'):
                if recvd_arg in self.chatroom:
                    self.chatroom.remove(recvd_arg)
                    Message = "Successfully delete the room"
                    self.socket.sendto(Message.encode('utf-8'),address)
                    print("Sent: ", Message)
                else:
                    Message = "No matched chat room. Please use another name"
                    self.socket.sendto(Message.encode('utf-8'),address)
                    print("Sent: ", Message)


            if(recvd_str == 'bye'):
                print("Closing {} receiver connection ... ".format(address_port))
                connection.close()
                break
                
########################################################################
# Echo Receiver class
########################################################################

class Receiver:

    RECV_SIZE = 256

    def __init__(self):

        print("Bind address/port = ", BIND_ADDRESS_PORT)
        
        self.get_socket()
        self.receive_forever()
    def connect_to_CRDS(self):
        while True:
            if(input("Please Enter Command: ") == 'connect'):
                self.get_socket()
                self.connect_to_sender()
                self.receive_forever()
            else:
                print('Should firstly connect to CRDS')
    def connect_to_sender(self):
        try:
            # Connect to the sender using its socket address tuple.
            self.socket.connect((Receiver.SERVER_HOSTNAME, Sender.PORT))
        except Exception as msg:
            print(msg)
            sys.exit(1)
    def get_socket(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

            # Bind to an address/port. In multicast, this is viewed as
            # a "filter" that determines what packets make it to the
            # UDP app.
            self.socket.bind(BIND_ADDRESS_PORT)

            ############################################################
            # The multicast_request must contain a bytes object
            # consisting of 8 bytes. The first 4 bytes are the
            # multicast group address. The second 4 bytes are the
            # interface address to be used. An all zeros I/F address
            # means all network interfaces.
            ############################################################
                        
            multicast_group_bytes = socket.inet_aton(MULTICAST_ADDRESS)

            print("Multicast Group: ", MULTICAST_ADDRESS)

            # Set up the interface to be used.
            multicast_if_bytes = socket.inet_aton(RX_IFACE_ADDRESS)

            # Form the multicast request.
            multicast_request = multicast_group_bytes + multicast_if_bytes

            # You can use struct.pack to create the request, but it is more complicated, e.g.,
            # 'struct.pack("<4sl", multicast_group_bytes,
            # int.from_bytes(multicast_if_bytes, byteorder='little'))'
            # or 'struct.pack("<4sl", multicast_group_bytes, socket.INADDR_ANY)'

            # Issue the Multicast IP Add Membership request.
            print("Adding membership (address/interface): ", MULTICAST_ADDRESS,"/", RX_IFACE_ADDRESS)
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, multicast_request)
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def receive_forever(self):
        while True:
            try:
                data, address_port = self.socket.recvfrom(Receiver.RECV_SIZE)
                address, port = address_port
                print("Received: ", data.decode('utf-8'), " Address:", address, " Port: ", port)
            except KeyboardInterrupt:
                print(); exit()
            except Exception as msg:
                print(msg)
                sys.exit(1)

########################################################################
# Process command line arguments if run directly.
########################################################################

if __name__ == '__main__':
    roles = {'receiver': Receiver,'sender': Sender}
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--role',
                        choices=roles, 
                        help='sender or receiver role',
                        required=True, type=str)

    args = parser.parse_args()
    roles[args.role]()
