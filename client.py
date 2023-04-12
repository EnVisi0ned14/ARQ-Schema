import socket
import threading
import sys
import os
import time

## --------------------------------------------

class Packet:
    def __init__(self, sequence_number: int, data: str):
        self.sequence_number = sequence_number
        self.data = data

## --------------------------------------------

HOST_NAME_INDEX = 1
PORT_INDEX = 2
FILE_INDEX = 3
WINDOW_INDEX = 4
MSS_INDEX = 5

DATA_PACKET = b'0101010101010101'

bytes_sent  = 0
sequence_number = 0
acknowledgment = 0

pending_packets: list[Packet] = []

## --------------------------------------------


def rdt_send(file_name: str, amount_read: int) -> str:

    if not os.path.isfile(file_name):
        print("[-] Please input a valid file")
        sys.exit()

    # Open the file
    file = open(file_name, "r")

    # Travel to the current byte to read
    file.seek(amount_read)

    # Read in the next character
    char = file.read(1)

    # Return the character which was read
    return char if char != '' else None

def computeCheckSum(data: str) -> str:
    
    checksum, sum = '', 0

    # Break the data into 16 bit segments
    chunks = [data[i:i+2] for i in range(0, len(data), 2)]

    # Calculate the sum of the chunks
    for chunk in chunks:
        
        # Convert chunk to binary representation
        binary = ''.join(format(ord(c), '08b') for c in chunk)

        # Add the binary to the sum
        sum += int(binary, 2)
    
    sum = bin(sum)

    # Remove the binary tags from the stream
    sum = sum.replace('0b', '')

    # Calculate the complement of the sum
    for i in sum:
        if i == '1':
            checksum += '0'
        else:
            checksum += '1'
    
    binary_value = int(checksum, 2)

    return str(binary_value)

def begin_timer(client_socket: socket.socket, sequence_number: int):

    # Timer set to one second
    time.sleep(1)

    # If the packet has already been acknowledged
    if acknowledgment > sequence_number:
        return
    
    # Find if the packet is still pending
    for packet in pending_packets:
        if packet.sequence_number == sequence_number:
            send_data(client_socket, sequence_number, packet.data, True)

def send_data(socket: socket.socket, start_byte: int, data: str, isRetransmission = False):
    global bytes_sent
    global sequence_number

    # Create the header
    header = str(start_byte) + ";"
    header += computeCheckSum(data) + ";"
    header += DATA_PACKET.decode() + ";"
    header += data

    # Send the data to the server
    socket.send(header.encode())

    # Begin the timer for the packet
    thread = threading.Thread(target=begin_timer, args=(client_socket, start_byte))

    # Countdown the timer
    thread.start()

    if not isRetransmission:

        # Add the packet as pending
        pending_packets.append(Packet(sequence_number, data))

        # Update the sequence number
        sequence_number += len(data)
        bytes_sent += len(data)

    


def listen_for_ack(client_socket: socket.socket):
    
    global acknowledgment
    global bytes_sent
    global sequence_number

    while True:
            
            # Read in the acknowledgment
            local_acknowledgmenet = int(client_socket.recv(1024).decode().split(";")[0])

            # If the new acknowledgment is more up to date
            if local_acknowledgmenet > acknowledgment:
                acknowledgment = local_acknowledgmenet

            # Update bytes sent
            bytes_sent = sequence_number - acknowledgment

            # Remove all packets which have been acknowledged
            for packet in pending_packets:
                if packet.sequence_number <= acknowledgment:
                    pending_packets.remove(packet)

            print("[+] Acknowledgment recieved")


# Create the client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Window Size 
window_size = int(sys.argv[WINDOW_INDEX])

# Connect to the server
try:
    client_socket.connect((sys.argv[HOST_NAME_INDEX], int(sys.argv[PORT_INDEX])))

    # Initalize the thread
    thread = threading.Thread(target=listen_for_ack, args=(client_socket,))

    # Start listening for acknowledgments
    thread.start()

    # Grab the file to transfer
    file_name = sys.argv[FILE_INDEX]

    # Initalize the buffer and pos for the file
    buffered_data, pos = '', 0

    # Read in the starting data
    read_contents = rdt_send(file_name, pos)
    
    # While there is more to read
    while read_contents != None:
        
        # Update the variables
        buffered_data = buffered_data + read_contents
        pos += 1

        # If the amount buffered is the MSS
        if len(buffered_data) == int(sys.argv[MSS_INDEX]):
            send_data(client_socket, sequence_number, buffered_data)

            # Reset the buffered_data
            buffered_data = ''

        # Respect the window size
        while bytes_sent >= window_size:
            pass

        # Read the next part of the file
        read_contents = rdt_send(file_name, pos)


except ConnectionRefusedError:
    print("The server is not started or could not be reached.")
    sys.exit()