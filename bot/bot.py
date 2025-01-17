import logging
import re
import os
import psycopg2
import paramiko
from telebot import TeleBot
from dotenv import load_dotenv

load_dotenv()

# Настройка логгирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция выполнения команды через SSH
def ssh_command(command):
    ssh_host = os.getenv('SSH_HOST')
    ssh_port = os.getenv('SSH_PORT')
    ssh_username = os.getenv('SSH_USERNAME')
    ssh_password = os.getenv('SSH_PASSWORD')

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ssh_host, port=int(ssh_port), username=ssh_username, password=ssh_password)

    stdin, stdout, stderr = ssh_client.exec_command(command)

    output = stdout.read().decode('utf-8')

    ssh_client.close()

    return output

# Функция для выполнения SQL запросов к базе данных PostgreSQL
def execute_sql_query(query, params=None, fetch=True):
    try:
        # Подключение к базе данных
        connection = psycopg2.connect(host=os.getenv('DB_HOST'),
                                      port=os.getenv('DB_PORT'),
                                      user=os.getenv('DB_USER'),
                                      password=os.getenv('DB_PASSWORD'),
                                      database=os.getenv('DB_DATABASE'))

        cursor = connection.cursor()

        # Выполнение SQL запроса
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Если нужно получить результат запроса
        result = None
        if fetch:
            result = cursor.fetchall()

        # Подтверждение выполнения изменений в базе данных
        connection.commit()

        # Закрытие соединения с базой данных
        cursor.close()
        connection.close()

        return result
    except Exception as e:
        print(f"Ошибка при выполнении SQL запроса: {e}")
        return None

# Создание экземпляра бота
bot = TeleBot(os.getenv('TOKEN'))

# Обработчик команды /get_emails
@bot.message_handler(commands=['get_emails'])
def get_emails(message):
    emails_query = "SELECT * FROM emails;"
    emails_result = execute_sql_query(emails_query)
    formatted_result = "\n".join([f"ID: {row[0]}, Email: {row[1]}" for row in emails_result])
    bot.reply_to(message, formatted_result)

# Обработчик команды /get_phone_numbers
@bot.message_handler(commands=['get_phone_numbers'])
def get_phone_numbers(message):
    phone_numbers_query = "SELECT * FROM phonenums;"
    phone_numbers_result = execute_sql_query(phone_numbers_query)
    formatted_result = "\n".join([f"ID: {row[0]}, Phone Number: {row[1]}" for row in phone_numbers_result])
    bot.reply_to(message, formatted_result)

# Обработчик команды /get_repl_logs
@bot.message_handler(commands=['get_repl_logs'])
def get_release(message):
    try:
        release_info = ssh_command('tail -n 50 /tmp/pg.log | grep -i "replication\|streaming\|WAL"')
        if not release_info.strip():
            bot.reply_to(message, "Лог файл пуст или не удалось получить его содержимое.")
            return

        bot.reply_to(message, release_info)
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")

@bot.message_handler(commands=['find_email'])
def find_email(message):
    bot.reply_to(message, "Введите текст, в котором необходимо найти email-адреса:")
    bot.register_next_step_handler(message, process_find_email)

def process_find_email(message):
    text = message.text
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    found_emails = re.findall(email_pattern, text)
    if found_emails:
        email_list = "\n".join(found_emails)
        bot.reply_to(message, f"Найденные email-адреса:\n{email_list}\nХотите сохранить их в базе данных? Отправьте /save_emails")
        # Store found emails in user data and register next step handler
        bot.register_next_step_handler(message, save_emails_command, found_emails)
    else:
        bot.reply_to(message, "Email-адреса не найдены в тексте.")


def save_emails_command(message, found_emails):
    try:
        for email in found_emails:
            print("Сохраняем email:", email)
            insert_query = "INSERT INTO emails (email) VALUES ('{}')".format(email)
            execute_sql_query(insert_query, fetch=False)
        bot.reply_to(message, "Email-адреса успешно сохранены в базе данных.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении email в базе данных: {e}")
        bot.reply_to(message, "Произошла ошибка при сохранении email в базе данных.")

@bot.message_handler(commands=['find_phone_number'])
def find_phone_number(message):
    bot.reply_to(message, "Введите текст, в котором необходимо найти номера телефонов:")
    bot.register_next_step_handler(message, process_find_phone_number)

def process_find_phone_number(message):
    text = message.text
    phone_number_pattern = r'(?:(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{2,4})(?: *x(\d+))?)'
    found_phone_numbers = re.findall(phone_number_pattern, text)
    if found_phone_numbers:
        formatted_phone_numbers = ["-".join(filter(None, phone)) for phone in found_phone_numbers]
        phone_numbers_text = "\n".join(formatted_phone_numbers)
        bot.reply_to(message, f"Найденные номера телефонов:\n{phone_numbers_text}\nХотите сохранить их в базе данных? Отправьте /save_phone_numbers")
        # Store found phone numbers in user data and register next step handler
        bot.register_next_step_handler(message, save_phone_numbers_command, formatted_phone_numbers)
    else:
        bot.reply_to(message, "Номера телефонов не найдены в тексте.")

def save_phone_numbers_command(message, formatted_phone_numbers):
    try:
        for phone_number in formatted_phone_numbers:
            print(phone_number)
            insert_query = "INSERT INTO phonenums (phonenum) VALUES ('{}')".format(phone_number)
            execute_sql_query(insert_query, fetch=False)
        bot.reply_to(message, "Номера телефона успешно сохранены в базе данных.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении номера телефона в базе данных: {e}")
        bot.reply_to(message, "Произошла ошибка при сохранении номера телефона в базе данных.")

bot.polling()
