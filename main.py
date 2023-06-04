import os
import re
import pytz
import logging
import traceback
import html
import json
# import openai
from sys import stdout
from telethon import TelegramClient
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import filters, MessageHandler, ContextTypes, CommandHandler, ApplicationBuilder
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from unicodedata import normalize
from completion.completion_service import CompletionService
from completion.claude_completion_service import ClaudeCompletionService

load_dotenv()

TELEGRAM_APP_API_ID = int(os.getenv('TELEGRAM_APP_API_ID', ""))
TELEGRAM_APP_API_HASH = os.getenv('TELEGRAM_APP_API_HASH', "")
TELEGRAM_BOT_API_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN', "")
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', "")
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', "")
DEVELOPER_CHAT_ID = int(os.getenv('DEVELOPER_CHAT_ID', ""))
dialog_id = 0

# Set up logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stdout)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


# Init Application
app = ApplicationBuilder().token(TELEGRAM_BOT_API_TOKEN).build()

# Init telegram client
client = TelegramClient('session', TELEGRAM_APP_API_ID, TELEGRAM_APP_API_HASH)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    logger.info("GET - /start")
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Hi! I am a summary bot. Invite me into your group and I will summarize them for you.')


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message when the command /help is issued."""
    logger.info("GET - /help")
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Following command are available: \n /start - Start the bot \n /help - Show this help message \n /echo [MESSAGE] - Echo the user message \n /show_chats - Show all chats the bot is currently in \n /set_chat_name [CHAT NAME] - Set the chat name for the bot \n /summary - Summarize the chat')


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo the user message."""
    logger.info("GET - /echo")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


async def show_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all chats the bot is currently in."""
    logger.info("GET - /show_chats")
    await update.effective_message.reply_text(text=f"Current Chat: {update.effective_chat.id}")


async def set_chat_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the chat name for the bot."""
    logger.info("GET - /set_chat_name")

    try:
        await client.start()
        me = await client.get_me()
        logger.info("Me: ")
        logger.info(me)

        if len(context.args) == 0:
            await update.effective_message.reply_text(text="Please provide a chat name")
            return

        async for dialog in client.iter_dialogs():
            # logger.info("Dialog: " + dialog.title)
            if dialog.title == context.args[0]:
                global dialog_id
                dialog_id = dialog.id
                logger.info("Set dialog ID as: " + str(dialog_id))
                break

    except Exception as e:
        logger.error(f"Error setting chat name: {e}")


async def get_messages_from_telegram_api():
    """Retrieve all messages from Telegram API within last 24 hours."""

    try:
        # Filter out only those messages sent within last 24 hours.
        recent_messages = []
        tz = pytz.timezone('UTC')
        daily_time_filter = datetime.now().astimezone(tz) - timedelta(days=1)
        async for message in client.iter_messages(dialog_id):
            if message.date >= daily_time_filter:
                # TODO: Maybe we can add image and video support later.
                if message.text != '':
                    recent_messages.append({
                        'msg_id': message.id,
                        'sender': message.sender_id,
                        'reply_to_msg_id': message.reply_to_msg_id,
                        'msg': message.text,
                        'channel_id': message.peer_id.channel_id,
                    })
            else:
                logger.info("Last message: ")
                logger.info(message)
                break

        return recent_messages

    except Exception as e:
        logging.error(f"Error retrieving messages from Telegram API: {e}")

# remove whitespace character from message


def remove_whitespace(message):
    message_with_half_width = normalize('NFKC', message)
    clean_msg = re.sub(r"[\s。，]+", " ", message_with_half_width).strip()
    return clean_msg


def summarize_messages(dialog_id, chat_messages, completion_service):
    """Summarize list of text messages using OpenAI service."""

    try:
        messages = f"""
Your task is to extract key point from a conversation in telegram chat room. \

From the conversation below, delimited by triple quotes, \
Message is in csv format, each row is a message mainly talking in chinese. \
The first column is the msg_id, the second column is the sender id, \
the third column is the reply message id (will be empty if it doesn't quote and reply to anyone), \
the fourth column is the message content and the fifth column is the channel_id. \
please summarize the messages into a few key points, each point is in following format. \
`<topic_name> (https://t.me/c/<channel_id>/<msg_id>)`. \
Each topic_name must within 1 or 2 sentences. \

Conversation: ```{chat_messages}```
"""

        # Combine chat_messages into single string
        chats_content = ""
        for chat in chat_messages:
            if chat['reply_to_msg_id'] == None:
                chats_content += f"{chat['msg_id']},{chat['sender']},,{remove_whitespace(chat['msg'])}\n"
            else:
                chats_content += f"{chat['msg_id']},{chat['sender']},{chat['reply_to_msg_id']},{remove_whitespace(chat['msg'])}\n"

        # logger.info("Chats content: ")
        # logger.info(chats_content)

        # Get result from AI
        result = completion_service.get_completion(messages=messages)
        return result

    except Exception as e:
        logging.error(f"Error summarizing messages: {e}")
        traceback.print_exc(file=sys.stdout)


async def summarize(update, context, completion_service: CompletionService):
    """Retrieve and send back stored key points."""

    logger.info("GET - /summarize")

    if dialog_id == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please set chat name first.")
        return

    try:
        await client.start()
        me = await client.get_me()
        logger.info("Me: ")
        logger.info(me)

        # Get messages from Telegram API
        result = await get_messages_from_telegram_api()
        # logger.info("Messages: ")
        # logger.info(messages)
    except Exception as e:
        logging.error(f"Error connecting to Telegram API: {e}")

    # Summarize messages using OpenAI
    summarized_text_list = summarize_messages(
        dialog_id=dialog_id, chat_messages=result, completion_service=completion_service)

    # Send back summarized text as a message to user who requested it
    await context.bot.send_message(chat_id=update.effective_chat.id, text=summarized_text_list)
    # await context.bot.send_message(chat_id=update.effective_chat.id, text=messages)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Done")

    # Retrieve recent messages from Telegram API.

    # Summarize the retrieved messages using OpenAI service.

    # Send back summarized text as a message to user who requested it


# From https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/errorhandlerbot.py
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message to developer channel
    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
    )


if __name__ == '__main__':

    # Inject dependencies for completion service
    completion_service = ClaudeCompletionService(
        api_key=CLAUDE_API_KEY, predefined_context="")

    # Add handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help))
    app.add_handler(CommandHandler('summary', lambda update,
                    context: summarize(update, context, completion_service)))
    app.add_handler(CommandHandler('set_chat_name', set_chat_name))
    app.add_handler(CommandHandler('show_chats', show_chats))
    # app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    app.add_error_handler(error_handler)

    app.run_polling()
