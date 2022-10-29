import socket
import threading
import sys
# pip install kivy
import kivy
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.lang import Builder
from kivy.core.window import WindowBase
from kivy.clock import Clock, mainthread
# Making the app look sharper on Windows systems
try:
    from ctypes import windll, c_int64
    windll.user32.SetProcessDpiAwarenessContext(c_int64(-4))

except:
    pass


class EnterIP(Screen):
    # This method is launched when the user presses "enter"
    def establish_connection(self):
        # Establishing the connection
        server_address = self.address.text
        server_port = 12345

        try:
            client.connect((server_address, server_port))
            
        except:
            # Prevent loop formation
            self.address.text = ""

            # Updating the GUI in case the entered IP addr is invalid
            self.label_not_found.text = "Server not found!"


class EnterNickname(Screen):
    # This method is launched when the user presses "enter"
    def check_if_nickname_is_entered(self):
        if len(self.nickname.text) > 0:
            self.check_if_nickname_is_taken()

    # The method where the nickname is checked against the server's list of nicknames
    def check_if_nickname_is_taken(self):
        client.send(self.nickname.text.encode('utf-8'))

        # The server returns 'STATUS:FAILURE' if the entered nickname is already present
        if client.recv(1024).decode('utf-8') == 'STATUS:FAILURE':
            # Showing the result of the comparison in GUI
            self.label_enter_nick.text = "Nickname unavailable!"

            # Deleting the input to prevent loop formation
            self.nickname.text = ""

        else:
            # Proceeding to the next screen if the nickname is available
            self.manager.current = "WannaChat_main"

            ChatMainPage().start_receive_thread()


class ChatMainPage(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

        # This constantly adds to GUI the elements stored in add_to_gui
        Clock.schedule_interval(self.receive_helper, 0.5)

    # The method to send is called whenever the user presses the "send" button
    def message_send(self):
        try:
            client.send(self.entered_message.text.encode('utf-8'))
            
        except (ConnectionAbortedError, ConnectionResetError):
            sys.exit()

    # The method to start the receiving thread
    def start_receive_thread(self):
        self.receive_thread = threading.Thread(target=self.receive)
        self.receive_thread.start()

    # The receive method
    def receive(self):
        global add_to_gui

        while True:
            try:
                add_to_gui += client.recv(1024).decode('utf-8') + "\n"
                
            except ConnectionResetError:
                sys.exit()

    # Kivy can't change GUI elements outside the main thread so this method is needed
    def receive_helper(self, *aw):
        if len(add_to_gui) > 2:
            self.chat_history.text = add_to_gui


class Manager(ScreenManager):
    pass


class WannaChatApp(App):
    def build(self):
        kv = Builder.load_file('wannachat.kv')
        return kv


if __name__ == "__main__":
    kivy.require("1.9.0")

    add_to_gui = ""

    # Creating the client for the TCP connection
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Launching the GUI
    WannaChatApp().run()