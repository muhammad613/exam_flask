import telebot
from telebot import types
import subprocess
from tasks_answers_link import tasks, answers, course_links, book_link

# Создание экземпляра бота
bot = telebot.TeleBot('6532220819:AAENCSn896fwXthi2jvbw3vURVzZRUKhZTo')

# Словарь для хранения данных пользователей
user_data = {}

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🐍Python", "👨🏻‍💻Курсы", "📚Книги")
    bot.send_message(message.chat.id, "Привет. Это бот задачник по программированию \nВыберите язык или раздел:", reply_markup=markup)
    user_data[message.chat.id] = {}

# Обработчик раздела "Курсы"
@bot.message_handler(func=lambda message: message.text == "👨🏻‍💻Курсы")
def courses(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    buttons = []
    for language, links in course_links.items():
        for link in links:
            buttons.append(types.InlineKeyboardButton(language, url=link))
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Выберите курс и можете сразу скачивать:", reply_markup=markup)

# Обработчик раздела "Книги"
@bot.message_handler(func=lambda message: message.text == "📚Книги")
def books(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    book_button = types.InlineKeyboardButton("📚Книги", url=book_link)
    markup.add(book_button)
    bot.send_message(message.chat.id, "Ссылка на скачивние книг:", reply_markup=markup)

# Обработчик выбора языка
@bot.message_handler(func=lambda message: message.text in ["🐍Python"])
def choose_language(message):
    user_id = message.from_user.id
    user_data[user_id] = {'language': message.text, 'current_task_index': 0}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🌟Easy", "⭐️Medium", "🔥Hard")
    bot.send_message(message.chat.id, "Выберите уровень:", reply_markup=markup)
    bot.register_next_step_handler(message, choose_level)

# Обработчик выбора уровня сложности
def choose_level(message):
    user_id = message.from_user.id
    user_data[user_id]['level'] = message.text

    language = user_data[user_id]['language']
    level = user_data[user_id]['level']

    tasks_for_level = tasks.get(language, {}).get(level, [])
    user_data[user_id]['tasks_for_level'] = tasks_for_level

    if not tasks_for_level:
        bot.send_message(message.chat.id, "Для выбранного языка и уровня задачи отсутствуют.")
        return

    user_data[user_id]['current_task_index'] = 0
    task_index = user_data[user_id]['current_task_index']
    task = tasks_for_level[task_index]

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    bot.send_message(message.chat.id, task, reply_markup=markup)
    bot.register_next_step_handler(message, process_solution)

# Обработчик ввода решения задачи
def process_solution(message):
    global response
    user_id = message.from_user.id
    user_data[user_id]['solution'] = message.text

    language = user_data[user_id]['language']
    level = user_data[user_id]['level']
    answer = answers.get(language, {}).get(level, [])[user_data[user_id]['current_task_index']]
    solution = user_data[user_id]['solution']

    expected_output = answer.strip()

    with open("user_code.py", "w") as code_file:
        code_file.write(solution)

    try:
        result = subprocess.check_output(["python", "user_code.py"], stderr=subprocess.STDOUT, timeout=5,
                                         universal_newlines=True).strip()

        if result == expected_output:
            response = "Правильно! Ответ верный."
        else:
            response = "Неправильно. Попробуйте ещё раз. Введите новое решение:"
            bot.send_message(user_id, response)
            bot.register_next_step_handler(message, process_solution)  # Ожидаем новое решение и выходим из функции
            return  # Выходим из функции после отправки сообщения

    except subprocess.TimeoutExpired:
        response = "Превышено время выполнения. Попробуйте ещё раз. Введите новое решение:"
    except subprocess.CalledProcessError:
        response = "Ошибка выполнения кода. Попробуйте ещё раз. Введите новое решение:"
    finally:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        bot.send_message(user_id, response, reply_markup=markup)

    user_data[user_id]['current_task_index'] += 1
    current_task_index = user_data[user_id]['current_task_index']
    tasks_for_level = user_data[user_id]['tasks_for_level']

    if current_task_index < len(tasks_for_level):
        task = tasks_for_level[current_task_index]
        bot.send_message(message.chat.id, task)
        bot.register_next_step_handler(message, process_solution)
    else:
        markup = types.InlineKeyboardMarkup()  # Создаем inline-клавиатуру
        button = types.InlineKeyboardButton(text="Меню", callback_data="choose_language")
        markup.add(button)

        bot.send_message(user_id, "Все задачи завершены. Меню:", reply_markup=markup)

# Обработчик inline-клавиши "Меню"
@bot.callback_query_handler(func=lambda call: call.data == "choose_language")
def callback_choose_language(call):
    user_id = call.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🐍Python", "👨🏻‍💻Курсы", "📚Книги")
    bot.send_message(user_id, "Выберите язык или раздел:", reply_markup=markup)

# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)
