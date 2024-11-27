import re
import json
import spacy
import requests
from skimage import io
from telebot import types
from zxingcpp import read_barcodes
from googletrans import Translator
from ecobot_db import save_message_to_db


# DEFINE CONSTANTS

with open('/data/materials.json', 'r') as file:
    MATERIALS = json.load(file)

PACKAGE_KEYS = [
    'packaging', 
    'packaging_old', 
    'packaging_text',
    'packaging_tags', 
    'packaging_hierarchy', 
    'packaging_materials_tags', 
    'packaging_recycling_tags', 
    'packaging_shapes_tags',
]


# DEFINE FUNCTIONS

def translate_to_en(s):
    """
    Translate string into english using Google Translate library.

    Args:
        s (str): String to be translated.

    Returns:
        str: String translated into English.
    """

    # if input is not a string, convert to string
    if type(s) is not str:
        s = str(s)
    
    translator = Translator()
    return translator.translate(s, dest='en').text


def clear_str(s):
    """
    Clear string from symbols and extra spaces using regular expressions. Also converts the string to lowercase.

    Args:
        s (str): String to be cleared.

    Returns:
        str: Cleared lowercase string.
    """

    # if input is not a string, convert to string
    if type(s) is not str:
        s = str(s)

    # remove hyphens and colons
    s = s.replace('-', ' ').replace(':', ' ')

    return re.sub(' +', ' ', re.sub(r'[^a-zA-Z ]+', '', s)).lower().strip()


def lemmatize(s):
    """
    Returns the lemmas (canonical forms) of the words for the given string using spaCy library.

    Args:
        s (str): String to be lemmatized.

    Returns:
        str: Lemmatized string.
    """

    # if input is not a string, convert to string
    if type(s) is not str:
        s = str(s)

    # if input is not empty or None, return canonical forms of the given words
    if s:
        nlp = spacy.load('en_core_web_sm')
        doc = nlp(s)
        return ' '.join([token.lemma_ for token in doc])
    
    # otherwise, return empty string
    return ''


def escaping_for_markdown(s):
    """
    Escaping special characters for Telegram MarkdownV2.

    Args:
        s (str): String to be send using MarkdownV2.

    Returns:
        str: The sent string with special characters escaped.
    """

    # replace characters using using a pre-defined dictionary
    for key, val in {
        '_': '\_', '[': '\[',
        ']': '\]', '(': '\(',
        ')': '\)', '~': '\~',
        '>': '\>', '#': '\#',
        '+': '\+', '-': '\-',
        '=': '\=', '|': '\|',
        '{': '\{', '}': '\}',
        '.': '\.', '!': '\!' 
    }.items():
        s = s.replace(key, val)
    return s


def get_barcode(url):
    """
    Recognizes barcodes in images using ZXing-C++.

    Args:
        url (str): Link to the image file containing barcodes.

    Returns:
        list (str): List of the barcodes recognized in the image.
    """

    # get image
    img = io.imread(url)

    # detect barcodes
    codes = read_barcodes(img)

    return [code.text for code in codes]


def barcode_search(barcode):
    """
    Searches for product information by barcode in available databases.

    Args:
        barcode (str): Product barcode.

    Returns:
        dict: Dictionary with information about the given product, if it is present in the database. Otherwise, returns None.
    """

    # check in Open Food Facts API
    url = f'https://world.openfoodfacts.org/api/v3/product/{barcode}.json'
    response = requests.get(url)

    if response.text:
        return response.json().get('product')


def find_materials(product):
    """
    Finds materials in product information for which the bot has sorting recommendations.

    Args:
        product (dict): Dictionary with product information.

    Returns:
        list (str): List of materials the given product may contain.
    """

    keywords = []
    result = []

    # check packaging data contained in string fields
    for key in PACKAGE_KEYS:
        val = str(product.get(key))
        if val:
            keywords += lemmatize(translate_to_en(clear_str(translate_to_en(val)))).split(' ')

    # keep only unique keywords
    keywords = list(set(keywords))

    # find intersection with the list of recommendations
    for k in keywords:
        if k in MATERIALS.keys():
            result.append(k)

    return result


def print_recommendations(materials, product_name, barcode, bot, message, caps_factory):
    """"
    Sends the user recommendations for sorting waste if there is enough information in the database.

    Args:
        materials (list of str): List of material tags for which the bot has sorting recommendations.
        product_name (str): Name of the product.
        barcode (str): Barcode of the product.
        bot (TeleBot object): Telegram bot object.
        message (Message object): Message to reply.
        caps_factory (CallbackData object): Callback data factory's object to process callbacks.

    Returns:
        None
    """
    
    # keep only unique material names
    materials = list(set([MATERIALS[m] for m in materials]))

    # number of caps as a reward
    caps = 5 if len(materials) > 1 else 10

    if materials:
        for m in materials:

            # read file with recommendations
            file = open(f'/data/recommendations/{m}.txt', 'r', encoding='UTF-8')

            # message with recommendation
            message_text = escaping_for_markdown(
                f'\U0001F3AB*Barcode*: `{barcode}`\n' +
                f'\U0001F4DD*Product name*: {product_name.replace('*', '').replace('`', '') if product_name else "Not found"}\U0001F5FF\n\n' +
                f'It seems that the package of this product contains *{m}*.' +
                '\U0000267BTo ensure proper recycling and reduce waste, follow these simple guidelines:\n\n' +
                f'{file.read()}\n\n' +
                'When in doubt, *check your local recycling guidelines* or dispose of the item in regular waste.\n\n' +
                'Thank you for helping to recycle responsibly!\U0001F49A'
            )

            # temporarily save message text to the database
            message_id = save_message_to_db(message_text)

            # create a callback button to get caps
            caps_button = types.InlineKeyboardButton(
                text=f'I followed your advice (+{caps} caps)',
                callback_data=caps_factory.new(
                    caps_amount=str(caps),
                    message_id=str(message_id)
                )
            )

            # add button to keyboard
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(caps_button)

            # send recommendations
            bot.reply_to(
                message, 
                message_text, 
                parse_mode='MarkdownV2',
                reply_markup=keyboard
            )                
    else:
        # send a message about insufficient information in Open Food Facts database
        bot.reply_to(
            message,
            escaping_for_markdown(
                f'\U0001F3AB*Barcode*: `{barcode}`\n' +
                f'\U0001F4DD*Product name*: {product_name.replace('*', '').replace('`', '') if product_name else "Not found"}\U0001F5FF\n\n' +
                '\U0001F614Unfortunately, we have not found sufficient information on the product\'s packaging type.\n\n' +
                'We use the Open Food Facts database,' +
                ' so you can help us and this independent non-profit project by filling in the product information in the app,'
            ) + ' which can be downloaded using [this link](https://world.openfoodfacts.org/open-food-facts-mobile-app)\.',
            parse_mode='MarkdownV2'
        )