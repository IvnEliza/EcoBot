import sqlite3

# DEFINE CONSTANTS

# path to the database
DB_PATH = '/data/ecobot.db'


# DEFINE DB FUNCTIONS

def create_balance_table():
    """
    Creates a database table to store user balances (if not already created).

    Returns: 
        None
    """

    # connect to the database
    conn = sqlite3.connect(DB_PATH)
    
    # create a cursor object to execute SQL queries
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS balance (
            chat_id INTEGER PRIMARY KEY, 
            caps INTEGER DEFAULT 0 NOT NULL
        );
    """)
    
    # close connection to the database
    conn.close()


def get_user_balance(chat_id):
    """
    Get user balance from the database by chat_id.

    Args:
        chat_id (int): Telegram chat ID.

    Returns:
        int: The user\'s balance. Returns None if there is no user in the database.
    """

    # connect to the database
    conn = sqlite3.connect(DB_PATH)
    
    # create a cursor object to execute SQL queries
    cursor = conn.cursor()
    
    # try to get balance
    cursor.execute("""
        SELECT chat_id, caps
        FROM balance
        WHERE chat_id = ?
    """, (chat_id,))
    
    # save the result
    result = cursor.fetchone()

    # close connection to the database
    conn.close()

    # return balance if there is such user
    if result:
        return int(result[1])
    

def add_caps_to_db(chat_id, caps):
    """
    Add caps to the user\'s balance by their chat_id.

    Args:
        chat_id (int): Telegram chat ID.
        caps (int): Number of caps to add.

    Returns: 
        None
    """

    # get current user balanse
    user_balance = get_user_balance(chat_id)

    # connect to the database
    conn = sqlite3.connect(DB_PATH)
    
    # create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # add caps
    if user_balance is None:
       cursor.execute("""
           INSERT INTO balance (chat_id, caps)
           VALUES (?, ?)
       """, (chat_id, caps))
    else:
        cursor.execute("""
           UPDATE balance SET caps = ?
           WHERE chat_id = ?
       """, (user_balance + caps, chat_id))

    # commit changes
    conn.commit()

    # close connection to the database
    conn.close()


def create_messages_table():
    """
    Creates a database table to temporarily store recommendation messages (if not already created).

    Returns: 
        None
    """
    
    # connect to the database
    conn = sqlite3.connect(DB_PATH)
    
    # create a cursor object to execute SQL queries
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY, 
            message_text TEXT NOT NULL
        );
    """)
    
    # close connection to the database
    conn.close()



def save_message_to_db(message_text):
    """
    Saves a message text to the database.

    Args:
        message_text (str): Recommendation message text.

    Returns: 
        int: Custom message identifier.
    """

    # connect to the database
    conn = sqlite3.connect(DB_PATH)
    
    # create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # save message text
    cursor.execute("""
           INSERT INTO messages (message_id, message_text)
           VALUES (NULL, ?)
       """, (message_text,))
    
    # commit changes
    conn.commit()

    # get message id
    cursor.execute("""
        SELECT message_id, message_text
        FROM messages
        WHERE message_text = ?
    """, (message_text,))

    # save the result
    result = cursor.fetchone()

    # close connection to the database
    conn.close()

    if result:
        return int(result[0])


def get_message_from_db(message_id):
    """
    Extracts the message text from the database by its custom identifier.
    After that, the message is deleted from the database.

    Args:
        message_id (int): Custom message identifier.

    Returns: 
        str: Recommendation message text.
    """

    # connect to the database
    conn = sqlite3.connect(DB_PATH)
    
    # create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # get message text by message_id
    cursor.execute("""
        SELECT message_id, message_text
        FROM messages
        WHERE message_id = ?
    """, (message_id,))

    # save the result
    result = cursor.fetchone()

    if result:
        message_text = result[1]

        # delete temporarily stored message text
        cursor.execute("""
            DELETE FROM messages
            WHERE message_id = ?
        """, (message_id,))

        # commit changes
        conn.commit()

        # close connection to the database
        conn.close()

        return message_text
    
    # close connection to the database
    conn.close()