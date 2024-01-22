import logging
from utils import LangContatiner, EnvironmentContainer

# setup logger
global LOGGER
LOGGER = logging.getLogger(__name__)

# setup language container
global LANG
LANG = LangContatiner()
LOGGER.info(LANG.logger.info.logger.init.format(name=__name__))
LOGGER.info(LANG.logger.info.lang.init.format(name=__name__))

# setup environment variables
# global ENV
# ENV = EnvironmentContainer(required=("TOKEN",))
# LOGGER.info(LANG.logger.info.env.init.format(name=__name__))

class NotEnoughPlayers(Exception):
	def __init__(self, channel, num, *args):
		super().__init__(*args)
		self.minimum_players = 2
		self.channel = channel
		self.num = num
		LOGGER.exception(self.__str__())
		
	async def send_message(self):
		await self.channel.send(self.__str__())
	def __str__(self):
		return LANG.exception.not_enough_players.message.format(players=self.num, minimum=self.minimum_players)

class NotInVC(Exception):
	def __init__(self, channel, *args):
		super().__init__(*args)
		self.minimum_players = 2
		self.channel = channel
		LOGGER.exception(self.__str__())
		
	async def send_message(self):
		await self.channel.send(self.__str__())
	def __str__(self):
		return LANG.exception.not_in_vc.message