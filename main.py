import socket
import threading
import pywinauto
import keyboard
import sys
import random
import warnings
import time
from key_codes import *

# small project I did for fun, will most likely not be updated/maintained
# the code below is designed to work for Pokemon Emerald as an example
# only handles keyboard inputs

#################### HOW TO USE #####################

# 1. change user variables to match twitch channel and game window
# 2. add/edit commands in game_control() (line 105)
# 3. run program
# 4. to stop the program: press SHIFT, then type any message in chat to exit program (scuffed exit method due to threading, sorry!)

################## USER VARIABLES ###################

# your twitch channel
CHANNEL = "channelname"

# title of your game window (has to be exact, hide framerate via emulator settings if needed)
WINDOW = "mGBA - Pokemon - Emerald Version (USA, Europe) - 0.10.3"

#####################################################

# suppress warnings for sending {key down} inputs to out of focus windows
warnings.simplefilter("ignore", category=UserWarning)

# count down before starting, so you have time to set your game as the active window if needed
countdown = 5
while countdown > 0:
    print("starting in: ", countdown)
    countdown -= 1
    time.sleep(1)

try:
    print("Finding game window...")
    # connect to an existing application
    app_list = pywinauto.Application(backend="win32").connect(title=WINDOW, timeout=3)

    # select application to work with
    game = app_list[WINDOW]
    print("Game window found.")
except:
    print(
        "Game window not found. Double check to make sure your game is running, and the WINDOW variable is correct. Exiting program..."
    )
    sys.exit()

# create socket to communicate with twitch server using anonymous account "justinfan"
twitchbot = "justinfan%i" % random.randint(10000, 99999)
irc = socket.socket()
print("Connecting to twitch...")
irc.connect(("irc.twitch.tv", 6667))
print("Connected to twitch. Logging in anonymously with " + twitchbot + "...")
irc.send(
    ("PASS asdf\r\nNICK " + twitchbot + "\r\n" + "JOIN #" + CHANNEL + "\r\n").encode()
)

# global variables
message = ""
user = ""


# handle game actions based on received messages
def game_control():

    global message

    # hold down key
    def hold_key(key_code):
        action_down = f"\u007b{key_code} down\u007d"
        game.type_keys(action_down)

    # release key
    def release_key(key_code):
        action_up = f"\u007b{key_code} up\u007d"
        game.type_keys(action_up)

    # hold key for X seconds (default 0.3 seconds)
    def hold_and_release_key(key_code, seconds=0.3):
        hold_key(key_code)
        time.sleep(seconds)
        release_key(key_code)

    while True:
        # vastly reduce cpu consumption by adding a small delay between each loop
        time.sleep(0.01)

        # if user presses shift, end program upon receiving the next chat message
        if keyboard.is_pressed("shift"):
            print("Exiting program. Awaiting any chat message to complete the exit...")
            exit_flag.set()  # set flag to exit other thread
            sys.exit()

        msg = message.lower()

        if msg != "":
            # ADD/EDIT COMMANDS IN HERE

            # the keycode you use will be dependant on your keybinds in the emulator you use
            # e.g. if you have "up" in game bound to the "W" key, then use "W" as your keycode

            # use the "hold_key(KEYCODE)" function to hold down a key on your keyboard
            # use the "release_key(KEYCODE)" function to release a key on your keyboard
            # use the "hold_and_release_key(KEYCODE, SECONDS)" function to press and hold down a key on your keyboard for X seconds
            # defaulted to 0.3 seconds if SECONDS is not specified

            if msg == "a":
                hold_and_release_key(X)
            if msg == "b":
                hold_and_release_key(Z)
            if msg == "up":
                hold_and_release_key(UP_ARROW)
            if msg == "down":
                hold_and_release_key(DOWN_ARROW)
            if msg == "left":
                hold_and_release_key(LEFT_ARROW)
            if msg == "right":
                hold_and_release_key(RIGHT_ARROW)
            if msg == "lb":
                hold_and_release_key(A)
            if msg == "rb":
                hold_and_release_key(S)
            if msg == "start":
                hold_and_release_key(F)
            if msg == "select":
                hold_and_release_key(D)

            # commands with seconds specified
            if msg == "hold up":
                hold_and_release_key(UP_ARROW, 2)
            if msg == "hold down":
                hold_and_release_key(DOWN_ARROW, 2)
            if msg == "hold left":
                hold_and_release_key(LEFT_ARROW, 2)
            if msg == "hold right":
                hold_and_release_key(RIGHT_ARROW, 2)

            # reset message after command is done
            message = ""


# connect to twitch and parse messages
def twitch():

    # attempt to connect to specific channel's twitch chat
    def join_chat():
        loading = True
        while loading:
            readbuffer_join = irc.recv(1024).decode()
            print(readbuffer_join)
            for line in readbuffer_join.split("\n")[0:-1]:
                if "End of /NAMES list" in line:
                    print(
                        twitchbot
                        + " has joined "
                        + CHANNEL
                        + "'s Channel! Monitoring chat for messages..."
                    )
                    loading = False
        irc.send("CAP REQ :twitch.tv/tags\r\n".encode())

    # grab username of twitch chatter ("username : message")
    def get_user(line):
        # global user
        colons = line.count(":")
        colonless = colons - 1
        separate = line.split(":", colons)
        user = separate[colonless].split("!", 1)[0]
        return user

    # grab message of twitch chatter ("username : message")
    def get_message(line):
        # global message
        try:
            colons = line.count(":")
            message = (line.split(":", colons))[colons]
        except:
            message = ""
        return message

    # parse messages that appear in twitch chat
    def parse_messages():

        global user
        global message

        # receive data from twitch
        try:
            readbuffer = irc.recv(1024).decode()
        except:
            readbuffer = ""

        # parse data
        for line in readbuffer.split("\r\n"):
            if line == "":
                continue
            if "tmi.twitch.tv CAP * ACK" in line:
                continue
            if "PING :tmi.twitch.tv" in line:
                print(line)
                msg = "PONG :tmi.twitch.tv\r\n".encode()
                irc.send(msg)
                print(msg)
                continue
            else:
                try:
                    user = get_user(line)
                    message = get_message(line)

                    # print chat message to verify contents are correct
                    print(user + " : " + message)
                except Exception:
                    pass

    # join chat, then continuously monitor chat for messages
    join_chat()
    while not exit_flag.is_set():
        parse_messages()

    # after exiting loop
    print("Exit successful.")


def main():
    if __name__ == "__main__":
        t1 = threading.Thread(target=twitch)
        t1.start()
        t2 = threading.Thread(target=game_control)
        t2.start()


exit_flag = threading.Event()
main()
