![vector header image, simple, with robot and multivac tube connotations, dark backgroun2d](https://i.imgur.com/Ruo7oC1.png)

# Multivac
A python Discord bot powered by GPT4 to provide natural language conversations, responses, and image generation, while interacting with other API services.
If you'd like to use this bot for other models, you should be able to change that in the "model="gpt-4", replace "gpt-4" with "gpt-3.5-turbo" or "text-davinci-002" for example. You can also adjust the max_tokens found under that to increase prompt and completion length.

Help fund the API costs by supporting me on https://ko-fi.com/sardistic 🍵🤖


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


**Update Summary: Added multivacv2.py**

1. Enhanced reply functionality: The bot now replies directly to the user who initiated the prompt, providing a more conversational experience.
2. Improved image generation response: The bot now sends a "Generating image, please wait..." message before generating the image. Once the image is generated, the initial message is deleted, and the bot replies with the generated image.
3. Added support for bot image generation using Dalle: The bot now responds to image generation requests if it's mentioned after the word "imagine" is used at the begining of the prompt(e.g., "imagine a beautiful sunset @Bot").
4. Removed weather functions for this script temporarily.

These updates enhance the bot's user experience by providing more intuitive replies, better messaging during image generation, and support for image generation using Dalle.
