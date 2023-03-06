import os
import random
from datetime import datetime, timedelta
from typing import Optional
from urllib.request import urlopen

import openai
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def valid_input(value: Optional[str]) -> bool:
    return value is not None and value.strip() != ''


def get_env(key: str, default: Optional[str]) -> str:
    value = os.getenv(key, default)
    if not valid_input(value):
        value = default
    return value


def log(content: str):
    now = datetime.now()
    print(f'[{now.isoformat()}] {content}', flush=True)


# Load environment variables
load_dotenv()

# Integration tokens and keys
SLACK_BOT_TOKEN = get_env('SLACK_BOT_TOKEN', None)
SLACK_APP_TOKEN = get_env('SLACK_APP_TOKEN', None)
OPENAI_API_KEY = get_env('OPENAI_API_KEY', None)

# Event API, Web API and OpenAI API
app = App(token=SLACK_BOT_TOKEN)
client = WebClient(SLACK_BOT_TOKEN)
openai.api_key = OPENAI_API_KEY

# ChatGPT configuration
model = get_env('GPT_MODEL', 'gpt-3.5-turbo')
system_desc = get_env('GPT_SYSTEM_DESC', 'You are a very direct and straight-to-the-point assistant.')
image_size = get_env('GPT_IMAGE_SIZE', '512x512')

# Keep chat history to provide context for furute prompts
chat_history = {
    'general': []
}
history_expires_seconds = int(get_env('HISTORY_EXPIRES_IN', '900'))  # 15 minutes


# Activated when the bot is tagged in a channel
@app.event('app_mention')
def handle_mention_events(body):
    prompt = str(str(body['event']['text']).split('>')[1]).strip()
    channel = body['event']['channel']
    handle_prompt(prompt, channel)


# Activated when bot receives direct message
@app.event('message')
def handle_message_events(body):
    prompt = str(body['event']['text']).strip()
    user = body['event']['user']
    handle_prompt(prompt, user)


def handle_prompt(prompt, channel):
    # Log requested prompt
    log(f'Channel {channel} received message: ' + prompt)

    # Let the user know that we are busy with the request 
    client.chat_postMessage(channel=channel,
                            text=random.choice([
                                'Generating... :gear:',
                                'Multiplying matrices :abacus:',
                                'Yessir :saluting_face:',
                                'Beep beep boop :robot_face:',
                                'Death to the machines! :skull:',
                                'Anything for you :unicorn_face:',
                                'Here you go :rainbow:'
                            ]))

    if prompt.lower().startswith('image:'):
        # Generate DALL-E image command based on the prompt
        image_prompt = prompt[6:].strip()
        if len(image_prompt) == 0:
            text = 'Please check your input. To generate image use this format -> image: robot walking a dog'
        else:
            response = openai.Image.create(prompt=image_prompt, n=1, size=image_size)
            image_url = response.data[0].url

            # Read image from URL
            image_content = urlopen(image_url).read()

            image_name = f'{image_prompt}.png'
            image_path = f'./tmp/{image_name}'

            # Write file in temp directory
            image_file = open(image_path, 'wb')
            image_file.write(image_content)
            image_file.close()

            # Upload image to Slack and send response message to channel
            try:
                upload_response = client.files_upload_v2(
                    channel=channel,
                    title=image_prompt,
                    filename=image_name,
                    file=image_path
                )

                # Set text vairable for logging purposes only
                text = upload_response['file']['url_private']
            except SlackApiError:
                text = image_url
                client.chat_postMessage(channel=channel, text=image_url)

            # Remove temp image
            if os.path.exists(image_path):
                os.remove(image_path)
    else:
        # Generate chat response
        now = datetime.now()

        # Add history messages if not expired
        history_messages = []
        if channel in chat_history:
            for channel_message in chat_history[channel]:
                if channel_message['created_at'] + timedelta(seconds=history_expires_seconds) < now:
                    continue
                history_messages.append({'role': channel_message['role'], 'content': channel_message['content']})
        else:
            chat_history[channel] = []

        # Log history messages count
        log(f'Using {str(len(history_messages))} history messages')

        # Combine messages from system, history and current prompt
        messages = [
            {'role': 'system', 'content': system_desc},
            *history_messages,
            {'role': 'user', 'content': prompt}
        ]

        # Send request to ChatGPT
        response = openai.ChatCompletion.create(model=model, messages=messages)

        # Prepare response text
        text = response.choices[0].message.content.strip('\n')

        # Add messages to history
        chat_history[channel].append({'role': 'user', 'content': prompt, 'created_at': now})
        chat_history[channel].append({'role': 'assistant', 'content': text, 'created_at': datetime.now()})
        if len(chat_history[channel]) > 4:
            chat_history[channel].pop(0)

        # Reply answer to thread
        client.chat_postMessage(channel=channel, text=text)

    # Log response text
    log('ChatGPT response: ' + text)


if __name__ == '__main__':
    try:
        SocketModeHandler(app, SLACK_APP_TOKEN).start()
    except KeyboardInterrupt:
        print('Stopping server')
