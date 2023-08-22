from Config import config, commands, bot_options
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import logging
import traceback
import validators


class UsefulMethod:
    def __init__(self, input_method):
        self.input = input_method
        self.output = {'status': 'false', 'error': ''}

    def input_validator(self, validator_type=None):
        if not validator_type:
            return self.output
        if validator_type == 'url':
            if validators.url(self.input):
                self.output.update({'status': "true"})
                return
            return self.output


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
    def __init__(self):
        self.MENU = 1
        self.PHOTO, self.CAPTION, self.URL = range(3)
        self.context = {}
        self.userName = ''

    def set_welcome_format(self, info):
        try:
            self.userName = info.message.chat.first_name
        except:
            pass
        return f"Hi {self.userName}"

    def start(self, bot: Bot, update):
        start_text = self.set_welcome_format(update)

        # keyboard = [
        #     [InlineKeyboardButton("Option 1", callback_data='/ad')],
        #     [InlineKeyboardButton("Option 2", callback_data='option2')],
        #     [InlineKeyboardButton("Option 3", callback_data='option3')],
        #     [InlineKeyboardButton("Option 4", callback_data='option4')]
        # ]
        # reply_markup = InlineKeyboardMarkup(keyboard)
        # update.message.reply_text(start_text, reply_markup=reply_markup)

        update.message.reply_text(start_text, reply_markup=ReplyKeyboardMarkup(bot_options, one_time_keyboard=True))
        return self.MENU

    def menu_selection(self, bot: Bot, update):
        selected_option = update.message.text
        # if selected_option == 'ساخت بنر':
        #     self.make_ad(bot, update)
        return ConversationHandler.END

    @staticmethod
    def help(bot, update):
        """Send a message when the command /help is issued."""
        text = "Available Commands :"
        for this_c in commands.keys():
            text += f"\n/{this_c}"
        update.message.reply_text(text)

    def get_photo(self, bot: Bot, update):

        command_name = self.get_command_name(update)
        command_text = commands.get(command_name, '')

        self.context['photo'] = update.message.photo[-1].file_id
        update.message.reply_text(command_text)
        return self.CAPTION

    def get_caption(self, bot: Bot, update):
        self.context['caption'] = "Check out our awesome product!\n[Learn More](https://example.com)"  # Markdown

        update.message.reply_text("Got it! Finally, send the URL for the hyperlink.")
        return self.URL

    def choice_banner_frame(self, bot: Bot, update):
        keyboard = [
            [InlineKeyboardButton("TextLink1",
                                  callback_data="Check out our awesome product!\n[Learn More](https://example.com)")],
            [InlineKeyboardButton("TextLink2",
                                  callback_data="Earn More", url=self.context['url'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Please choice the one of TextLinks", reply_markup=reply_markup)
        self.context['text_link'] = update.callback_query.data
        update.message.reply_text("please send your url:")
        return self.URL

    def button_click(self, update, context):
        query = update.callback_query
        option_text = query.data
        query.answer(f"you are chose '{option_text}'option.")



    def get_url(self, bot: Bot, update):
        try:
            self.context['url'] = update.message.text
            # Create the ad banner with the collected information
            banner_object = self.create_banner()
            if banner_object:
                bot.send_photo(update.message.chat_id, photo=banner_object['photo'],
                               caption=banner_object['caption'], reply_markup=banner_object['reply_markup'],
                               parse_mode='Markdown', disable_web_page_preview=True)
            update.message.reply_photo(**banner_object)
        except:
            print(traceback.format_exc())
        finally:
            self.context.clear()
            return ConversationHandler.END

    def create_banner(self):
        photo = self.context['photo']
        caption = self.context['caption']
        url = self.context['url']
        text_link = self.context['text_link']

        validator_object = UsefulMethod(url)
        if validator_object.input_validator(validator_type='url').get('status', 'false') == 'false':
            return {}

        button = InlineKeyboardButton(text_link, url=url)
        keyboard = [[button]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        return {"photo": photo, "caption": caption, "reply_markup": reply_markup}

    def make_ad(self, bot: Bot, update):
        """Send a message when the command /help is issued."""
        update.message.reply_text(text="send a photo please")
        return self.PHOTO

    @staticmethod
    def get_command_name(update):
        return str(update.message.text).split('/')[-1]


class MakeBanner(Commands):
    def __init__(self, command_name='ad'):
        super().__init__()
        self.command = command_name

    def banner_handler(self):
        conversation_handler = ConversationHandler(
            entry_points=[CommandHandler(self.command, self.make_ad)],
            states={
                self.PHOTO: [MessageHandler(filters=Filters.photo, callback=self.get_photo)],
                self.CAPTION: [MessageHandler(filters=Filters.text, callback=self.get_caption)],
                self.URL: [MessageHandler(filters=Filters.text, callback=self.get_url)]
            },
            fallbacks=[]
        )
        return conversation_handler


class MakeMenu(Commands):
    def __init__(self, command_name='menu'):
        super().__init__()
        self.command = command_name

    def menu_handler(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler(self.command, self.start)],
            states={
                self.MENU: [MessageHandler(Filters.text, self.menu_selection)]
            },
            fallbacks=[]
        )
        return conv_handler


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
            # dp.add_handler(CommandHandler("start", self.start))

            for this_c in commands_list:
                dp.add_handler(CommandHandler(*this_c))

            conversation_handler = MakeBanner().banner_handler()
            menu_handler = MakeMenu('start').menu_handler()

            dp.add_handler(menu_handler)
            dp.add_handler(conversation_handler)
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

    # def start(self, bot, update):
    #     """Send a message when the command /start is issued."""
    #     welcome_text = self.set_welcome_format(update)
    #     update.message.reply_text(welcome_text)

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
        for this_c in self.commands.keys():
            try:
                result.append(tuple([this_c, eval(f'self.{this_c}')]))
            except:
                continue
        return result


if __name__ == '__main__':
    BotDispatcher(log=True).handler()
