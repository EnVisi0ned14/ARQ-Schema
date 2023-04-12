import socket
import sys
import random

PORT_INDEX = 1
FILE_INDEX = 2
PROBABILITY_INDEX = 3

RESERVED = b'0000000000000000'
ACK_PACKET = b'1010101010101010'

acknowledgment = 0



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

def sendACK(server_socket: socket.socket, destination_addr, acknowledgment: int):

    # Create the header
    header = str(acknowledgment) + ";"
    header +=  RESERVED.decode() + ";"
    header += ACK_PACKET.decode() + ";"
    
    # Send the acknowledgment to the client
    server_socket.sendto(header.encode(), destination_addr)
    
# Open the file to write to
file = open(sys.argv[FILE_INDEX], "w")

# Create a socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind socket to local host on the SERVER_PORT
server_socket.bind(("0.0.0.0", int(sys.argv[PORT_INDEX])))

# Report status
print("[+] Listening for data...")

# Keep listening for connections
while True:

    # Read in the first packet sent by the client
    packet, clientAddress = server_socket.recvfrom(1024)

    while packet == None:
        # Read in the first packet sent by the client
        packet, clientAddress = server_socket.recvfrom(1024)
    
    # Grab the fields of the packet
    fields = packet.decode().split(";")

    # Break down the packet into fields
    sequence_number, checksum, packet_type, data = int(fields[0]), int(fields[1]), fields[2], fields[3]

    # Discard packet at probability
    if random.uniform(0, 1) <= float(sys.argv[PROBABILITY_INDEX]):
        print("Packet loss, sequence number = " + str(sequence_number))
        continue

    # Check for valid checksum
    if checksum != int(computeCheckSum(data)):
        print("[-] Data was corrupted. Checksum failed")

    # If the packet came out of order
    if acknowledgment != sequence_number:
        print("[-] Packet is out of order. Expected byte " + str(acknowledgment)+ " but was byte " + str(sequence_number))

    # Write the data out to a file
    file.write(data)

    # Update the sequence number
    acknowledgment += len(data)

    print("[+] Acknowledged Data: " + data)

    # Send the ACK packet
    sendACK(server_socket, clientAddress, acknowledgment)