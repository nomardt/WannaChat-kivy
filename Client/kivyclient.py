#!/usr/bin/env python
# encoding: utf-8
import logging
import socket
import threading
from time import sleep
from kivy import require as kivy_require
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
# Makes the program look sharper on Windows systems
try:
    from ctypes import windll, c_int64
    windll.user32.SetProcessDpiAwarenessContext(c_int64(-4))

except ImportError:
    pass

except Exception as e:
    logging.error(e)
    exit()


class EnterIP(Screen):
    '''
    The first screen where the user enters the IP address of the server
    '''
    def establish_connection(self) -> None:
        """
        Establishing the connection after 'enter' is pressed
        """
        self.server_address = self.address.text
        self.server_port = 12345

        try:
            client.connect((self.server_address, self.server_port))

        except Exception:
            # Prevent loop formation
            self.address.text = ""

            # Updating the GUI in case the entered IP addr is invalid
            self.label_not_found.text = "Server not found!"


class EnterNickname(Screen):
    '''
    The second screen where the user enters her/his nickname
    '''
    def check_if_nickname_is_entered(self) -> None:
        """
        Checking if the user has entered a nickname after she/he presses 'enter' 
        """
        global my_nickname
        my_nickname = self.nickname.text

        if len(my_nickname) > 0:
            self.check_if_nickname_is_taken()

    def check_if_nickname_is_taken(self) -> None:
        """
        The nickname the user entered is checked against the server's list of nicknames
        """
        # Sending the nickname the user has just entered in the InputField
        client.send(my_nickname.encode('utf-8'))

        # The server returns 'STATUS:FAILURE' if the entered nickname is already present
        if client.recv(1024).decode('utf-8') == 'STATUS:FAILURE':
            # Showing the result of the comparison in GUI
            self.label_enter_nick.text = "Nickname unavailable!"

            # Removing the input to prevent loop formation
            self.nickname.text = ""

        else:
            # Proceeding to the next screen if the nickname is available
            self.manager.current = "WannaChat_main"

            # This thread will be waiting for messages from the server
            receive_thread = threading.Thread(target=ChatMainPage().receive)
            receive_thread.daemon = True
            receive_thread.start()


class ChatMainPage(Screen):
    '''
    The third screen with the functionality to send messages and 
    read those written by other clients
    '''
    def __init__(self, **kw):
        super().__init__(**kw)

        # This constantly adds to GUI the elements stored in chat_history_gui
        Clock.schedule_interval(self.receive_helper, 0.25)

    def message_send(self) -> None:
        """
        It sends the message after the user has pressed the "send" button
        """
        try:
            client.send(self.entered_message.text.encode('utf-8'))

            # Refreshing the text input field
            sleep(0.1)
            self.entered_message.text = ""

        except (ConnectionAbortedError, ConnectionResetError):
            WannaChatApp().close_application()

    def receive(self) -> None:
        """
        It is constantly waiting for messages from the server, 
        works in a thread called every 0.25 seconds
        """
        global chat_history_gui
        global who_is_typing

        while True:
            try:
                # Waiting for new messages
                self.just_received = client.recv(1024).decode('utf-8')

                if "STATUS:TYPING" in self.just_received:
                    # Handling notifications that somebody else is typing
                    if my_nickname not in self.just_received:
                        # Setting TTL to the dictionary of users currently typing
                        nickname_of_sender = self.just_received.split(" > ")[0]
                        who_is_typing[nickname_of_sender] = 25
                    
                    else:
                        pass

                # Handling ordinary messages
                elif " > " in self.just_received:
                    # Preventing message forgery achieved by sending "\nAnother_user_nickname > "
                    message_body = self.just_received.split(" > ", 1)[1]
                    message_body = message_body.replace(" > ", "")
                    self.just_received = self.just_received.split(" > ")[0] + " > " + message_body

                    chat_history_gui += self.just_received + "\n"

                # Handling welcome messages, disconnected notifications
                else:
                    chat_history_gui += self.just_received + "\n"

            except ConnectionResetError:
                WannaChatApp().close_application()

    def receive_helper(self, *aw) -> None:
        """
        Kivy can't change GUI elements outside the main thread 
        so this method is needed
        """
        global who_is_typing

        # Refreshing the GUI
        self.chat_history.text = chat_history_gui
        self.label_typing.text = ""

        for self.typing_user in who_is_typing:
            # Handling the case when only one user is typing
            if len(who_is_typing) == 1:
                self.label_typing.text = self.typing_user + " is typing..."

            # Handling the case when multiple users are typing but 
            # everybody else is already present on the screen
            elif self.typing_user == list(who_is_typing)[-1]:
                self.label_typing.text += self.typing_user + " are typing..."

            # Handling the case when multiple users are typing
            else:
                self.label_typing.text += self.typing_user + ", "

            # Reducing the TTL of "user is typing" by 1
            who_is_typing[self.typing_user] -= 1

        # Clearing the dictionary users currently typing from users with expired TTL
        who_is_typing = {key:val for key, val in who_is_typing.items() if val != 0}


    def user_typing(self) -> None:
        """
        Broadcast to everybody that the user started typing
        """
        try:
            client.send("STATUS:TYPING".encode('utf-8'))

        except (ConnectionAbortedError, ConnectionResetError):
            WannaChatApp().close_application()

    def remove_text_hint(self) -> None:
        """
        Remove "Enter your message" hint from the TextInput panel
        """
        self.entered_message.hint_text = ""


class Manager(ScreenManager):
    pass


class WannaChatApp(App):
    def build(self):
        self.kv = Builder.load_file('wannachat.kv')
        return self.kv

    def close_application(self):
        """
        This method is called when a user presses x
        in the top-left corner
        """
        # Unloading the Builder file
        Builder.unload_file('wannachat.kv')

        # Closing the application
        App.get_running_app().stop()

        # Removing the window
        Window.close()


if __name__ == "__main__":
    kivy_require("1.9.0")

    chat_history_gui: str = ""         # Global to store the chat history
    who_is_typing: dict[str, int] = {} # Global to store nicknames of who's typing
    my_nickname: str = ""              # Global to store the nickname

    # Creating the client for the TCP connection
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Launching the GUI
    WannaChatApp().run()
