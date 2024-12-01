from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.callback_data import CallbackData
from telebot import TeleBot
from ecobot_db import *
from ecobot import *
import os


# create bot object by its token
API_TOKEN = os.environ['API_TOKEN']
bot = TeleBot(API_TOKEN)
caps_factory = CallbackData('caps_amount', 'message_id', prefix='add_caps')


def run_caps_callback(call):
    """
    Checks if the callback query is an add_caps callback.

    Args:
        call (CallbackQuery object): Incoming callback query from the pressed callback button.

    Returns:
        bool: True if the callback should be activated, False otherwise.
    """

    return caps_factory.filter().check(call)  

@bot.callback_query_handler(func=run_caps_callback)
def add_caps(call):
    """
    Callback handler that adds caps to the user.

    Args:
        call (CallbackQuery object): Incoming callback query from the pressed callback button.

    Returns:
        None
    """

    # get the id of the chat
    chat_id = call.message.chat.id
    
    # get the number of caps to add
    caps = int(caps_factory.parse(callback_data=call.data)['caps_amount'])

    # get recommendation message id
    message_id = int(caps_factory.parse(callback_data=call.data)['message_id'])

    # remove buttons to avoid re-crediting
    message_from_db = get_message_from_db(message_id)
    if message_from_db:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id, 
            text=message_from_db,
            parse_mode='MarkdownV2'
        )
    else:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id, 
            text=call.message.text
        )

    # add user's caps in database
    add_caps_to_db(chat_id, caps)
    
    bot.send_message(
        chat_id, 
        f'You\'ve got `{caps}` caps\!{"\U0001F973" if caps == 5 else "\U0001F60E"}\. Your balance now is `{get_user_balance(chat_id)}` caps\.',
        parse_mode='MarkdownV2'
    )

    
@bot.message_handler(commands = ['start'])
def send_welcome(message):
    """
    Sends welcome message and displays markdown.

    Args:
        message (Message object): User message with the start command.

    Returns:
        None
    """

    # create new murkup
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton('\U00002753Info'),
        KeyboardButton('\U0001F4B0Balance'),
        KeyboardButton('\U0001F6DFHelp')
    )

    # display new markup
    bot.send_message(message.chat.id, 'Hi there! Let\'s get started. Send a photo of the product barcode to get information on its disposal.', reply_markup=markup)


def display_help(message):
    """
    Checks if the sent message is a help command.

    Returns:
        bool: True if the message is a help command, False otherwise.
    """

    if message.text in ('/help', '\U0001F6DFHelp'):
        return True
    return False

@bot.message_handler(func=display_help)
def send_info(message):
    """
    Sends help information.

    Args:
        message (Message object): User message with a help command.

    Returns:
        None
    """

    bot.send_message(
        message.chat.id, 
        (
            'If you have any problems with the bot, try clicking the /start button\. If it doesn\'t help, please contact us:\n' +
            '• by email `ielisaveta24@gmail.com`\n' +
            '• or Telegram @eco\_assist\_help\_bot\.'
        ),
        parse_mode='MarkdownV2'
    )


def display_info(message):
    """
    Checks if the sent message is an info command.

    Returns:
        bool: True if the message is an info command, False otherwise.
    """

    if message.text in ('/info', '\U00002753Info'):
        return True
    return False

@bot.message_handler(func=display_info)
def send_info(message):
    """
    Sends bot information.

    Args:
        message (Message object): User message with an info command.

    Returns:
        None
    """

    bot.send_message(
        message.chat.id, 
        (
            '*Our Mission*\n\n' +
            'This bot is here to help you identify packaging types and make waste disposal simple, accurate, and hassle\-free\. Let\'s work together to keep the planet cleaner\!\n\n' +
            '*How to Use*\n\n' +
            'Using the bot is easy:\n' +
            '1\. Snap a photo of a product\'s barcode\.\n' +
            '2\. Send it to the bot\.\n' +
            'The bot will analyze the packaging type and provide tailored guidance on how to dispose of it responsibly\.\n\n' +
            'We use the *Open Food Facts database*, which focuses on food products\. Currently, this means the bot works *only with food packaging* \(see the full list of supported products [here](https://world.openfoodfacts.org/)\)\. Keep in mind:\n' +
            '• Not all products in the database include detailed packaging info\. However, the bot already supports *100,000\+ products* and is growing\!\n' +
            '• Response times can vary depending on server load, taking up to *a couple of minutes*\.\n' +
            'Rest assured, we *do not store your data or media files*\. Images are deleted when removed from the chat, ensuring your privacy\. The source code can be found [on GitHub](https://github.com/IvnEliza/EcoBot)\.\n\n' +
            '*Earn Rewards\!*\n\n' +
            'Every time you submit a product\'s barcode and follow the disposal recommendations:\n' +
            '• Earn *five virtual caps* for each material you recycle correctly\.\n' +
            '• Earn *ten caps* for single\-material packaging\.\n' +
            'Collect *1,000 caps* to claim a fun prize: a themed sticker set\! Buttons will appear below the recommendation message to claim your caps\.\n\n' +
            '*Contribute to the Cause*\n\n' +
            'You can help us — and the *Open Food Facts* project — by enriching the database:\n' +
            '• Download the Open Food Facts app from their [official website](https://world.openfoodfacts.org/open-food-facts-mobile-app)\.\n' +
            '• Add new products or enhance existing product descriptions to improve packaging details\.\n' +
            'Your contributions will make the bot even smarter and more accurate\!\n\n' +
            '*Bot Commands*\n\n' +
            'Here are some quick commands to get the most out of the bot:\n' +
            '• /balance or tap `\U0001F4B0Balance`: Check your current caps balance\.\n\n' +
            '• /help or tap `\U0001F6DFHelp`: Get support or troubleshoot issues\.\n\n' +
            '• /info or tap `\U00002753Info`: View the information section\.\n\n' +
            '• /start: Display the welcome message and restart the keyboard\.\n\n' +
            'Together, we can create a cleaner, greener world\. Let\'s make a difference — one package at a time\!\U0001F331'
        ),
        parse_mode='MarkdownV2'
    )


def display_balance(message):
    """
    Checks if the sent message is a balance command.

    Returns:
        bool: True if the message is a balance command, False otherwise.
    """

    if message.text in ('/balance', '\U0001F4B0Balance'):
        return True
    return False

@bot.message_handler(func=display_balance)
def send_balance(message):
    """
    Sends user balance.

    Args:
        message (Message object): User message with a balance command.

    Returns:
        None
    """

    # get user balance
    caps = get_user_balance(message.chat.id)

    bot.send_message(
        message.chat.id,
        f'You currently have `{caps if caps else 0}` caps\. Follow our recommendations on waste sorting to collect more caps\!', 
        parse_mode='MarkdownV2'
    )


@bot.message_handler(content_types = ['photo'])
def photo(message):
    """
    Provides the user with recommendations on how to correctly sort product packaging based on a photo with its barcode sent to the bot chat.

    Args:
        message (Message object): User message with a barcode photo.

    Returns:
        None
    """

    # ID of the sent photo
    photo_id = message.photo[-1].file_id

    # photo file information
    file_info = bot.get_file(photo_id)

    # read barcodes from photos
    barcodes = get_barcode(f'https://api.telegram.org/file/bot{API_TOKEN}/{file_info.file_path}')

    # if there are no barcodes
    if not barcodes:
        bot.reply_to(message, '\U0001F97A Sorry, I can\'t detect any barcodes on this image. Please take a higher quality photo. Note that the barcode must be clearly visible and not obscured by anything.')
    
    # if there are barcodes
    for barcode in barcodes:

        # get product information from the Open Food Facts database
        product = barcode_search(barcode)

        # if there is no product information
        if not product:
            bot.reply_to(
                message,
                escaping_for_markdown(
                    f'\U0001F3AB*Barcode*: `{barcode}`\n\n' +
                    '\U0001F614Unfortunately, the product was not found in the database.\n\n' +
                    'We use the Open Food Facts database,' +
                    ' so you can help us and this independent non-profit project by scanning the product in the app,'
                ) + ' which can be downloaded using [this link](https://world.openfoodfacts.org/open-food-facts-mobile-app)\.',
                parse_mode='MarkdownV2'
            )
        
        # if there is product information
        else:
            # provide the user with recommendations
            print_recommendations(find_materials(product), product.get('product_name'), barcode, bot, message, caps_factory)


# create DB table to store user balances (if not already created)
create_balance_table()

# create DB table to temporarily store recommendation messages (if not already created)
create_messages_table()

# start bot
bot.polling()