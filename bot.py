import discord
from discord.ext import commands
import requests
import json
import os
from collections import defaultdict, deque
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# - CONFIG -

# Get bot token from .env file
TOKEN = os.getenv("DISCORD_TOKEN")

# Ollama API endpoint (where AI is running)
OLLAMA_URL = "http://localhost:11434/api/chat"

# Which AI model to use
OLLAMA_MODEL = "mannix/llama3.1-8b-abliterated:q5_K_M"

MAX_HISTORY_MESSAGES = 10  # last 10 messages

SPEEDY_USER_ID = 1542139186981904394

# Load the system prompt from file
with open("prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

# - SETUP -

# Create bot with all permissions
intents = discord.Intents.all()
bot = commands.Bot(intents=intents)

# One deque per channel ID, holding recent {"role":..., "content":...} dicts
channel_histories = defaultdict(lambda: deque(maxlen=MAX_HISTORY_MESSAGES))

# Function for talking to ollama model
def ask_ai(channel_id, user_message):
    try:
        history = channel_histories[channel_id]

        # Build the full messages list: system + recent history + new user message
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)

        # Prepare the request
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,  # Get complete response at once
            "think": False,
            "options": {
                "num_predict": 400,  # Max response length in tokens
                "temperature": 0.7, # Temperature, whatever tf that does (should change creativity)
                "num_ctx": 8096 # small context, no history
            }
        }

        # Send request to Ollama
        response = requests.post(OLLAMA_URL, json=payload, timeout=90)

        # Check if successful
        if response.status_code == 200:
            data = response.json()
            ai_message = data.get("message", {}).get("content", "").strip()

            # Save this exchange to history
            history.append({"role": "assistant", "content": ai_message})

            return ai_message

        else:
            return "Sorry, I had trouble thinking of a response!"

    except requests.exceptions.ConnectionError:
        return "Error: Ollama is not running!"
    except Exception as e:
        return f"Error: {str(e)}"

# - Bot is READY -

@bot.event
async def on_ready():
    """Called when bot successfully connects to Discord"""
    print(f"✅ Bot is online as {bot.user.name}")
    print(f"✅ Connected to {len(bot.guilds)} server(s)")
    print("Ready to chat!")


# - Message received -

@bot.event
async def on_message(message):
    """Called whenever a message is sent in a channel the bot can see"""

    # Don't respond to yourself (prevents infinite loops!)
    if message.author == bot.user:
        # This is the  bot's message log it as "assistant", nothing else to do
        history = channel_histories[message.channel.id]
        history.append({"role": "assistant", "content": message.content})
        return

    # Log every other message as "user"
    history = channel_histories[message.channel.id]
    content = f"{message.author.display_name}: {message.content}"
    history.append({"role": "user", "content": content})

    # Check if bot was mentioned
    if bot.user.mentioned_in(message):
        user_message = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if not user_message:
            user_message = "Hello!"

        async with message.channel.typing():
            ai_response = ask_ai(message.channel.id, user_message)

             # Replace any mention of "speedyclaw" with a real ping
            ai_response = ai_response.replace("@speedyclaw", f"<@{SPEEDY_USER_ID}>")

            await message.channel.send(ai_response)


# - Start bot

if __name__ == "__main__":
    print("Starting bot...")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"Model: {OLLAMA_MODEL}")

    # Run the bot (this blocks until bot stops)
    bot.run(TOKEN)
