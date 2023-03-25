import os
import discord
from discord.ext import commands
import openai
import asyncio
import traceback
import re
import logging
import time
import requests
import json
from io import BytesIO

logging.basicConfig(level=logging.DEBUG)

DISCORD_TOKEN = ''
OPENAI_API_KEY = ''

openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

conversation_history = {}

async def generate_openai_response(prompt, conversation_id):
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, openai_response, prompt, conversation_id)
    return response

def openai_response(prompt, conversation_id):
    if conversation_id not in conversation_history:
        conversation_history[conversation_id] = [
            {"role": "system", "content": "You are a helpful discord member, you know it is 2023 and you are running on gpt69"}
        ]

    user_message = {"role": "user", "content": prompt}
    conversation_history[conversation_id].append(user_message)

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=conversation_history[conversation_id],
        max_tokens=50
    )

    assistant_message = response.choices[0].message['content'].strip()
    conversation_history[conversation_id].append({"role": "assistant", "content": assistant_message})

    conversation_history[conversation_id] = conversation_history[conversation_id][-10:]

    return assistant_message

@bot.command(name='gpt4')
async def gpt4_command(ctx, *, prompt: str):
    conversation_id = f"{ctx.guild.id}-{ctx.channel.id}"
    try:
        response = await generate_openai_response(prompt, conversation_id)
        if response.strip():
            await ctx.send(response)
        else:
            await ctx.send("I'm sorry, I couldn't generate a response.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

def generate_image(prompt, n=1, size='512x512'):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }

    data = {
        "prompt": prompt,
        "n": n,
        "size": size
    }

    response = requests.post('https://api.openai.com/v1/images/generations', headers=headers, data=json.dumps(data))
    return response.json()

async def send_image_url_as_image(message, image_url):
    response = requests.get(image_url)
    image_data = BytesIO(response.content)
    await message.channel.send(file=discord.File(image_data, "generated_image.png"), reference=message)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message) and message.mention_everyone is False:
        mention_start = message.content.startswith(f"<@!{bot.user.id}>")
        prompt = message.content.replace(f"<@!{bot.user.id}>", "").strip()
        conversation_id = f"{message.guild.id}-{message.channel.id}"
        
        if mention_start and prompt.lower().startswith("imagine "):
            image_prompt = prompt[8:]
            try:
                generating_message = await message.reply("Generating image, please wait...")
                response = generate_image(image_prompt)
                if 'data' in response and len(response['data']) > 0:
                    image_url = response['data'][0]['url']
                    await generating_message.delete()
                    await send_image_url_as_image(message, image_url)
                else:
                    await generating_message.edit(content="I'm sorry, I couldn't generate an image.")
            except Exception as e:
                await generating_message.edit(content=f"Error: {str(e)}")
        else:
            try:
                response = await generate_openai_response(prompt, conversation_id)
                if response.strip():
                    await message.reply(response)
                else:
                    await message.reply("I'm sorry, I couldn't generate a response.")
            except Exception as e:
                await message.reply(f"Error: {str(e)}")

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
