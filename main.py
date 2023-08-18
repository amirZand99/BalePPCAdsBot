from Config import config, commands
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import traceback


class BotHandler:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

    def __init__(self):
        self.user_id = config.get('user_id')
        self.token = None
        self.logger = logging.getLogger(__name__)

    def set_token(self):
        if self.user_id:
            self.token = f"{self.user_id}:{config.get('token')}"

    def get_token(self):
        return self.token

    def set_dispatcher(self):
        self.set_token()
        token = self.get_token()
        bot = Bot(token=token,
                  base_url=config.get('url'),
                  base_file_url=config.get("file_url"))
        updater = Updater(bot=bot)
        dp = updater.dispatcher
        return [updater, dp]


class Commands:
    @staticmethod
    def help(bot, update):
        """Send a message when the command /help is issued."""
        text = "Available Commands :"
        for this_c in commands:
            text += f"\n/{this_c}"
        update.message.reply_text(text)


class BotDispatcher(BotHandler, Commands):
    def __init__(self, log=False):
        super().__init__()
        self.get_log = log
        self.commands = []
        self.userName = ''

    def handler(self):
        dp_option = self.set_dispatcher()
        dp = dp_option[1]
        updater = dp_option[0]

        try:
            commands_list = self.create_commands_tuple()
            dp.add_handler(CommandHandler("start", self.start))

            for this_c in commands_list:
                dp.add_handler(CommandHandler(*this_c))

            dp.add_handler(MessageHandler(Filters.text, self.unknown_text))
            dp.add_handler(MessageHandler(Filters.command, self.unknown_command))

            if self.get_log:
                log = dp.add_error_handler(self.set_error)
                self.logger.warning(log)

            updater.start_polling(poll_interval=2)
            updater.idle()
        except:
            print(traceback.format_exc())
        finally:
            updater.stop()

    def start(self, bot, update):
        """Send a message when the command /start is issued."""
        welcome_text = self.set_welcome_format(update)
        update.message.reply_text(welcome_text)

    @staticmethod
    def unknown_text(bot, update):
        """Echo the user message."""
        update.message.reply_text("I'm sorry, I didn't understand")

    @staticmethod
    def unknown_command(bot, update):
        """Echo the user message."""
        update.message.reply_text(f'{update.message.text} was not found !')

    @staticmethod
    def set_error(bot, update):
        """Log Errors caused by Updates."""
        return 'Update "%s" caused error "%s"', update, update.message

    def create_commands_tuple(self):
        self.commands = commands
        result = []
        for this_c in self.commands:
            try:
                result.append(tuple([this_c, eval(f'self.{this_c}')]))
            except:
                continue
        return result

    def set_welcome_format(self, info):
        try:
            self.userName = info.message.chat.first_name
        except:
            pass
        return f"Hi {self.userName}"


if __name__ == '__main__':
    BotDispatcher(log=True).handler()