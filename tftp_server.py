# There is NO off-the-shelf TFTP libraries used.
# All of these libraries are allowed for the project
import socket # python socket library
from threading import Thread # python thread library
import sys # handles command-line argument
import random # randomly selects ephemeral port
import struct # used to support binary mode

# reference: specification at https://tools.ietf.org/html/rfc1350

# main is at the bottom

def put_file(filename, user_ip,user_port):
    socket_put = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_put.settimeout(timeout)
    num_blk = 0
    num_ack = 0

    # ephemeral ports i.e. random temporary port
    eph_port = random.randint(1024, 65000) # first 1024 ports are reserved so cannot be used
    while socket_put.bind(('', eph_port)) == False:
        eph_port = random.randint(1024, 65000)

    try:
        f = open(filename,'ab') # opens file for appending in binary format
    except:
        no_file_error = struct.pack('!hhhb', 5, 5, 5, num_blk)
        socket_put.sendto(no_file_error, client_address)
        exit() # Exits with informational message when ERROR

    while True:
        if num_blk == num_ack:
            ack = struct.pack('!hh', 4, num_ack)
            num_ack += 1
            socket_put.sendto(ack, client_address)
        else:
            socket_put.sendto(ack, client_address)

        try:
            wr = socket_put.recv(1024)
            op = struct.unpack('!h', wr[:2])

            if op[0] == 3: # DATA packet
                num_blk = struct.unpack('!h', wr[2:4])[0]

                if num_blk == num_ack:
                    wr_data = wr[4:]
                    f.write(wr_data)

                if (num_blk == num_ack) and (len(wr_data) < 512): # the last data block (this program supports 512-byte data blocks)
                    ack = struct.pack('!hh', 4, num_ack)
                    socket_put.sendto(ack, client_address)
                    f.close()
                    print('WRQ for {} Completed'.format(filename))
                    exit() # done, so stop

        except socket.timeout:
            print('timeout, so retransmitting'); continue # supports retransmiting DATA and ACK messages after timeout


def get_file(filename, client_address, timeout):
    socket_get = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_get.settimeout(timeout)
    num_blk = 0
    num_ack = 0

    # ephemeral ports i.e. random temporary port
    eph_port = random.randint(1024, 65000) # first 1024 ports are reserved so cannot be used
    while socket_get.bind(('', eph_port)) == False:
        eph_port = random.randint(1024, 65000)

    try:
        f = open(filename,'rb') # reading in binary format
    except:
        no_file_error = struct.pack('!hhhb', 5, 5, 5, num_blk)
        socket_get.sendto(no_file_error, client_address)
        exit() # Exits with informational message when ERROR

    while True:
        if num_blk == num_ack:
            num_blk += 1
            datablock = f.read(512) # supports 512-byte data blocks

        data_to_send = struct.pack('!hh', 3, num_blk) + datablock
        socket_get.sendto(data_to_send, client_address)

        if len(datablock) < 512: # the last data block
            f.close()
            print('RRQ for {} Completed'.format(filename))
            exit() # done, so stop

        try: 
            ack =  socket_get.recv(1024)
            op, num_ack = struct.unpack("!hh", ack)
        except socket.timeout:
            print('timeout, so retransmitting'); continue # supports retransmiting DATA and ACK messages after timeout


if __name__ == '__main__':
    # Accepts server port number as first positional command-line argument
    server_port = int(sys.argv[1])

    # Accepts retransmission timeout (in milliseconds) as second positional command-line argument
    timeout = int(sys.argv[2]) / 1000 # milliseconds converted to microseconds

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Uses UDP as underlying transport protocol
    s.bind(('', server_port)) # 127.0.0.1

    print('The server is ready to receive')

    while True:

        data_received, client_address = s.recvfrom(1024) # Client connected to server port
        print('First packet has been received: {} from (ip) {}, (port) {}'.format(data_received, client_address[0], client_address[1]))
        
        op = struct.unpack('!h', data_received[:2]) # either (1,) or (2,) for RRQ/WRQ
        filename = data_received[2:-7].decode()
            
        if op[0] == 1: # support read (RRQ) requests from TFTP clients
            print('RRQ: "get {}" received'.format(filename))
            rrq_thread = Thread(target = get_file, args = (filename, client_address, timeout))
            rrq_thread.start() 

        elif op[0] == 2: # support write (WRQ) requests from TFTP clients
            print('WRQ: "put {}" received'.format(filename))
            wrq_thread = Thread(target = put_file, args = (filename, client_address, timeout))
            wrq_thread.start()