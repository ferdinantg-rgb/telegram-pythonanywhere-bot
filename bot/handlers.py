import os
from datetime import datetime
from bot.clients import bot, BOT_INFO, store
from bot.config import COMMIT_SHA, HF_SPACE_ID, HOSTING_LABEL, MODEL, RATE_LIMIT
from bot.ai import ask_ai
from bot.helpers import is_allowed, keep_typing, send_reply, should_respond
from bot.history import clear_history
from bot.preferences import get_provider, set_provider
from bot.rate_limit import is_rate_limited

# Verbose console logging for local dev and teaching. Enabled by
# BOT_VERBOSE_LOG=1 (run_local.py sets this automatically). Prints one
# line per inbound/outbound message so kids and teachers can see the
# conversation flow in their terminal while the bot is running.
VERBOSE_LOG = os.environ.get("BOT_VERBOSE_LOG", "").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)


def _log(message, direction: str, text: str) -> None:
    """Print a one-line trace of a message in verbose mode.

    direction is "in" (user → bot) or "out" (bot → user). Text is
    truncated to 500 characters so long AI replies don't flood the
    terminal. Newlines are collapsed for single-line readability.
    """
    if not VERBOSE_LOG:
        return
    user = message.from_user
    user_name = (
        f"@{user.username}" if user.username else (user.first_name or f"user:{user.id}")
    )
    bot_name = f"@{BOT_INFO.username}"
    snippet = (text or "").replace("\n", " ").replace("\r", " ")
    if len(snippet) > 500:
        snippet = snippet[:500] + "..."
    if direction == "in":
        sender, receiver = user_name, bot_name
    else:
        sender, receiver = bot_name, user_name
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {sender} → {receiver}: {snippet}", flush=True)


@bot.message_handler(commands=["start"], func=is_allowed)
def cmd_start(message):
    prompt = """
    Generate a short welcome message for a student using an AI learning assistant.

    Requirements:
    - Friendly and natural tone
    - Explain that the bot teaches step by step
    - Encourage the user to ask questions
    - Mention /help briefly
    - Keep it short
    """

    response = ask_ai(message.from_user.id, prompt)

    bot.send_message(message.chat.id, response)
    
@bot.message_handler(commands=["roll"], func=is_allowed)
def roll(message):
    from random import randint as r
    num=r(1,6)
    bot.send_message(
        message.chat.id,
        f"your number is {num}", 
    )


@bot.message_handler(commands=["help"], func=is_allowed)
def cmd_help(message):
    prompt = """
    Generate a help message for an AI learning assistant.

    Include:
    - List of commands: /start, /help, /reset, /about, /joke, /roll(1/6), /compliment, /fact, /quote, /coin(give red/green), /roast <name>
    - Explain each briefly
    - Encourage learning and asking questions
    - Keep it short and clearly
    """

    response = ask_ai(message.from_user.id, prompt)

    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=["reset"], func=is_allowed)
def cmd_reset(message):
    clear_history(message.from_user.id)
    bot.send_message(message.chat.id, "Conversation cleared. Starting fresh!")


@bot.message_handler(commands=["about"], func=is_allowed)
def cmd_about(message):
    prompt = """
    Generate an "About" message for an AI learning assistant bot.

    Requirements:
    - Explain that this is an AI educational assistant
    - Its purpose is to help users learn step by step
    - Mention that it uses simple explanations, examples, and practice exercises
    - Keep the tone friendly, supportive, and motivating
    - Keep it short and clear (not too technical)
    - End with an encouraging sentence
    - Keep it short
    """

    response = ask_ai(message.from_user.id, prompt)

    bot.send_message(message.chat.id, response)

if HF_SPACE_ID:

    @bot.message_handler(commands=["model"], func=is_allowed)
    def cmd_model(message):
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) == 1:
            current = get_provider(message.from_user.id)
            bot.send_message(
                message.chat.id,
                f"Current provider: {current}\n\n"
                "Options:\n"
                "/model main — Cerebras (fast, multilingual, with memory)\n"
                "/model hf — ArmGPT (Armenian only, slow, no memory)",
            )
            return
        choice = parts[1].strip().lower()
        if choice not in ("main", "hf"):
            bot.send_message(
                message.chat.id, "Invalid choice. Use: /model main or /model hf"
            )
            return
        if not set_provider(message.from_user.id, choice):
            bot.send_message(
                message.chat.id, "Could not save preference. Try again later."
            )
            return
        if choice == "hf":
            bot.send_message(
                message.chat.id,
                "Switched to hf (ArmGPT).\n\n"
                "Note: this is a tiny base completion model trained only on Armenian text. "
                "It will continue whatever you write rather than answer questions, "
                "and it does not understand English. Replies take ~30-60s and there is no memory.",
            )
        else:
            bot.send_message(message.chat.id, "Switched to Main Provider.")

@bot.message_handler(commands=["remember"], func=is_allowed)
def cmd_remember(message):
 note = message.text.split(maxsplit=1)[1] if " " in message.text else ""
 store.set(f"note:{message.from_user.id}", note)
 bot.send_message(message.chat.id, "Saved!")

@bot.message_handler(commands=["recall"], func=is_allowed) 
def cmd_recall(message): 
    note = store.get(f"note:{message.from_user.id}") 
    if note: 
        bot.send_message( message.chat.id, f"Your note: {note}" ) 
    else: 
        bot.send_message( message.chat.id, "You don't have any saved notes." )
 

@bot.message_handler(commands=["joke"], func=is_allowed)
def cmd_joke(message):
 reply = ask_ai(message.from_user.id, "Tell one short, clean programming joke.")
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["compliment"], func=is_allowed)
def cmd_compliment(message):
 reply = ask_ai(message.from_user.id, "Tell one short, clean compliment.")
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["fact"], func=is_allowed)
def cmd_fact(message):
 reply = ask_ai(message.from_user.id, "Tell one short fact about programing.")
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["quote"], func=is_allowed)
def cmd_quote(message):
 reply = ask_ai(message.from_user.id, "Tell one short motivation line.")
 bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=["coin"], func=is_allowed)
def cmd_coin(message):
  from random import randint as r
  num=r(0,1)
  if num==0:
    res="green"
  else:
    res="red"
  bot.send_message(message.chat.id, f"It came up {res}")

@bot.message_handler(commands=["roast"], func=is_allowed)
def cmd_roast(message):
  name = message.text.split(maxsplit=1)[1] if " " in message.text else "you"
  reply = ask_ai(message.from_user.id, f"Write a short, playful, friendly roast of {name}.")
  bot.send_message(message.chat.id, reply)
  

@bot.message_handler(content_types=["text"], func=is_allowed)
def handle_message(message):
    if not should_respond(message):
        return
    text = (message.text or "").replace(f"@{BOT_INFO.username}", "").strip()
    if not text:
        # Edited messages, forwards, or stickers-with-empty-caption can
        # arrive with no usable text. Don't burn rate-limit / AI calls on them.
        return
    _log(message, "in", text)
    if is_rate_limited(message.from_user.id):
        limit_msg = f"You've reached the daily limit of {RATE_LIMIT} messages. Try again tomorrow."
        bot.send_message(message.chat.id, limit_msg)
        _log(message, "out", f"[rate limited] {limit_msg}")
        return
    try:
        with keep_typing(message.chat.id):
            reply = ask_ai(message.from_user.id, text)
        send_reply(message, reply)
        _log(message, "out", reply)
    except Exception as e:
        print(f"Error in handle_message: {e}")
        bot.send_message(message.chat.id, "Something went wrong. Please try again.")
        _log(message, "out", f"[error] {e}")
