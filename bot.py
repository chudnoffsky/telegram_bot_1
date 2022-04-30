import telebot
import config
import random
import utils
import time
import COVID19Py
import pyowm
import requests
import datetime
import sys
import sqlite3

from pyowm.owm import OWM
from pyowm.utils.config import get_default_config
from requests import get
from telebot import TeleBot, types
from bs4 import BeautifulSoup as BS
from random import randint

# база данных
conn = sqlite3.connect('db/database.db', check_same_thread=False)
cursor = conn.cursor()


# создание бд если её нет
def create_tables():
    users_query = '''CREATE TABLE IF NOT EXISTS USERS 
                        (user_id INTEGER PRIMARY KEY NOT NULL,
                        user_name TEXT,
                        user_surname TEXT,
                        username TEXT)'''
    cursor.execute(users_query)
    conn.commit()


create_tables()


# записываем в бд
def db_table_val(user_id: int, user_name: str, user_surname: str, username: str):
    cursor.execute('INSERT INTO users (user_id, user_name, user_surname, username) VALUES (?, ?, ?, ?)',
                   (user_id, user_name, user_surname, username))
    conn.commit()


# язык
config_dict = get_default_config()
config_dict['language'] = 'ru'
owm = OWM(config.WEATHER_API, config_dict)

# covid19 = COVID19Py.COVID19()
covid19 = COVID19Py.COVID19(url="https://cvtapi.nl")

bot = telebot.TeleBot(config.TOKEN)
api_weather = config.WEATHER_API
response = requests.get(config.URLPRIVAT).json()
apikey = config.APIKEYYANDEX


# start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    sticker = open('img/welcome.webp', 'rb')
    bot.send_sticker(message.chat.id, sticker)
    # клавиатура
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Помощь")
    btn2 = types.KeyboardButton("Игры")
    btn3 = types.KeyboardButton("Разное")
    btn4 = types.KeyboardButton("Регистрация")

    markup.add(btn1, btn2, btn3, btn4)
    # сообщение при команде старт
    msg = bot.send_message(message.chat.id,
                           "Добро пожаловать, {0.first_name}!\nЯ - <b>{1.first_name}</b>, бот созданный чтобы быть "
                           "подопытным кроликом.".format(
                               message.from_user, bot.get_me()),
                           parse_mode='html', reply_markup=markup)
    bot.register_next_step_handler(msg, process_select_step)


# главное меню
def menu(message):
    # клавиатура
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Помощь")
    btn2 = types.KeyboardButton("Игры")
    btn3 = types.KeyboardButton("Разное")
    btn4 = types.KeyboardButton("Регистрация")

    markup.add(btn1, btn2, btn3, btn4)
    msg = bot.send_message(message.chat.id, "Вы в снова в главном меню".format(message.from_user, bot.get_me()),
                           parse_mode='html', reply_markup=markup)
    bot.register_next_step_handler(msg, process_select_step)


# обработчик меню
def process_select_step(message):
    try:
        if message.text == 'Помощь':
            helps(message)
        elif message.text == 'Разное':
            other_command(message)
        elif message.text == 'Игры':
            games(message)
        elif message.text == 'Регистрация':
            register_user_confirm(message)
        else:
            send_welcome(message)

    except Exception as e:
        return menu(message)


# регистрация пользователей в бд
def register_user_confirm(message):
    us_id = message.from_user.id
    us_name = message.from_user.first_name
    us_sname = message.from_user.last_name
    username = message.from_user.username

    db_table_val(user_id=us_id, user_name=us_name, user_surname=us_sname, username=username)
    bot.send_message(message.chat.id, "Вы зарегистрированы")


# /help
@bot.message_handler(commands=['help'])
def helps(message):
    message_text = '⚡️ EliteBot by Vladimir v1.0.1\n\n' \
                   + 'Создан для того, чтобы приносить пользу 👀\n' \
                   + 'Тут же можно посмотреть погоду, новости, местоположение, а также и множество других функций - ' \
                     'от игр до гороскопа и курса валют!\n\n' \
                   + '🧩 Чтобы начать взаимодействовать с ботом, используйте нижнее меню.'
    bot.send_message(message.chat.id, message_text)
    menu(message)


def other_command(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Погода")
    btn2 = types.KeyboardButton("Курсы Валют")
    btn3 = types.KeyboardButton("Посты Rss")
    btn4 = types.KeyboardButton("Ковид")
    btn5 = types.KeyboardButton("Гороскоп")
    btn6 = types.KeyboardButton("Моя геолокация")
    btn7 = types.KeyboardButton("Вернуться")

    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    msg = bot.send_message(message.chat.id, "Дополнительные функции:".format(message.from_user, bot.get_me()),
                           parse_mode='html', reply_markup=markup)
    bot.register_next_step_handler(msg, process_select_other_step)


# обработчик меню
def process_select_other_step(message):
    try:
        if message.text == 'Погода' or message.text == '/weather' or message.text == '/weather@TheExcelentBot':
            weather(message)
        elif message.text == 'Курсы Валют':
            coins(message)
        elif message.text == 'Посты Rss':
            read_rss(message)
        elif message.text == 'Ковид':
            covid_cmd(message)
        elif message.text == 'Гороскоп':
            Goroscop(message)
        elif message.text == 'Моя геолокация':
            locationSend(message)
        elif message.text == 'Вернуться' or message.text == '/back' or message.text == '/back@TheExcelentBot':
            menu(message)
        else:
            menu(message)

    except Exception as e:
        return menu(message)


# ДРУГИЕ КОМАНДЫ

# rss
@bot.message_handler(commands=['read_rss'])
def read_rss(message):
    post = utils.feed_parser()
    bot.send_message(message.chat.id, 'Новая информация на выбранных площадках:')
    for key in post.keys():
        bot.send_message(message.chat.id, key + '\n' + post[key])
    return menu(message)


# covid
@bot.message_handler(commands=['covid'])
def covid_cmd(message):
    # keyboard
    markupCovid = types.ReplyKeyboardMarkup(resize_keyboard=True)
    itemus = types.KeyboardButton("США")
    itemru = types.KeyboardButton("Россия")
    itemua = types.KeyboardButton("Украина")
    itemback = types.KeyboardButton("Вернуться")

    markupCovid.add(itemus, itemru, itemua, itemback)

    bot.send_message(message.chat.id, "нажмите на страну чтобы узнать подробности",
                     parse_mode='html', reply_markup=markupCovid)


@bot.message_handler(content_types=['text'])
def covid(message):
    final_covid_message = ""
    get_message_bot = message.text.strip().lower()
    if get_message_bot == "сша":
        location = covid19.getLocationByCountryCode("US")
    elif get_message_bot == "украина":
        location = covid19.getLocationByCountryCode("UA")
    elif get_message_bot == "россия":
        location = covid19.getLocationByCountryCode("RU")
    elif get_message_bot == "вернуться":
        menu(message)
    else:
        covid(message)

    if final_covid_message == "":
        date = location[0]['last_updated'].split("T")
        time = date[1].split(".")
        final_covid_message = f"<u>Данные по стране:</u>\nНаселение: {location[0]['country_population']:,}\n" \
                              f"Последнее обновление: {date[0]} {time[0]}\nПоследние данные:\n<b>" \
                              f"Заболевших: </b>{location[0]['latest']['confirmed']:,}\n<b>Сметрей: </b>" \
                              f"{location[0]['latest']['deaths']:,}"
    bot.send_message(message.chat.id, final_covid_message, parse_mode='html')


# Курсы валют
def coins(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton('USD')
    itembtn2 = types.KeyboardButton('EUR')
    itembtn3 = types.KeyboardButton('RUR')
    itembtn4 = types.KeyboardButton('BTC')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)

    msg = bot.send_message(message.chat.id, "Узнать наличный курс СберБанка (в отделениях)", reply_markup=markup)
    bot.register_next_step_handler(msg, process_coin_step)


def process_coin_step(message):
    try:
        for coin in response:
            if message.text == coin['ccy']:
                bot.send_message(message.chat.id, printCoin(coin['buy'], coin['sale']), parse_mode="Markdown")
                coins(message)

    except Exception as e:
        bot.reply_to(message, 'ошибка')


# курс валют
def printCoin(buy, sale):
    return "💰 *Курс покупки:* " + str(buy) + "\n💰 *Курс продажи:* " + str(sale)


# погода
@bot.message_handler(commands=['weather'])
def weather(message):
    bot.send_message(message.chat.id, 'В каком населённом пункте хотим узнать погоду?')
    bot.register_next_step_handler(message, weatherSend)


def weatherSend(message):
    bot.send_message(message.chat.id, 'Загружаем...')

    try:
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place(message.text)
        w = observation.weather
        temp = w.temperature('celsius')['temp']
        today = datetime.datetime.today()
        # ответ погоды
        answer = 'Сегодня, ' + (
            today.strftime("%d/%m/%Y")) + ' ' + 'в городе ' + message.text + ' ' + w.detailed_status + '\n'
        answer += 'Температура в районе ' + str(temp) + ' по Цельсию.' + '\n\n'
        if temp < 5:
            answer += 'Сейчас на улице холодно, одевайся тепло!'
        elif temp < 17:
            answer += 'Сейчас на улице прохладно, одевайся потеплее!'
        else:
            answer += 'Погода просто каеф! Одевайся как душе угодно!'

        bot.send_message(message.chat.id, answer)
        return menu(message)

    except:
        bot.send_message(message.chat.id, 'Я ещё не знаю такого города :(\nДавай посмотрим погоду в другом месте?')
        return other_command(message)


# игры
@bot.message_handler(commands=['game'])
def games(message):
    # keyboard
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    itemrandom = types.KeyboardButton('Рандомное число')
    itemrandomball = types.KeyboardButton('Магический шар')
    itemrandomOR = types.KeyboardButton('Орёл или Решка')
    itemkvest = types.KeyboardButton('Квест')
    itemback = types.KeyboardButton('Вернуться')
    markup.add(itemrandom, itemrandomball, itemrandomOR, itemkvest, itemback)

    msg = bot.send_message(message.chat.id, "Выберите игру", reply_markup=markup)
    bot.register_next_step_handler(msg, process_select_games_step)


def process_select_games_step(message):
    try:
        if message.text == 'Рандомное число':
            bot.send_message(message.chat.id, str(random.randint(0, 100)))  # рандомное число от 0 до 100
            return menu(message)  # возвращает функцию – games (меню)
        elif message.text == 'Магический шар':
            Magic8Ball(message)
        elif message.text == 'Орёл или Решка':
            Orel_Or_Reshka(message)
        elif message.text == 'Квест':
            games_kvest(message)
        elif message.text == 'Вернуться':
            menu(message)
        else:
            menu(message)

    except Exception as e:
        return menu(message)


# магический шар
answers = [
    'Скорее всего',
    'Перспективы хорошие',
    'Ответ туманный',
    'Попробуйте еще раз',
    'Не могу предсказать сейчас',
    'Спросите позже',
    'Совершенно верно',
    'Лучше не говорить вам сейчас',
    'Несомненно',
    'Без сомнения',
    'Да - определенно',
    'Вы можете положиться на это',
    'Мой ответ - нет',
    'Насколько я понимаю, да',
    'Сконцентрируйтесь и спросите еще раз',
    'Прогноз не так хорош',
    'Не в счет на нем',
    'Мои источники говорят,что нет',
    'Очень сомнительно'
]


def Magic8Ball(message):
    bot.send_message(message.chat.id, "Задайте мне вопрос.")
    get_message_8ball_bot = message.text.strip().lower()
    bot.register_next_step_handler(message, Magic8BallSend)  # следующий шаг – Magic8BallSend


def Magic8BallSend(message):
    bot.send_message(message.chat.id, answers[random.randint(0, len(answers) - 1)])  # рандомный ответ из списка
    games(message)  # возвращает функцию – games (меню)


# орел или решка
answers_orre = [
    'Орёл',
    'Решка'
]


def Orel_Or_Reshka(message):
    bot.send_message(message.chat.id,
                     answers_orre[random.randint(0, len(answers_orre) - 1)])
    games(message)


# гороскоп
first_gor = [
    "Будьте осторожны, сегодня звёзды могут повлиять на ваше финансовое состояние.",
    "Сегодня — идеальный день для новых начинаний.",
    "Оптимальный день для того, чтобы решиться на смелый поступок!",
    "Лучшее время для того, чтобы начать новые отношения или разобраться со старыми.",
    "Плодотворный день для того, чтобы разобраться с накопившимися делами."
]
second_gor = [
    "Но помните, что даже в этом случае нужно не забывать про",
    "Если поедете за город, заранее подумайте про",
    "Те, кто сегодня нацелен выполнить множество дел, должны помнить про",
    "Если у вас упадок сил, обратите внимание на",
    "Помните, что мысли материальны, а значит вам в течение дня нужно постоянно думать про"
]
second_add_gor = [
    "отношения с друзьями и близкими.",
    "бытовые вопросы — особенно те, которые вы не доделали вчера.",
    "себя и своё здоровье, иначе к вечеру возможен полный раздрай.",
    "работу и деловые вопросы, которые могут так некстати помешать планам.",
    "отдых, чтобы не превратить себя в загнанную лошадь в конце месяца."
]
third_gor = [
    "Знайте, что успех благоволит только настойчивым, поэтому посвятите этот день воспитанию духа.",
    "Не нужно бояться одиноких встреч — сегодня то самое время, когда они значат многое.",
    "Злые языки могут говорить вам обратное, но сегодня их слушать не нужно.",
    "Даже если вы не сможете уменьшить влияние ретроградного Меркурия, то хотя бы доведите дела до конца.",
    "Если встретите незнакомца на пути — проявите участие, и тогда эта встреча посулит вам приятные хлопоты."
]


@bot.message_handler(content_types=['text'])
def Goroscop(message):
    bot.send_message(message.from_user.id, "Приветик, сейчас я покажу тебе гороскоп на сегодня.")
    keyboard = types.InlineKeyboardMarkup()

    key_oven = types.InlineKeyboardButton(text='Овен', callback_data='zodiac_gor')
    keyboard.add(key_oven)
    key_telec = types.InlineKeyboardButton(text='Телец', callback_data='zodiac_gor')
    keyboard.add(key_telec)
    key_rak = types.InlineKeyboardButton(text='Рак', callback_data='zodiac_gor')
    keyboard.add(key_rak)
    key_bliznecy = types.InlineKeyboardButton(text='Близнецы', callback_data='zodiac_gor')
    keyboard.add(key_bliznecy)
    key_strelec = types.InlineKeyboardButton(text='Стрелец', callback_data='zodiac_gor')
    keyboard.add(key_strelec)
    key_lev = types.InlineKeyboardButton(text='Лев', callback_data='zodiac_gor')
    keyboard.add(key_lev)
    key_deva = types.InlineKeyboardButton(text='Дева', callback_data='zodiac_gor')
    keyboard.add(key_deva)
    key_vesy = types.InlineKeyboardButton(text='Весы', callback_data='zodiac_gor')
    keyboard.add(key_vesy)
    key_scorpion = types.InlineKeyboardButton(text='Скорпион', callback_data='zodiac_gor')
    keyboard.add(key_scorpion)
    key_ryby = types.InlineKeyboardButton(text='Рыбы', callback_data='zodiac_gor')
    keyboard.add(key_ryby)
    key_kozerog = types.InlineKeyboardButton(text='Козерог', callback_data='zodiac_gor')
    keyboard.add(key_kozerog)
    key_vodoley = types.InlineKeyboardButton(text='Водолей', callback_data='zodiac_gor')
    keyboard.add(key_vodoley)

    bot.send_message(message.from_user.id, text='Выбери свой знак зодиака', reply_markup=keyboard)


# обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.message:
        if call.data == 'zodiac_gor':
            message = random.choice(first_gor) + ' ' + random.choice(second_gor) + ' ' + random.choice(
                second_add_gor) + ' ' + random.choice(third_gor)

            bot.send_message(call.id, message)
            other_command(message)


# геолокация
@bot.message_handler(content_types=["location"])
def locationSend(message):
    bot.send_message(message.chat.id, 'Отправь мне точку на геопозиции или координаты (долгота, широта):')
    bot.register_next_step_handler(message, location)

@bot.message_handler(content_types=["location"])
def location(message):
    if message.location is not None:
        coord = str(message.location.longitude) + ',' + str(message.location.latitude)
        r = requests.get('https://geocode-maps.yandex.ru/1.x/?apikey=' + apikey + '&format=json&geocode=' + coord)
    if (message.text != message.location):
        line = message.text  # получаем строку, которую написал пользователь
        longitude = line.split(' ')[0]  # разбиваем строку на элементы, которые написаны через пробел
        latitude = line.split(' ')[1]
        coord = str(longitude) + ',' + str(latitude)
        r = requests.get('https://geocode-maps.yandex.ru/1.x/?apikey=' + apikey + '&format=json&geocode=' + coord)

    if len(r.json()['response']['GeoObjectCollection']['featureMember']) > 0: 
        address = r.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][ 'GeocoderMetaData']['text']
        bot.send_message(message.chat.id, 'Ваш адрес\n{}'.format(address))
        menu(message)
    else:
        bot.send_message(message.chat.id, 'Не удалось получить Ваш адрес')
        return locationSend(message)


pictures = {
    0: "https://storage.geekclass.ru/images/760e484b-a099-4a7a-a722-5aec9a933614.jpg",
    1: "https://storage.geekclass.ru/images/4637fc41-08df-466a-b112-aa577dba6c1d.jpg",
    2: "https://storage.geekclass.ru/images/c2a2a60c-9c7b-4c3a-b663-42d2559bf869.jpg"
}

states = {}
inventories = {}


@bot.message_handler(commands=["kvest"])
def games_kvest(message):
    user = message.chat.id

    states[user] = 0
    inventories[user] = []
    bot.send_message(user, "Добро пожаловать в квест!")

    process_state(user, states[user], inventories[user])


@bot.callback_query_handler(func=lambda call: True)
def user_answer(call):
    user = call.id
    process_answer(user, call.data)


def process_state(user, state, inventory):
    kb = types.InlineKeyboardMarkup()

    bot.send_photo(user, pictures[state])

    if state == 0:
        kb.add(types.InlineKeyboardButton(text="пойти направо", callback_data="1"))
        kb.add(types.InlineKeyboardButton(text="пойти налево", callback_data="2"))

        bot.send_message(user, "Вы в оказались в темном подземелье, перед вами два прохода.", reply_markup=kb)

    if state == 1:
        kb.add(types.InlineKeyboardButton(text="переплыть", callback_data="1"))
        kb.add(types.InlineKeyboardButton(text="вернуться", callback_data="2"))

        bot.send_message(user, "Перед вами большое подземное озеро, а вдали виднеется маленький остров.",
                         reply_markup=kb)

    if state == 2:
        bot.send_message(user, "Вы выиграли.")


@bot.callback_query_handler(func=lambda call: True)
def process_answer(call, user, answer):
    if states[user] == 0:
        if call.data == "1":
            states[user] = 1
        else:
            if "key" in inventories[user]:
                bot.send_message(user,
                                 "Перед вами закрытая дверь. Вы пробуете открыть ее ключем, и дверь поддается. "
                                 "Кажется, это выход.")
                states[user] = 2
            else:
                bot.send_message(user,
                                 "Перед вами закрытая дверь, и, кажется, без ключа ее не открыть. Придется вернуться "
                                 "обратно.")
                states[user] = 0

    elif states[user] == 1:
        if call.data == "2":
            bot.send_message(user,
                             "И правда, не стоит штурмовать неизвестные воды. Возвращаемся назад...")
            states[user] = 0
        else:
            bot.send_message(user,
                             "Вы пробуете переплыть озеро...")

            chance = randint(0, 100)
            if chance > 30:
                bot.send_message(user,
                                 "Вода оказалось теплой, а в сундуке на острове вы нашли старый ключ. Стоит вернутся "
                                 "обратно.")
                inventories[user].append("key")
                states[user] = 0
            else:
                bot.send_message(user, "На середине озера вас подхватывают волны и возвращают обратно.")
                states[user] = 1

    process_state(user, states[user], inventories[user])


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()

# запуск бота
if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception:
            time.sleep(15)
