from Config import config, commands
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
import logging
import traceback
import validators
import re
from json import loads, dumps
import sqlite3


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

class PaymentDatabase:
    def __init__(self, db_name='payment_log.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS log (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                price REAL
            )
        ''')
        self.conn.commit()

    def insert_payment(self, user_id, price):
        self.cursor.execute('INSERT INTO log (user_id, price) VALUES (?, ?)', (user_id, price))
        self.conn.commit()

    def get_all_payments(self):
        self.cursor.execute('SELECT * FROM log')
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

#use PaymentDatabase class
payment_db = PaymentDatabase()

user_id = 12345
price = 50.0

payment_db.insert_payment(user_id, price)

all_payments = payment_db.get_all_payments()
for payment in all_payments:
    print(f"ID: {payment[0]}, User ID: {payment[1]}, Price: {payment[2]}")

payment_db.close()


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
        print(update)
        start_text = self.set_welcome_format(update)

        # keyboard = [
        #     [InlineKeyboardButton("Option 1", callback_data='/ad')],
        #     [InlineKeyboardButton("Option 2", callback_data='option2')],
        #     [InlineKeyboardButton("Option 3", callback_data='option3')],
        #     [InlineKeyboardButton("Option 4", callback_data='option4')]
        # ]
        # reply_markup = InlineKeyboardMarkup(keyboard)
        # update.message.reply_text(start_text, reply_markup=reply_markup)

        update.message.reply_text(start_text, reply_markup=ReplyKeyboardMarkup(self.get_bot_menu(),
                                                                               one_time_keyboard=True))
        # return self.MENU
        return ConversationHandler.END

    def menu_selection(self, bot: Bot, update):
        selected_option = update.message.text
        # if selected_option == 'ساخت بنر':
        #     self.make_ad(bot, update)
        return ConversationHandler.END

    def invoice(self, bot:Bot, update):
        payment_id = "" #your payment_id
        update.message.reply_text("در حال انتقال به صفحه پرداخت...")
        admin_confirmation_message = "در انتظار تایید ادمین ..."
        update.message.reply_text(admin_confirmation_message)




    @staticmethod
    def help(bot, update):
        """Send a message when the command /help is issued."""
        text = "Available Commands :"
        for this_c in commands.keys():
            text += f"\n/{this_c}"
        update.message.reply_text(text)

    def get_photo(self, bot: Bot, update):
        # command_name = self.get_command_name(update)
        # command_text = commands.get(command_name, '')
        self.context['photo'] = update.message.photo[-1].file_id
        update.message.reply_text('2 - توضیحات مروبطه را وارد نمایید .')
        return self.CAPTION

    def get_caption(self, bot: Bot, update):
        text = update.message.text
        pattern = r"<<<(.*?)>>>"
        matches = re.findall(pattern, text)
        for this_m in matches:
            text = text.replace(f"<<<{this_m}>>>", "")
        for this_m in matches:
            if ":" not in this_m:
                continue
            this_m = this_m.split(':')
            text += f"\n [{this_m[0]}]({this_m[-1]})"
        self.context['caption'] = text
        update.message.reply_text("3 - لینک تبلیتان رو ارسال کنید .")
        return self.URL

    def get_url(self, bot: Bot, update):
        try:
            self.context['url'] = update.message.text
            # Create the ad banner with the collected information
            banner_object = self.create_banner()
            update.message.reply_photo(**banner_object)
            keyboard = [
                [InlineKeyboardButton("تایید", callback_data='تعرفه تبلیغات')],
                [InlineKeyboardButton("عدم تایید", callback_data='ساخت بنر')]
                # [InlineKeyboardButton("Option 3", callback_data='option3')],
                # [InlineKeyboardButton("Option 4", callback_data='option4')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("بنر تبلیغاتی شما آماده است .", reply_markup=reply_markup)
        except:
            print(traceback.format_exc())
        finally:
            self.context.clear()
            return ConversationHandler.END

    def create_banner(self):
        photo = self.context['photo']
        caption = self.context['caption']
        url = self.context['url']

        # validator_object = UsefulMethod(url)
        # if validator_object.input_validator(validator_type='url').get('status', 'false') == 'false':
        #     return {}
        result = {"photo": photo, "caption": caption}
        if url not in ('n', 'N', 'No'):
            if "<<<" not in url or '>>>' not in url or ":" not in url:
                url = ["فرمت لینک اشتباه است", ""]
            else:
                url = url.replace("<<<", '')
                url = url.replace(">>>", '')
                url = url.split(":")

            button = InlineKeyboardButton(*url)
            keyboard = [[button]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            result.update({"reply_markup": reply_markup})
        return result

    def make_ad(self, bot: Bot, update):
        """Send a message when the command /help is issued."""
        help_text = """لطفا در ساخت بنر به موارد زیر دقت کنید:

1 - کپشن مربوط به تبلیغ به صورت جداگانه از عکس از کاربر
دریافت می‌گردد.

2 - بنر شما می‌تواند شامل لینک متنی یا لینک شیشه‌ای باشد.

3 - برای افزودن لینک متنی در کپشن با فرمت زیر وارد کنید.
                                                                   <<<placeholder:link>>>

4 - اطلاعات مربوط به لینک شیشه‌ای به صورت جداگانه در پایان 
از شما دریافت می‌گردد(فرمت همانند لینک متنی) در صورت عدم نیاز، کافی است N را وارد نمایید.

نمونه به صورت پایین 👇👇👇
"""
        step_text = """در صورت تمایل لطفا مراحل زیر را طی نمایید :
1 - عکس موردنظرتان را ارسال نمایید .
2 - توضیحات مروبطه را ارسال نمایید .
3 - لینک تبلیغتان رو ارسال کنید .
        """
        update.message.reply_text(text=help_text)
        self.create_sample_banner(bot)
        banner_object = self.create_banner()
        update.message.reply_photo(**banner_object)
        update.message.reply_text(text=step_text)
        return self.PHOTO

    @staticmethod
    def get_command_name(update):
        return str(update.message.text).split('/')[-1]

    @staticmethod
    def get_bot_menu():
        c_list, pairs = [], []

        for k, v in commands.items():
            if v and v.get('category', '') == 'menu':
                c_list.append(v.get('name'))

        if len(c_list) > 0:
            for i in range(0, len(c_list), 2):
                pair = [c_list[i], c_list[i + 1]] if i + 1 < len(c_list) else [c_list[i]]
                pairs.append(pair)
        return pairs

    def create_sample_banner(self, bot):
        info = bot.get_me()
        bot_id = f"@{info.username}"
        caption = "PPC (Pay-Per-Click) یک مدل تبلیغات آنلاین است که تبلیغ‌دهنده بر اساس تعداد کلیک‌های دریافتی پرداخت " \
                  "می‌کند. این مدل به تبلیغ‌دهندگان امکان می‌دهد فقط برای نتایج مستقیم پرداخت کنند و هزینه‌های بیشتری " \
                  "صرف تبلیغ‌های بدون بازده نخواهند کرد. استفاده از کلمات کلیدی و تحلیل دقیق در انتخاب مخاطبان هدف از " \
                  "اهمیت بالایی برخوردار است. "
        caption += '\n\n\n'
        caption += f"[نمونه لینک متنی]({bot_id})"
        self.context['caption'] = caption
        image_path = r"/home/amir/Downloads/BaleBotImage.jpg"
        self.context['photo'] = open(image_path, 'rb')
        self.context['url'] = f"<<<نمونه لینک شیشه ای:{bot_id}>>>"

    async def handle_callback(self, bot: Bot, update: Update):
        query = update.callback_query

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        await query.answer()

        await query.edit_message_text(text=f"Selected option: {query.data}")


class MakeBanner(Commands):
    def __init__(self):
        super().__init__()

    def banner_handler(self):
        conversation_handler = ConversationHandler(
            entry_points=[MessageHandler(Filters.regex("^(ساخت بنر)$"), self.make_ad)],
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
            dp.add_handler(CommandHandler("start", self.start))

            for this_c in commands_list:
                dp.add_handler(CommandHandler(*this_c))

            conversation_handler = MakeBanner().banner_handler()
            # menu_handler = MakeMenu('start').menu_handler()
            dp.add_handler(CallbackQueryHandler(self.handle_callback))
            # dp.add_handler(menu_handler)
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

    # خواندن user_idهای ادمین از فایل و ذخیره آن‌ها در یک لیست
    def load_admin_users(self, file_path = "admin_users.txt"):
        admin_users = []
        try:
            with open(file_path, 'r') as file:
                admin_users = [int(line.strip()) for line in file.readlines()]
        except FileNotFoundError:
            print("فایل مربوط به user_idهای ادمین یافت نشد.")
        return admin_users
    #
    # # نام فایل مربوط به user_idهای ادمین
    # admin_users_file = 'admin_users.txt'
    # admin_users = load_admin_users(admin_users_file)
    #

if __name__ == '__main__':
    BotDispatcher(log=True).handler()