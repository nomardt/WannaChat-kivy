import socket
import threading
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
from kivy.clock import Clock
# Making the app look sharper on Windows systems
try:
    from ctypes import windll, c_int64
    windll.user32.SetProcessDpiAwarenessContext(c_int64(-4))

except ModuleNotFoundError:
    pass

except Exception:
    exit()


class EnterIP(Screen):
    """
    The first screen where the user enters the IP address of the server.
    """
    def establish_connection(self) -> None:
        """
        Establishing the connection after 'enter' is pressed
        """
        server_address = self.address.text
        server_port = 12345

        try:
            client.connect((server_address, server_port))
            
        except:
            # Prevent loop formation
            self.address.text = ""

            # Updating the GUI in case the entered IP addr is invalid
            self.label_not_found.text = "Server not found!"


# The second screen
class EnterNickname(Screen):
    """
    The second screen where the user enters her/his nickname
    """
    def check_if_nickname_is_entered(self) -> None:
        """
        Checking if the user has entered a nickname after she/he presses 'enter' 
        """
        if len(self.nickname.text) > 0:
            self.check_if_nickname_is_taken()

    def check_if_nickname_is_taken(self) -> None:
        """
        The nickname the user entered is checked against the server's list of nicknames
        """
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
    """
    The third screen with the functionality to send messages and read the ones written by other clients
    """
    def __init__(self, **kw):
        """
        It refreshes the chat history window
        """
        super().__init__(**kw)

        # This constantly adds to GUI the elements stored in add_to_gui
        Clock.schedule_interval(self.receive_helper, 0.5)

    def message_send(self) -> None:
        """
        It sends the message after the user has pressed the "send" button
        """
        try:
            client.send(self.entered_message.text.encode('utf-8'))

            self.entered_message.text = ""
            
        except (ConnectionAbortedError, ConnectionResetError):
            exit()

    def start_receive_thread(self) -> None:
        """
        It starts the receiving thread
        """
        self.receive_thread = threading.Thread(target=self.receive)
        self.receive_thread.start()

    def receive(self) -> None:
        """
        It is constantly waiting for messages from the server, works in a thread
        """
        global add_to_gui

        while True:
            try:
                add_to_gui += client.recv(1024).decode('utf-8') + "\n"
                
            except ConnectionResetError:
                exit()

    def receive_helper(self, *aw) -> None:
        """
        Kivy can't change GUI elements outside the main thread so this method is needed
        """
        self.chat_history.text = add_to_gui


class Manager(ScreenManager):
    pass


class WannaChatApp(App):
    def build(self):
        kv = Builder.load_file('wannachat.kv')
        return kv


if __name__ == "__main__":
    kivy.require("1.9.0")

    # String to store the chat history
    add_to_gui = ""

    # Creating the client for the TCP connection
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Launching the GUI
    WannaChatApp().run()