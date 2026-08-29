import discord
from discord.ext import commands
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# - CONFIG -

# Get bot token from .env file
TOKEN = os.getenv("DISCORD_TOKEN")

# Ollama API endpoint (where AI is running)
OLLAMA_URL = "http://localhost:11434/api/generate"

# Which AI model to use
OLLAMA_MODEL = "mannix/llama3.1-8b-abliterated:q5_K_M"

# - SETUP -

# Create bot with all permissions
intents = discord.Intents.all()
bot = commands.Bot(intents=intents)

# Function for talking to ollama model
def ask_ai(prompt):
    try:
        # Prepare the request
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,  # Get complete response at once
            "options": {
                "num_predict": 400  # Max response length in tokens
            }
        }

        # Send request to Ollama
        response = requests.post(OLLAMA_URL, json=payload, timeout=90)

        # Check if successful
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "").strip()
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
        return

    # I might want him to talk to speedy

    # # Don't respond to other bots
    # if message.author.bot:
    #     return

    # Check if bot was mentioned
    if bot.user.mentioned_in(message):
        # Remove the mention from the message
        user_message = message.content.replace(f'<@{bot.user.id}>', '').strip()

        # If they just mentioned with no text
        if not user_message:
            user_message = "Hello!"

        # Show typing indicator (looks more natural)
        async with message.channel.typing():
            # Ask AI for response
            ai_response = ask_ai(user_message)

            # Send response
            await message.channel.send(ai_response)


# - Start bot

if __name__ == "__main__":
    print("Starting bot...")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"Model: {OLLAMA_MODEL}")

    # Run the bot (this blocks until bot stops)
    bot.run(TOKEN)
