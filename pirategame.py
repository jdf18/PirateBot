import framework
from json import loads, dumps
from random import shuffle
from utils import LangContatiner, EnvironmentContainer
import discord
import logging

# setup logger
global LOGGER
LOGGER = logging.getLogger(__name__)

# setup language container
global LANG
LANG = LangContatiner()
LOGGER.info(LANG.logger.info.logger.init.format(__name__))
LOGGER.info(LANG.logger.info.lang.init.format(__name__))

# setup environment variables
global ENV
ENV = EnvironmentContainer(required=("TOKEN",))
LOGGER.info(LANG.logger.info.env.init.format(__name__))

class Grid:
    weights = [1,1,1,1,1,1,1,1,1,1,1,1,2,10,25]
    def __init__(self, size=7):
        # stored as a 2 dimensional array of indexes 0-15
        self.items = [[None for i in range(size)] for j in range(size)]
    def __getitem__(self, coords):
        x, y = coords
        return self.items[x][y]
    def __setitem__(self, coords, value):
        x, y = coords
        self.items[x][y] = value

    def randomise(self):
        # Generates a random grid for the player to use
        temp = []
        for i, weight in enumerate(self.weights):
            for j in range(weight): temp.append(i)
        shuffle(temp)
        for i in range(len(self.items)):
            self.items[i] = temp[7*i:7*(i+1)]
        pass

    def __str__(self) -> str:
        # TODO A function that returns the board as a string that can be sent to the player.
        lookup = loads("["+LANG.pirate.grid.order+"]")
        rows = ["" for i in range(len(self.items))]
        for i, row in enumerate(self.items):
            for item in row:
                try:
                    rows[i] += LANG.pirate.grid.key.__getattr__(lookup[item])
                except IndexError:
                    rows[i] += LANG.pirate.grid.key.none
        return eval('"'+LANG.pirate.grid.format.format(*rows)+'"')

class Game:
    class Player:
        def __init__(self, member):
            self.member = member
            self.id = member.id

            self.grid = Grid().randomise()
            self.member.send(embed=self.grid.to_embed())

    def __init__(self, players):
        self.active = True
        self.players = {}
        for player in players:
            self.players.update({player.id: self.Player(player)})

class App(framework.BaseClass):
    def __init__(self):
        super().__init__()

        self.voice_channel = None
        self.text_channel = None

    async def recieved_group_channel(self, message):
        pass
    async def recieved_command(self, message: discord.Message):
        content = message.content
        parts = content.split(' ')
        if parts[1].upper() == LANG.discord.command.help.upper():
            LOGGER.info(LANG.logger.command.help.format(message.author.display_name))
            await message.channel.send(LANG.pirate.message.help)
        elif parts[1].upper() == LANG.discord.command.dev.prefix.upper():
            if parts[2].upper() == LANG.discord.command.dev.generate_board.upper():
                LOGGER.info(LANG.logging.command.dev.generate_board.format(message.author.display_name))
                new_board = Grid()
                new_board.randomise()
                await message.channel.send(str(new_board))
        elif parts[1].upper() == LANG.discord.command.start.upper():
            self.voice_channel = message.author.voice.channel
            self.text_channel = message.channel
            self.start_game()

    async def recieved_direct_message(self, message):
        pass

    def start_game(self):
        self.current_game = Game(self.voice_channel.members)