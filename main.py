import os
import discord
from discord.ext import commands
import openai
import asyncio
import traceback
import re
import logging
import time
import json
from io import BytesIO
import io
import warnings
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
import sqlite3
import sys
import random
import aiohttp
import httpx

if '--verbose' in sys.argv:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)

DISCORD_TOKEN = ''
openai.api_key = ''
os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'
os.environ[
  'STABILITY_KEY'] = ''
GOOGLE_PLACES_API_KEY = ''
OPENWEATHER_API_KEY = ''

gmaps = Client(GOOGLE_PLACES_API_KEY)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

conn = sqlite3.connect('conversation_history.db')
c = conn.cursor()

gmaps = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)

def create_user_table(user_id):
    table_name = f"user_{user_id}_history"
    c.execute(f'''CREATE TABLE IF NOT EXISTS {table_name}
                (conversation_id TEXT PRIMARY KEY, messages TEXT)''')
    conn.commit()

async def generate_openai_response(prompt, conversation_id, user_id):
    response = await openai_response(prompt, conversation_id, user_id)
    return response

async def generate_stability_image(image_prompt, width=960, height=768):
    stability_api = client.StabilityInference(
        key=os.environ['STABILITY_KEY'],
        verbose=True,
        engine="stable-diffusion-v1-5",
    )

    random_seed = random.randint(0, 2**32 - 1)  # Generate a random seed

    answers = stability_api.generate(
        prompt=image_prompt,
        seed=random_seed,
        steps=50,
        cfg_scale=11.0,
        width=960,
        height=768,
        samples=2,
        sampler=generation.SAMPLER_K_EULER_ANCESTRAL
    )
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = Image.open(io.BytesIO(artifact.binary))
                img_data = io.BytesIO()
                img.save(img_data, format="PNG")
                img_data.seek(0)
                return img_data

async def handle_image_generation(message, prompt):
    if prompt.lower().startswith("imagine "):
        image_prompt = prompt[8:].strip()
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
    elif prompt.lower().startswith("stable imagine "):
        image_prompt = prompt[15:].strip()
        try:
            generating_message = await message.reply("Generating image, please wait...")
            image_data = await generate_stability_image(image_prompt)
            if image_data:
                await generating_message.delete()
                await message.channel.send(file=discord.File(image_data, "generated_image.png"))
            else:
                await generating_message.edit(content="I'm sorry, I couldn't generate an image.")
        except Exception as e:
            await generating_message.edit(content=f"Error: {str(e)}")

async def get_location_details(location):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
            params={
                "input": location,
                "inputtype": "textquery",
                "fields": "formatted_address,geometry",
                "key": GOOGLE_PLACES_API_KEY,
            },
        )

    result = response.json()
    if result["status"] == "OK":
        place = result["candidates"][0]
        address = place["formatted_address"]
        lat = place["geometry"]["location"]["lat"]
        lng = place["geometry"]["location"]["lng"]
        return address, lat, lng
    return None

def get_weather_data(lat, lng):
    weather = owm.get_current((lat, lng), units='metric', appid=OPENWEATHER_API_KEY)
    return weather

async def test_openweather_api(lat, lon):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None

# Test with Washington, D.C. coordinates
lat = 38.8951100
lon = -77.0363700
weather_data = test_openweather_api(lat, lon)

if weather_data is not None:
    print(weather_data)
else:
    print("Error: Unable to fetch weather data.")

async def openai_response(prompt, conversation_id, user_id):
    table_name = f"user_{user_id}_history"
    c.execute(f"SELECT messages FROM {table_name} WHERE conversation_id=?", (conversation_id,))
    row = c.fetchone()
    if row is None:
        messages = [
            {"role": "system", "content": "You are a helpful discord member that keeps completions as concise as possible"}
        ]
        c.execute(f"INSERT INTO {table_name} VALUES (?, ?)", (conversation_id, json.dumps(messages)))
        conn.commit()
    else:
        messages = json.loads(row[0])

    user_message = {"role": "user", "content": prompt}
    messages.append(user_message)

    response = openai.ChatCompletion.create(
        model="gpt-4-0314",
        messages=messages,
        max_tokens=110
    )

    assistant_message = response.choices[0].message['content'].strip()
    messages.append({"role": "assistant", "content": assistant_message})

    messages = messages[-10:]
    c.execute(f"UPDATE {table_name} SET messages=? WHERE conversation_id=?", (json.dumps(messages), conversation_id))
    conn.commit()

    return assistant_message

def get_messages_for_conversation(conversation_id, user_id):
    table_name = f"user_{user_id}_history"
    c.execute(f"SELECT messages FROM {table_name} WHERE conversation_id=?", (conversation_id,))
    row = c.fetchone()
    if row is None:
        return None
    else:
        return json.loads(row[0])

@bot.command(name='history')
async def history_command(ctx):
    conversation_id = f"{ctx.guild.id}-{ctx.channel.id}"
    user_id = ctx.author.id
    messages = get_messages_for_conversation(conversation_id, user_id)
    if messages is None:
        await ctx.send("No conversation history available.")
    else:
        history_text = ""
        for message in messages:
            role = message['role'].capitalize()
            content = message['content']
            history_text += f"{role}: {content}\n\n"
        await ctx.send(history_text)


@bot.command(name='gpt4')
async def gpt4_command(ctx, *, prompt: str):
    conversation_id = f"{ctx.guild.id}-{ctx.channel.id}"
    user_id = ctx.author.id
    create_user_table(user_id)
    try:
        response = await generate_openai_response(prompt, conversation_id, user_id)
        if response.strip():
            await ctx.send(response)
        else:
            await ctx.send("I'm sorry, I couldn't generate a response.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

@bot.command(name='test_weather')
async def test_weather_command(ctx, lat: float, lon: float):
    weather_data = test_openweather_api(lat, lon)
    if weather_data is not None:
        description = weather_data['weather'][0]['description']
        temp = weather_data['main']['temp']
        response = f"The weather at coordinates ({lat}, {lon}) is {description} with a temperature of {temp}°C."
    else:
        response = "Error: Unable to fetch weather data."

    await ctx.send(response)

async def handle_image_generation(message, prompt):
    if prompt.lower().startswith("imagine "):
        image_prompt = prompt[8:].strip()
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
    elif prompt.lower().startswith("stable imagine "):
        image_prompt = prompt[15:].strip()
        try:
            generating_message = await message.reply("Generating image, please wait...")
            image_data = await generate_stability_image(image_prompt)
            if image_data:
                await generating_message.delete()
                await message.channel.send(file=discord.File(image_data, "generated_image.png"))
            else:
                await generating_message.edit(content="I'm sorry, I couldn't generate an image.")
        except Exception as e:
            await generating_message.edit(content=f"Error: {str(e)}")

async def send_image_url_as_image(message, image_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            image_data = BytesIO(await response.read())
    await message.channel.send(file=discord.File(image_data, "generated_image.png"), reference=message)

def generate_image(prompt, n=1, size='1024x1024'):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai.api_key}'
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

    # Ignore messages starting with the bot's command prefix
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    if bot.user.mentioned_in(message) and message.mention_everyone is False:
        prompt = re.sub(f"<@!?{bot.user.id}>", "", message.content).strip()
        conversation_id = f"{message.guild.id}-{message.channel.id}"
        user_id = message.author.id
        create_user_table(user_id)

        if 'weather' in prompt.lower():
            location = prompt.replace('weather', '').strip()
            print(f"DEBUG: Location: {location}")  # Debug information
            location_details = get_location_details(location)
            if location_details:
                address, lat, lng = location_details
                weather_data = get_weather_data(lat, lng)
                description = weather_data['weather'][0]['description']
                temp = weather_data['main']['temp']
                response = f"The weather in {address} is {description} with a temperature of {temp}°C."
            else:
                response = "I'm sorry, I couldn't find the location you're looking for."

            await message.channel.send(response)
            return

        if prompt.lower().startswith("imagine ") or prompt.lower().startswith("stable imagine "):
            async with message.channel.typing():
                await handle_image_generation(message, prompt)
        else:
            try:
                async with message.channel.typing():
                    response = await generate_openai_response(prompt, conversation_id, user_id)
                if response.strip():
                    await message.channel.send(response)
                else:
                    await message.channel.send("I'm sorry, I couldn't generate a response.")
            except Exception as e:
                await message.channel.send(f"Error: {str(e)}")

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)