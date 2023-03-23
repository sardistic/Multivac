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
import spacy

nlp = spacy.load("en_core_web_lg")
logging.basicConfig(level=logging.DEBUG)

DISCORD_TOKEN = ''
OPENAI_API_KEY = ''
OPENWEATHER_API_KEY = ''

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

def preprocess_weather_message(text):
    text = text.replace("whats the", "").strip()
    text = text.replace("what's the", "").strip()
    text = text.replace("tell me", "").strip()
    text = text.replace("find", "").strip()
    text = text.replace("search", "").strip()
    text = text.replace("right now", "").strip()
    return text


def openai_response(prompt, conversation_id):
    if conversation_id not in conversation_history:
        conversation_history[conversation_id] = [
            {"role": "system", "content": "You are a helpful and accept any persona you are asked to be. Keep responses to 200 words or less"}
        ]

    user_message = {"role": "user", "content": prompt}
    conversation_history[conversation_id].append(user_message)

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=conversation_history[conversation_id],
        max_tokens=100
    )

    assistant_message = response.choices[0].message['content'].strip()
    conversation_history[conversation_id].append({"role": "assistant", "content": assistant_message})

    conversation_history[conversation_id] = conversation_history[conversation_id][-10:]

    return assistant_message

def extract_location(text):
    print(f"Original text: {text}")
    doc = nlp(text)
    city = None
    for ent in doc.ents:
        if ent.label_ == "GPE":
            print(f"Extracted city: {ent.text}")
            city = ent.text
    if not city:
        city_pattern = re.compile(r'weather in (.*?)(?:\b(?:right|now)\b)*\s*$', re.IGNORECASE)
        match = city_pattern.search(text)
        if match:
            city = match.group(1).strip()
            print(f"Extracted city using regex: {city}")
    return city

def generate_image(prompt, n=1, size='1024x1024'):
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

def get_weather(city):
    if ',' not in city:
        city = city.replace(' ', ',')
    if len(city.split(',')) < 2:
        city += ',US'

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather = data['weather'][0]['description']
        temp = data['main']['temp']
        return weather, temp
    else:
        return "I'm sorry, I couldn't fetch the weather data."
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message) and message.mention_everyone is False:
        prompt = message.content.replace(f"<@!{bot.user.id}>", "").strip()
        conversation_id = f"{message.guild.id}-{message.channel.id}"
        
        if "weather" in prompt.lower():
            preprocessed_prompt = preprocess_weather_message(prompt)
            city = extract_location(preprocessed_prompt)
            if city:
                weather, temp = get_weather(city)
                # Generate a natural language response using GPT-3
                weather_prompt = f"The current weather in {city} is {weather} with a temperature of {temp}°C. Can you provide a more natural response?"
                weather_response = await generate_openai_response(weather_prompt, conversation_id)
                await message.channel.send(weather_response)
            else:
                await message.channel.send("Please provide a city name after the word 'weather'.")
        else:
            try:
                response = await generate_openai_response(prompt, conversation_id)
                if response.strip():
                    await message.channel.send(response)
                else:
                    await message.channel.send("I'm sorry, I couldn't generate a response.")
            except Exception as e:
                await message.channel.send(f"Error: {str(e)}")

    await bot.process_commands(message)
bot.run(DISCORD_TOKEN)