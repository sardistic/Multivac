# Multivac
A python Discord bot powered by GPT4 to provide natural language conversations, responses, and image generation, while interacting with other API services.

>Could you give me a brief description what this script does, like a github readme

Title: Python Discord Weather Bot with GPT-4

Description: A Discord bot, built using Python, discord.py, and OpenAI's GPT-4, that provides weather information in a natural language based on user requests.

Features:
- Responds to weather-related queries with data fetched from OpenWeatherMap API.
- Generates a natural language response using OpenAI's GPT-4 model.
- Extracts the location from the user's query using SpaCy.

Dependencies:
- discord.py
- openai
- asyncio
- spacy
- requests

Usage:
1. Set up a Discord bot and obtain your bot token.
2. Replace `DISCORD_TOKEN` with your Discord bot token.
3. Replace `OPENAI_API_KEY` with your OpenAI API key.
4. Replace `OPENWEATHER_API_KEY` with your OpenWeatherMap API key.
5. Install the required dependencies using `pip install -r requirements.txt`.
6. Run the script using `python weather_bot.py`.

Commands:
Mention the bot with a message containing the word "weather" followed by the city name to get the weather information in a natural language response:

`@bot_user weather in New York`

Example response:

"Currently, in New York, the weather is mostly cloudy with a temperature of 18°C. Make sure to take an umbrella if you're going out, as it might rain later in the day."
