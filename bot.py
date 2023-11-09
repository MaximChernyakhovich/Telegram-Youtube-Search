import sqlite3
import sys
import telebot
import time
import logging
from telebot import types
from modules import youtube_search, search_list

# Определение константы для имени базы данных
DB_NAME = 'app.db'
token = 'TELEGRAM_BOT_API'
bot = telebot.TeleBot(token)
logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Функция для установления соединения с базой данных
def connect_to_db():
    return sqlite3.connect(DB_NAME)

# Функция для инициализации пользователя в базе данных
def add_user(chat_id):
    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute('INSERT OR IGNORE INTO Users (Id, Counter) VALUES (?, ?)', (chat_id, 1))
        connection.commit()

        logging.info(f'User with chat ID {chat_id} has been added to the database')
    except sqlite3.Error as e:
        logging.error(f'An error occurred while adding user with chat ID {chat_id}: {e}')
        print(f"An error occurred: {e}")
        
    finally:
        if connection:
            connection.close()

# Функция для обработки команды /start или /help
@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    # Извлечение информации из объекта message
    chat_id = message.chat.id
    username = message.chat.username
    first_name = message.chat.first_name
    last_name = message.chat.last_name
    

    logging.info(f'New message received from chat ID: {chat_id}')
    logging.debug(f'Username: {username}, First Name: {first_name}, Last Name: {last_name}')

    # Отправка приветственного сообщения
    bot.send_message(chat_id, text='Hello! With this bot you can quickly search for videos on YouTube video sharing. \
                     If you add a period before the first character (“.someone”), the bot will display a list of links. \
                     Please enter your search query:')

    # Инициализация пользователя в базе данных
    add_user(chat_id)

# Функция для отправки следующего видео пользователю
def send_next_video(chat_id, counter):

    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        cursor.execute('SELECT * FROM SearchResult WHERE UserId=:Id', {'Id': chat_id})
        results = cursor.fetchall()

        if results:
            video_sender = results[counter][1]
            logging.info(f'Sending video to chat ID {chat_id}: {video_sender}')
            bot.send_message(chat_id, text=video_sender)

            # Обновляем счетчик для пользователя
            cursor.execute("UPDATE Users SET Counter = Counter + 1 WHERE Id=:Id", {"Id": chat_id})
            connection.commit()

            # Отправляем клавиатуру с кнопкой "Next"
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
            callback_button = types.InlineKeyboardButton(text="/next", callback_data="test")
            keyboard.add(callback_button)
            bot.send_message(chat_id, 'To get the next video, click /next...', reply_markup=keyboard)

        else:
            bot.send_message(chat_id, 'No more videos available.')

    except sqlite3.Error as e:
        logging.error(f'An error occurred while sending the next video to chat ID {chat_id}: {e}')
        print(f"An error occurred: {e}")
    finally:
        if connection:
            connection.close()

# Функция для выполнения поиска на YouTube и отправки результатов пользователю
def perform_youtube_search(chat_id, text):

    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        # Очищаем предыдущие результаты пользователя
        cursor.execute('DELETE FROM SearchResult WHERE UserId=:Id', {'Id': chat_id})
        cursor.execute("UPDATE Users SET Counter = 0 WHERE Id=:Id", {'Id': chat_id})
        connection.commit()

        # Выполняем функцию youtube_search, которая заполняет таблицу SearchResult
        # ссылками на видео
        youtube_search(chat_id, text)

        # Отправляем первый результат пользователю
        send_next_video(chat_id, 0)
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if connection:
            connection.close()

@bot.message_handler(commands=['next'])
def next_video(message):
    chat_id = message.chat.id

    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        # Получаем текущий счетчик для пользователя
        cursor.execute('SELECT Counter FROM Users WHERE Id= ?', (chat_id,))
        counter = cursor.fetchone()[0]

        # Увеличиваем счетчик и обновляем его в базе данных
        new_counter = counter + 1
        cursor.execute("UPDATE Users SET Counter = ? WHERE ID = ?", (new_counter, chat_id))
        connection.commit()

        # Получаем данные о видео по новому счетчику
        cursor.execute('SELECT * FROM SearchResult WHERE UserId = ?', (chat_id,))
        video_link = cursor.fetchall()

        if video_link:
            bot.send_message(chat_id, text=video_link[new_counter][1])
        else:
            bot.send_message(chat_id, text='No more videos available. Try once more')
            

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if connection:
            connection.close()

# Обработчик всех остальных текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text
    user_name = message.chat.username
    first_name = message.chat.first_name
    last_name = message.chat.last_name

    # Обработка текстовых сообщений
    # Сообщения с точкой в начале сообщения возвращают список ссылок

    if '.' in message.text:
        request = text.split(".")[1]
        bot.send_message(message.chat.id, search_list(request)[:4096])

    else:
        perform_youtube_search(chat_id, text)

while True:
    try:
        bot.polling(none_stop=True, interval=1)
    except:
        print('bolt')
        logging.error('error: {}'.format(sys.exc_info()[0]))
        time.sleep(5)
