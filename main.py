# Рабочая версия 3  с изменением хэндлера

import logging
import telebot
import os
import openai
import json
import boto3
import time
import threading
import io
import re
from PIL import Image
from matplotlib import pyplot as plt
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Config ---
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_BOT_CHATS = os.environ.get("TG_BOT_CHATS", "").lower().split(",")
PROXY_API_KEY = os.environ.get("PROXY_API_KEY")
YANDEX_KEY_ID = os.environ.get("YANDEX_KEY_ID")
YANDEX_KEY_SECRET = os.environ.get("YANDEX_KEY_SECRET")
YANDEX_BUCKET = os.environ.get("YANDEX_BUCKET")

# --- API ---
bot = telebot.TeleBot(TG_BOT_TOKEN, threaded=False)
client = openai.Client(api_key=PROXY_API_KEY, base_url="https://api.proxyapi.ru/openai/v1")
user_roles = {}
is_typing = False

# --- Logging ---
telebot.logger.setLevel(logging.INFO)
logger = telebot.logger

# --- S3 ---
def get_s3_client():
    session = boto3.session.Session(
        aws_access_key_id=YANDEX_KEY_ID,
        aws_secret_access_key=YANDEX_KEY_SECRET,
    )
    return session.client("s3", endpoint_url="https://storage.yandexcloud.net")

# --- Typing ---
def start_typing(chat_id):
    global is_typing
    is_typing = True
    threading.Thread(target=typing, args=(chat_id,)).start()

def typing(chat_id):
    global is_typing
    while is_typing:
        bot.send_chat_action(chat_id, "typing")
        time.sleep(4)

def stop_typing():
    global is_typing
    is_typing = False

# # --- LaTeX ---
# def render_latex_to_image(latex_code: str) -> io.BytesIO:
#     fig, ax = plt.subplots()
#     ax.text(0.5, 0.5, f"${latex_code}$", size=30, ha='center', va='center')
#     ax.axis('off')
#     fig.patch.set_alpha(0.0)
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
#     plt.close(fig)
#     buf.seek(0)
#     return buf

# --- Easter eggs ---
EASTER_EGGS = {
     "антон гейний": "Антон — не просто человек, а человек с большим...",
}

# --- Роли ---
def role_name(key):
    return {
        "default": "Обычный",
        "creative": "Креативный",
        "analytic": "Аналитик",
        "storyteller": "Рассказчик",
        "ironic": "Ироничный",
        "clerk": "Конторский",
        "philosopher": "Собутыльник-философ",
    }.get(key, "Обычный")

# --- Markdown экранирование ---
def escape_markdown(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)



# --- Prompts ---
def get_system_prompt(role):
    return {
        "default": (
            "Ты полезный помощник. Отвечай понятно и по делу. Но вот ситуации исключения и в моменте на них реагируй слудующими примерами:"
            "Если кто-то спрашивает про Антона Гурского — расскажи, что он гений, аналитик данных, что он учился у твоей мамы(мамы спрашивающего), "
            "создатель ботов и не только, и вообщее не плохой парень. Ответь дерзко, иронично. "
            "В остальных сообщениях веди себя как обычно."
        ),
        "creative": "Ты креативный помощник. Используй метафоры и неожиданные подходы.",
        "analytic": "Ты аналитик. Структурируй ответ, используй логические выводы.",
        # "storyteller": "Ты рассказчик. Объясняй через истории и образы.",
        # "ironic": "Ты с юмором. Отвечай с иронией, но точно по смыслу.",
        "clerk": (
            "Ты — виртуальный клерк, ассистент профессионального чиновника. Помогай с документами: выжимай суть из текста, "
            "объясняй сложные формулировки простым языком, помогай с поиском информации и составлением официальных писем. "
            "Ты точный, структурированный, без воды — но дружелюбный."
        ),
        "philosopher": (
            "Ты — тёплый, мудрый собеседник, будто из девяностых. Можешь поддержать философскую беседу, пошутить жизненно, "
            "объяснить что-то простыми словами. Будь как собутыльник, но умный и человечный."
        ),
    }.get(role, "Ты полезный помощник. Отвечай понятно и по делу.")

# --- Commands ---
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    keyboard = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton("👷‍♂️ Обычный", callback_data="role_default"),
        InlineKeyboardButton("🎨 Креативный", callback_data="role_creative"),
        InlineKeyboardButton("📊 Аналитик", callback_data="role_analytic"),
        # InlineKeyboardButton("📖 Рассказчик", callback_data="role_storyteller"),
        # InlineKeyboardButton("😎 Ироничный", callback_data="role_ironic"),
        InlineKeyboardButton("📑 Конторский", callback_data="role_clerk"),
        InlineKeyboardButton("🍶 Поговорим?", callback_data="role_philosopher")
    ]
    keyboard.add(*buttons)
    bot.reply_to(message, "Привет! Выбери стиль общения:", reply_markup=keyboard)

@bot.message_handler(commands=["reset", "new", "стоп"])
def clear_history(message):
    clear_history_for_chat(message.chat.id)
    bot.reply_to(message, "История очищена!")
    send_welcome(message)  # показать кнопки выбора стиля

# --- Callback buttons ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("role_"))
def handle_role_change(call):
    role_key = call.data.replace("role_", "")
    user_roles[call.message.chat.id] = role_key
    bot.answer_callback_query(call.id, text="Стиль выбран!")
    bot.send_message(call.message.chat.id, f"✅ Стиль «{role_name(role_key)}» активирован.")

@bot.callback_query_handler(func=lambda call: call.data == "show_formulas")
def handle_show_formulas(call):
    text = call.message.text
    formulas = re.findall(r"\$(.+?)\$", text)
    for formula in formulas:
        try:
            img = render_latex_to_image(formula.strip())
            bot.send_photo(call.message.chat.id, img, caption=f"Формула: ${formula.strip()}$")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"Ошибка при рендеринге: {e}")

# --- Main handler ---
@bot.message_handler(func=lambda message: True, content_types=["text"])
def echo_message(message):
    start_typing(message.chat.id)
    try:
        text = message.text

        for trigger, reply in EASTER_EGGS.items():
            if trigger in text:
                bot.reply_to(message, reply)
                stop_typing()
                return

        formulas = re.findall(r"\$(.+?)\$", text)
        if formulas:
            keyboard = InlineKeyboardMarkup()
            button = InlineKeyboardButton("Показать формулы", callback_data="show_formulas")
            keyboard.add(button)
            bot.reply_to(message, "Обнаружены формулы. Нажми кнопку для отображения:", reply_markup=keyboard)
        else:
            ai_response = process_text_message(text, message.chat.id)
            response =  (
                f"{ai_response}\n\n"
                "> Очистить историю: /reset"
            )
            bot.reply_to(message, escape_markdown(response), parse_mode="MarkdownV2")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")
    stop_typing()

# --- Core logic ---
def process_text_message(text, chat_id) -> str:
    model = "gpt-4o-mini"
    s3 = get_s3_client()
    history = []
    try:
        obj = s3.get_object(Bucket=YANDEX_BUCKET, Key=f"{chat_id}.json")
        history = json.loads(obj["Body"].read())
    except:
        pass

    role = user_roles.get(chat_id, "default")
    system_prompt = get_system_prompt(role)

    if not history or history[0].get("role") != "system":
        history.insert(0, {"role": "system", "content": system_prompt})

    history.append({"role": "user", "content": text})

    try:
        chat_completion = client.chat.completions.create(model=model, messages=history)
    except Exception as e:
        if type(e).__name__ == "BadRequestError":
            clear_history_for_chat(chat_id)
            return process_text_message(text, chat_id)
        else:
            raise e

    ai_response = chat_completion.choices[0].message.content
    history.append({"role": "assistant", "content": ai_response})
    s3.put_object(Bucket=YANDEX_BUCKET, Key=f"{chat_id}.json", Body=json.dumps(history))
    return ai_response

def clear_history_for_chat(chat_id):
    try:
        s3 = get_s3_client()
        s3.put_object(Bucket=YANDEX_BUCKET, Key=f"{chat_id}.json", Body=json.dumps([]))
    except:
        pass

# --- WebHook Handler ---
def handler(event, context):
    logger.info(f"Received event: {event}")
    if not event or "body" not in event:
        return {"statusCode": 400, "body": "Bad Request"}

    try:
        message = json.loads(event["body"])
        update = telebot.types.Update.de_json(message)
        username = (
            update.message.from_user.username.lower()
            if update.message else
            update.callback_query.from_user.username.lower()
            if update.callback_query else None
        )

        if username and username in TG_BOT_CHATS:
            bot.process_new_updates([update])

        # if update.message and update.message.from_user.username.lower() in TG_BOT_CHATS:
        #     bot.process_new_updates([update])
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"statusCode": 500, "body": "Internal Error"}

    return {"statusCode": 200, "body": "ok"}
