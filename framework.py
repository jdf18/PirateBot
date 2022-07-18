from abc import abstractmethod
import logging
import discord
from discord import Member, Embed, Message
from utils import EnvironmentContainer, LangContatiner


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

class BaseClass:
    def __init__(self):
        # store the locale and prefix for easier access
        self.locale = LANG.locale
        self.COMMAND_PREFIX = LANG.discord.command.prefix

        # start the discord client
        self.client = discord.Client()
        LOGGER.info(LANG.logger.info.discord.init)

    def setup(self):
        @self.client.event
        async def on_ready():
            # log when the client is ready
            LOGGER.info(LANG.logger.info.discord.client.init.format(client=self.client))

        @self.client.event
        async def on_message(message: discord.message):
            # log when a message has been sent and parse the message
            await self.message_recieved(message)

    async def message_recieved(self, message):
        # parse the incoming message
        author = message.author

        if author == self.client.user:
            return # Exit as the client is recieving its own message

        # log all messages that are not sent by the bot
        LOGGER.debug('{} sent the message: "{}'.format(
            author.name, message.content[:50]+ ('"' if len(message.content) <= 50 else "..."), 
        ))

        channel = message.channel
        if type(channel) == discord.channel.TextChannel:
            # If the message was sent in a group text channel:
            if message.content.startswith(self.COMMAND_PREFIX):
                # If the message is a command:
                await self.recieved_command(message)
            else:
                await self.recieved_group_channel(message)

        elif type(channel) == discord.channel.DMChannel:
            # If the message was sent in a direct message:
            await self.recieved_direct_message(message)

        else:
            # The channel is not supported
            LOGGER.error(LANG.logger.error.unsupported_channel.format(ch_type=type(channel)))

    @abstractmethod # Needs to be inplemented in next class up
    async def recieved_group_channel(self, message):
        return
    @abstractmethod # Needs to be inplemented in next class up
    async def recieved_command(self, message):
        return
    @abstractmethod # Needs to be inplemented in next class up
    async def recieved_direct_message(self, message):
        return
        
    
    def start_client(self):
        # setup then start the client
        self.setup()
        self.client.run(ENV.TOKEN)

    async def send_direct_message(self, member: Member, message: Message, response_wanted: bool = False):
        try:
            if type(message) == Message:
                await member.discord_member.send(message.content)
            elif type(message) == Embed:
                await member.discord_member.send(embed=message.embed)
        except:
            LOGGER.error(LANG.logger.error.unknown)
    

