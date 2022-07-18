from exceptions import NotEnoughPlayers, NotInVC
import framework
from json import loads, dumps
from random import shuffle
from utils import LangContatiner, EnvironmentContainer
from discord import Message, Embed, Member
from random import choice
import logging

# setup logger
global LOGGER
LOGGER = logging.getLogger(__name__)

# setup language container
global LANG
LANG = LangContatiner()
LOGGER.info(LANG.logger.info.logger.init.format(name=__name__))
LOGGER.info(LANG.logger.info.lang.init.format(name=__name__))

# setup environment variables
global ENV
ENV = EnvironmentContainer(required=("TOKEN",))
LOGGER.info(LANG.logger.info.env.init.format(name=__name__))

class Game:
    class Grid:
        @classmethod
        def random(cls):
            a = cls()
            a.randomise()
            return a
        weights = [1,1,1,1,1,1,1,1,1,1,1,1,2,10,25] # amount of each number
        def __init__(self, size: int=7):
            # stored as a 2 dimensional array of indexes 0-15
            self.items = [[None for i in range(size)] for j in range(size)]
        def __getitem__(self, coords: tuple) -> int: # access a particular square using a = Grid[x,y]
            x, y = coords
            return self.items[x][y]
        def __setitem__(self, coords: tuple, value: int): # write to a particular square using Grid[x,y] = a
            x, y = coords
            self.items[x][y] = value

        def randomise(self):
            # Generates a random grid for the player to use
            temp = [] # Add the correct proportions to a temporary list
            for i, weight in enumerate(self.weights):
                for j in range(weight): temp.append(i)
            shuffle(temp) # shuffle the list
            for i in range(len(self.items)): # split the list into a 2s array that can be used as the grid
                self.items[i] = temp[7*i:7*(i+1)]
            pass

        def __str__(self) -> str:
            # A function that returns the board as a string that can be sent to the player.
            lookup = loads("["+LANG.pirate.grid.order+"]")
            rows = ["" for i in range(len(self.items))]
            for i, row in enumerate(self.items):
                for item in row:
                    try:
                        rows[i] += LANG.pirate.grid.key.__getattr__(lookup[item])
                    except IndexError:
                        rows[i] += LANG.pirate.grid.key.none
                    except TypeError:
                        rows[i] += LANG.pirate.grid.key.none
            return eval('"'+LANG.pirate.grid.format.format(*rows)+'"')

    class Player:
        # An object that stores data regarding the players in the game
        def __init__(self, member: Member, pl: list):
            self.member = member
            self.id = member.id

            self.display_name = member.display_name

            self.player_list = pl
            self.expect_response = False
            self.response_prompt = None
            self.is_ready1 = True
            self.is_ready2 = True

            self.grid = None

            # Set default player settings
            self.cash_value = 0
            self.bank_value = 0
            # None  -> Not collected
            # True  -> Collected, not used
            # False -> Collected, used
            self.shield_status = None
            self.mirror_status = None

        def generate_grid(self):
            self.grid = Game.Grid.random()
        
        def get_embed(self, desc: str='', board=True) -> Embed:
            # return the embed that the player will see after the tile has been selected
            if board:
                embed = Embed( title=LANG.pirate.message.embed.title,       description=LANG.pirate.message.embed.description+desc)
                embed.add_field(name=LANG.pirate.message.embed.your_board,  value=str(self.grid), inline=True)
                embed.add_field(name=LANG.pirate.message.embed.players,     value=self.player_list, inline=True)
                embed.add_field(name=LANG.pirate.message.embed.cash,        value=str(self.cash_value), inline=False)
                embed.add_field(name=LANG.pirate.message.embed.bank,        value=str(self.bank_value), inline=True)
                return embed
            else:
                embed = Embed( title=LANG.pirate.message.embed.title,       description=LANG.pirate.message.embed.description+desc)
                embed.add_field(name=LANG.pirate.message.embed.cash,        value=str(self.cash_value), inline=False)
                embed.add_field(name=LANG.pirate.message.embed.bank,        value=str(self.bank_value), inline=True)
                return embed

        async def send(self, *args, **kwargs):
            # use player.send instead of player.member.send
            return await self.member.send(*args, **kwargs)
        
        async def send_square(self, square: str):
            self.is_ready1, self.is_ready2 = False, False
            x, y = int(square[1])-1, ord(square[0])-65
            square_type = self.grid[x,y]
            self.grid[x,y] = None
            description = self.handle_square(square_type)
            await self.send(embed=self.get_embed(LANG.pirate.message.square_chosen.format(square=square)+'\n'+description))

        def handle_square(self, square_type: int) -> Embed:
            # Select what happens when a square is chosen
            # "rob","kill","present","nuke","swap","choose","shield","mirror","bomb","double","bank","5K","3K","1K","200"
            self.expect_response = False
            if square_type == 0: # rob
                self.expect_response = True
            elif square_type == 1: # kill
                self.expect_response = True
            elif square_type == 2: # present
                self.expect_response = True
            elif square_type == 3: # nuke
                self.expect_response = True
            elif square_type == 4: # swap
                self.expect_response = True
            elif square_type == 5: # choose
                self.expect_response = True
            elif square_type == 6: # shield
                self.shield_status = True
            elif square_type == 7: # mirror
                self.mirror_status = True
            elif square_type == 8: # bomb
                self.cash_value = 0
            elif square_type == 9: # double
                self.cash_value *= 2
            elif square_type == 10: # bank
                self.bank_value = self.cash_value
                self.cash_value = 0
            elif square_type == 11: # 5K
                self.cash_value += 5000
            elif square_type == 12: # 3K
                self.cash_value += 3000
            elif square_type == 13: # 1K
                self.cash_value += 1000
            elif square_type == 14: # 200
                self.cash_value += 200

            if self.expect_response: self.response_prompt = square_type
            self.is_ready1 = not self.expect_response

            lookup = loads("["+LANG.pirate.grid.order+"]")
            description = LANG.pirate.grid.message.__getattr__(lookup[square_type])
            return description

    def __init__(self, players: list, master: Member):
        # Setup variables
        self.active = True
        self.master = master

        self.squares = [chr(65+i)+str(j+1) for i in range(7) for j in range(7)]

        # control logic
        self.player_choice_list = []

        # Create a way to store all of the player data
        self.player_names = []
        self.player_id_lut = {}
        self.player_ids = []
        for player in players:
            self.player_ids.append(player.id)
            self.player_names.append(player.display_name)
            self.player_id_lut.update({player.display_name:player.id})
        print(self.player_id_lut, self.player_names)
        self.players = {}
        pl = self.get_player_list()
        for player in players:
            self.players.update({player.id: self.Player(player, pl)})

        return

    async def send_grids(self):
        # distribute random grids
        for id, player in self.players.items():
            player.generate_grid()
            embed = player.get_embed()
            await player.send(embed=embed)

    def get_player_list(self):
        return '<@'+'>\n<@'.join(map(str, self.player_ids))+'>'

    async def round(self):
        # new round
        # Choose new tile
        LOGGER.info(LANG.logger.info.game.new_round)

        # TODO Reset ready
        if len(self.squares) == 0:
            await self.end_game()
            return
        if len(self.player_choice_list) == 0:
            square = self.random_square()
        else:
            square = choice(self.player_choice_list)
            self.player_choice_list.remove(square)
        self.choose_square(square)

        # distribute the tile
        for player in self.players.values():
            await player.send_square(square)
        
        await self.check_run_round()
    
    async def check_run_round(self):
        # TODO is_ready_2 checks
        # If no-one needs to provide a response, run again
        ready = True
        for player in self.players.values():
            if not player.is_ready1:
                ready = False
        if ready:
            await self.round()

    def random_square(self) -> str:
        return choice(self.squares)

    def choose_square(self, square: str):
        LOGGER.info(LANG.logger.info.game.square_chosen.format(square=square))
        self.squares.remove(square)
        if square in self.player_choice_list:
            self.player_choice_list.remove(square)

    def is_response_valid(self, content: str, prompt: int) -> bool:
        # check to see if the response is in the correct format

        if prompt == 0: # rob
            return content.strip() in self.player_names
        elif prompt == 1: # kill
            return content.strip() in self.player_names
        elif prompt == 2: # present
            return content.strip() in self.player_names
        elif prompt == 3: # nuke
            # TODO Temporarily set to kill logic
            return content.strip() in self.player_names
            # TODO Nuke logic
        elif prompt == 4: # swap
            return content.strip() in self.player_names
        elif prompt == 5: # choose
            return content.strip()[0].isalpha() and content.strip()[1].isdigit() and \
                'A' <= content.strip()[0].upper() <= 'G' and 1 <= int(content.strip()[1]) <= 7 and \
                (content.strip()[:2].upper() in self.squares)
        return False

    async def response(self, message: Message):
        # parse the response
        player = self.players[message.author.id]

        #TODO run different sub-routine if a response to mirror/shield. set ready 2 then run check run round
        # exit if not expecting a response
        if not player.expect_response: return
        
        # check that the response is valid
        if not self.is_response_valid(message.content, player.response_prompt):
            # TODO Send a message asking to try again
            return

        LOGGER.info(LANG.logger.info.game.response.format(author=message.author.display_name))
        
        # Complete the action
        # TODO store the original values (key=sender as can only attack one person at time) so they can be reversed if shield/mirror used
        # TODO offer use of mirror/shield once all ready1 has been completed. Probably add to player.get_embed(board=False)
        content: str = message.content
        if player.response_prompt == 0: # rob
            victim_id: int = self.player_id_lut[content.strip()]
            temp = self.players[victim_id].cash_value
            self.players[victim_id].cash_value = 0
            player.cash_value += temp
            await self.players[victim_id].send(
                embed=self.players[victim_id].get_embed(
                    LANG.pirate.message.__getattr__(loads("["+LANG.pirate.grid.order+"]")[player.response_prompt]).victim.format(sender=player.display_name), board=False
                ))
            await player.send(
                embed=player.get_embed(
                    LANG.pirate.message.__getattr__(loads("["+LANG.pirate.grid.order+"]")[player.response_prompt]).sender.format(
                        victim=self.players[victim_id].display_name,amount=str(temp)), board=False
                ))
        elif player.response_prompt == 1: # kill
            victim_id: int = self.player_id_lut[content.strip()]
            self.players[victim_id].cash_value = 0
            await self.players[victim_id].send(
                embed=self.players[victim_id].get_embed(
                    LANG.pirate.message.__getattr__(loads("["+LANG.pirate.grid.order+"]")[player.response_prompt]).victim.format(sender=player.display_name), board=False
                ))
            await player.send(
                embed=player.get_embed(
                    LANG.pirate.message.__getattr__(loads("["+LANG.pirate.grid.order+"]")[player.response_prompt]).sender.format(victim=self.players[victim_id].display_name), board=False
                ))
        elif player.response_prompt == 2: # present
            victim_id: int = self.player_id_lut[content.strip()]
            self.players[victim_id].cash_value += 1000
            await self.players[victim_id].send(
                embed=self.players[victim_id].get_embed(
                    LANG.pirate.message.__getattr__(loads("["+LANG.pirate.grid.order+"]")[player.response_prompt]).victim.format(sender=player.display_name), board=False
                ))
            await player.send(
                embed=player.get_embed(
                    LANG.pirate.message.__getattr__(loads("["+LANG.pirate.grid.order+"]")[player.response_prompt]).sender.format(victim=self.players[victim_id].display_name), board=False
                ))
        elif player.response_prompt == 3: # nuke
            victim_id: int = self.player_id_lut[content.strip()]
            self.players[victim_id].cash_value = 0
            # TODO Think of what this is going to do
            #* Temporarily set to kill another player
            await self.players[victim_id].send(
                embed=self.players[victim_id].get_embed(
                    LANG.pirate.message.__getattr__(loads("["+LANG.pirate.grid.order+"]")[player.response_prompt]).victim.format(sender=player.display_name), board=False
                ))
            await player.send(
                embed=player.get_embed(
                    LANG.pirate.message.__getattr__(loads("["+LANG.pirate.grid.order+"]")[player.response_prompt]).sender.format(victim=self.players[victim_id].display_name), board=False
                ))
        elif player.response_prompt == 4: # swap
            victim_id: int = self.player_id_lut[content.strip()]
            temp = self.players[victim_id].cash_value
            self.players[victim_id].cash_value = player.cash_value
            player.cash_value = temp
            await self.players[victim_id].send(
                embed=self.players[victim_id].get_embed(
                    LANG.pirate.message.__getattr__(loads("["+LANG.pirate.grid.order+"]")[player.response_prompt]).victim.format(sender=player.display_name), board=False
                ))
            await player.send(
                embed=player.get_embed(
                    LANG.pirate.message.__getattr__(loads("["+LANG.pirate.grid.order+"]")[player.response_prompt]).sender.format(victim=self.players[victim_id].display_name), board=False
                ))
        elif player.response_prompt == 5: # choose
            if not content.strip()[:1] in self.player_choice_list:
                self.player_choice_list.append(content.strip()[:2])

        # action has been completed
        player.is_ready1 = True

        await self.check_run_round()
        return False

    async def end_game(self):
        LOGGER.info(LANG.logger.info.game.end)
        # make a 2d array of player ids and their total scores
        finalScores = []
        for player in self.players.values():
            finalScore = player.cash_value + player.bank_value
            finalScores.append([player.id, finalScore])
        # sort scores
        temp = []
        for i in range(len(finalScores) - 1):
            if finalScores[i][1] < finalScores[i+1][1]:
                temp = finalScores[i+1]
                finalScores[i+1] = finalScores[i]
                finalScores[i] = temp
            else:
                pass
        #send a message to everyone
        lines = []
        for playerid, score in finalScores:
            line = LANG.pirate.message.embed.leaderboard_item.format(id=playerid,score=score)
            lines.append(line)

        leaderboard = "\n".join(lines) 
        #embed that shows winner and leaderboard 
        embed = Embed( title=LANG.pirate.message.embed.title,       description=LANG.pirate.message.winner.format(id=finalScores[0][0],score=finalScores[0][1]))
        embed.add_field(name=LANG.pirate.message.embed.leaderboard,  value=str(leaderboard), inline=True)
        await self.text_channel.send(embed=embed)
        return


class App(framework.BaseClass):
    def __init__(self):
        super().__init__()

        self.voice_channel = None
        self.text_channel = None

    async def recieved_group_channel(self, message: Message):
        pass
    async def recieved_command(self, message: Message):
        # parse the incoming commands and respond
        content = message.content
        parts = content.split(' ')
        
        # pirate help
        if parts[1].upper() == LANG.discord.command.help.upper():
            LOGGER.info(LANG.logger.command.help.format(user=message.author.display_name))
            await message.channel.send(LANG.pirate.message.help)

        # pirate dev ...
        elif parts[1].upper() == LANG.discord.command.dev.prefix.upper():
            #pirate dev generate_board
            if parts[2].upper() == LANG.discord.command.dev.generate_board.upper():
                LOGGER.info(LANG.logger.command.dev.generate_board.format(user=message.author.display_name))
                new_board = Game.Grid()
                new_board.randomise()
                await message.channel.send(str(new_board))

        # pirate start
        elif parts[1].upper() == LANG.discord.command.start.upper():
            if not message.author.voice:
                # If the user is not in a VC:
                a = NotInVC(message.channel)
                await a.send_message()
                # raise a

            self.voice_channel = message.author.voice.channel
            self.text_channel = message.channel

            # check that there are enough players to start the game
            debug = False
            print(self.voice_channel.members)
            if not (len(self.voice_channel.members) >= 2 or debug == True):
                a = NotEnoughPlayers(message.channel, len(self.voice_channel.members))
                await a.send_message()
                # raise a

            LOGGER.info(LANG.logger.info.game.start.format(author=message.author))

            await self.start_game(message.author)

    async def recieved_direct_message(self, message: Message):
        author = message.author
        if not author.id in self.current_game.players.keys():
            # The sender is not currently in a game
            await author.send(LANG.pirate.message.not_in_game)
            return

        await self.current_game.response(message)

    async def start_game(self, master: Member):
        # starts the game
        self.current_game = Game(self.voice_channel.members, master)
        await self.text_channel.send(LANG.pirate.message.game_start.format(user_id=self.current_game.master.id))
        await self.current_game.send_grids()
        await self.current_game.round()