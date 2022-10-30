import socket
import threading
import random
from loguru import logger

def authenticate_new_users() -> None:
    """
    The method is used to wait for new connections 
    and start threads for new users
    """
    while True:
        # Waiting for a new connection
        connection, address = server.accept()
        logger.success("New connection: " + str(address))

        # Try except in case the user disconnects 
        # before choosing a nickname
        try:
            # Getting the nickname of the new user
            nickname = connection.recv(1024).decode('utf-8')
            
            # Checking the nickname against the list 
            # of already occupied nicknames
            while nickname in nicknames:
                connection.send("STATUS:FAILURE".encode('utf-8'))
                nickname = connection.recv(1024).decode('utf-8')

            # Updating the lists
            clients.append(connection)
            nicknames.append(nickname)

            generate_a_welcome_message(nickname)

            # Starting a thread for the newly connected client
            threadie = threading.Thread(target=handle_the_connection, 
                                        args=(connection, nickname))
            threadie.start()

        except Exception:
            connection.close()
            logger.info(str(address) + " disconnected!")

def handle_the_connection(connection, nickname) -> None:
    """
    This method receives the messages from the connected client.
    It is put in a thread for every connected user with a nickname.

    :type connection: Socket object
    :type nickname: str
    """
    while True:
        # Error will occur when the user disconnects from the server
        try:
            message = connection.recv(1024).decode('utf-8')
            broadcast(nickname + " > " + message)

        except Exception:
            clients.remove(connection)
            nicknames.remove(nickname)
            connection.close()
            broadcast(nickname + " disconnected!")
            break

def broadcast(message) -> None:
    """
    It sends the message to every connected client

    :type message: str
    """
    if "STATUS:TYPING" not in message:
        logger.info("BROADCAST | " + str(message))
    
    for client in clients:
        client.send(message.encode('utf-8'))

def generate_a_welcome_message(nickname) -> None:
    """
    It broadcasts a random welcome message 
    after the user has chosen a unique nickname

    :type nickname: str
    """
    messages = (
               nickname + " just connected!",
               nickname + " just entered the party!",
               "Hello, " + nickname + "! Hope you brought pancakes!", 
               "A wild brown " + nickname + " just appeared!", 
               "Everyone welcome " + nickname + "!"
               )

    random_greeting = random.choice(messages)
    broadcast(random_greeting)

if __name__ == "__main__":
    # Initial TCP Server setup
    server_address = socket.gethostbyname(socket.gethostname())
    server_port = 12345

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_address, server_port))
    server.listen()

    logger.success("Server started at " + server_address)

    # Waiting for new connections
    clients = []
    nicknames = []
    authenticate_new_users()