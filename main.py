import telebot
import requests
import jsons
from my_token import API_TOKEN
from Class_ModelResponse import ModelResponse

bot = telebot.TeleBot(API_TOKEN)

# Словарь для хранения истории сообщений каждого пользователя
user_contexts = {}


# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очистить память нейросети о предыдущих сообщениях\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['model'])
def send_model_name(message):
    # Отправляем запрос к LM Studio для получения информации о модели
    response = requests.get('http://localhost:1234/v1/models')

    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"Используемая модель: {model_name}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')

@bot.message_handler(commands=['clear'])
def clear_message_history(message):
    user_id = message.from_user.id

    if user_id in user_contexts:
        user_contexts[user_id].clear()


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_query = message.text

    # Инициализируем историю пользователя, если её нет
    if user_id not in user_contexts:
        user_contexts[user_id] = []

    # Добавляем текущее сообщение пользователя в историю
    user_contexts[user_id].append({"role": "user", "content": user_query})

    # Создаём запрос к модели с историей сообщений
    request = {
        "messages": user_contexts[user_id]
    }

    response = requests.post(
        'http://localhost:1234/v1/chat/completions',
        json=request
    )

    if response.status_code == 200:
        model_response: ModelResponse = jsons.loads(response.text, ModelResponse)

        # Добавляем ответ модели в историю
        assistant_response = model_response.choices[0].message.content
        user_contexts[user_id].append({"role": "assistant", "content": assistant_response})

        # Отправляем ответ пользователю
        bot.reply_to(message, assistant_response)

        # Ограничиваем длину истории (например, последние 10 сообщений)
        if len(user_contexts[user_id]) > 10:
            user_contexts[user_id] = user_contexts[user_id][-10:]
    else:
        bot.reply_to(message, 'Произошла ошибка при обращении к модели.')


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
