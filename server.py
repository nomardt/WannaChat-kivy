import socket
import threading
import random
#pip install loguru
from loguru import logger

def authenticate_new_users():
    while True:
        # Waiting for a new connection
        connection, address = server.accept()
        logger.success("New connection: " + str(address))

        # Try except in case the user disconnects before choosing a nickname
        try:
            # Getting the nickname of the new user
            nickname = connection.recv(1024).decode('utf-8')
            
            # Checking the nickname against the list of already occupied nicknames
            while nickname in nicknames:
                connection.send("STATUS:FAILURE".encode('utf-8'))
                nickname = connection.recv(1024).decode('utf-8')

            # Updating the lists
            clients.append(connection)
            nicknames.append(nickname)

            generate_a_welcome_message(nickname)

            # Starting a thread for the newly connected client
            threadie = threading.Thread(target=handle_the_connection, args=(connection, nickname))
            threadie.start()

        except:
            connection.close()
            logger.info(str(address) + " disconnected!")

def handle_the_connection(connection, nickname):
    while True:
        try:
            message = connection.recv(1024).decode('utf-8')
            broadcast(nickname + ": " + message)

        except:
            clients.remove(connection)
            nicknames.remove(nickname)
            connection.close()
            broadcast(nickname + " disconnected!")
            break

def broadcast(message):
    logger.info("BROADCAST | " + str(message))
    
    for client in clients:
        client.send(message.encode('utf-8'))

def generate_a_welcome_message(nickname):
    messages = {
        1: nickname + " just connected!",
        2: nickname + " just entered the party!",
        3: "Hello, " + nickname + "! Hope you brought pancakes!",
        4: "A wild brown " + nickname + " just appeared!",
        5: "Everyone welcome " + nickname + "!"
    }

    random_key = random.randint(1, 5)
    broadcast(messages[random_key])

if __name__ == "__main__":
    # Initial TCP Server setup
    server_address = socket.gethostbyname(socket.gethostname())
    server_port = 12345

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_address, server_port))
    server.listen()

    logger.success("Server started at " + server_address)

    # Waiting for connections that will be stored in the clients list
    clients = []
    nicknames = []
    authenticate_new_users()