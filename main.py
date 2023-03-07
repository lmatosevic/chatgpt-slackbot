import os
import random
import sys
from datetime import datetime, timedelta
from typing import Optional
from urllib.request import urlopen

import openai
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from _version import __version__


def valid_input(value: Optional[str]) -> bool:
    return value is not None and value.strip() != ''


def get_env(key: str, default: Optional[str]) -> str:
    value = os.getenv(key, default)
    if not valid_input(value):
        value = default
    return value


def log(content: str, error: bool = False):
    now = datetime.now()
    print(f'[{now.isoformat()}] {content}', flush=True, file=sys.stderr if error else sys.stdout)


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

# Keep timestamps of last requests per channel
last_request_datetime = {}


# Activated when the bot is tagged in a channel
@app.event('app_mention')
def handle_mention_events(body):
    prompt = str(str(body['event']['text']).split('>')[1]).strip()
    channel = body['event']['channel']
    thread_ts = body['event']['thread_ts'] if 'thread_ts' in body['event'] else None
    handle_prompt(prompt, channel, thread_ts)


# Activated when bot receives direct message
@app.event('message')
def handle_message_events(body):
    prompt = str(body['event']['text']).strip()
    user = body['event']['user']
    thread_ts = body['event']['thread_ts'] if 'thread_ts' in body['event'] else None
    handle_prompt(prompt, user, thread_ts, True)


def handle_prompt(prompt, channel, thread_ts=None, direct_message=False):
    # Log requested prompt
    log(f'Channel {channel} received message: {prompt}')

    # Initialize the last request datetime for this channel
    if channel not in last_request_datetime:
        last_request_datetime[channel] = datetime.fromtimestamp(0)

    # Let the user know that we are busy with the request if enough time has passed since last message
    if last_request_datetime[channel] + timedelta(seconds=history_expires_seconds) < datetime.now():
        client.chat_postMessage(channel=channel,
                                thread_ts=thread_ts,
                                text=random.choice([
                                    'Generating... :gear:',
                                    'Multiplying matrices :abacus:',
                                    'Beep beep boop :robot_face:'
                                ]))

    # Set current timestamp
    last_request_datetime[channel] = datetime.now()

    # Read parent message content if called inside thread conversation
    parent_message_text = None
    if thread_ts and not direct_message:
        conversation = client.conversations_replies(channel=channel, ts=thread_ts)
        if len(conversation['messages']) > 0 and valid_input(conversation['messages'][0]['text']):
            parent_message_text = conversation['messages'][0]['text']

    # Handle empty prompt
    if len(prompt.strip()) == 0 and parent_message_text is None:
        log('Empty prompt received')
        return

    if prompt.lower().startswith('image:'):
        # Generate DALL-E image command based on the prompt
        image_prompt = prompt[6:].strip()

        # Append parent message text as prefix if exists
        if parent_message_text:
            image_prompt = f'{parent_message_text}. {image_prompt}'
            log('Using parent message inside thread')

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

            if direct_message:
                # Send image URL as a message
                client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=image_url)
                text = image_url
            else:
                try:
                    # Upload image to Slack and send message with image to channel
                    upload_response = client.files_upload_v2(
                        channel=channel,
                        thread_ts=thread_ts,
                        title=image_prompt,
                        filename=image_name,
                        file=image_path
                    )

                    # Set text vairable for logging purposes only
                    text = upload_response['file']['url_private']
                except SlackApiError as e:
                    text = None
                    log(f'Error from Slack API: {e}', True)

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
                if channel_message['created_at'] + timedelta(seconds=history_expires_seconds) < now or \
                        channel_message['thread_ts'] != thread_ts or parent_message_text == channel_message['content']:
                    continue
                history_messages.append({'role': channel_message['role'], 'content': channel_message['content']})
        else:
            chat_history[channel] = []

        # Log used history messages count
        log(f'Using {len(history_messages)} messages from chat history')

        # Append parent text message from current thread
        if parent_message_text:
            history_messages.append({'role': 'user', 'content': parent_message_text})
            log(f'Adding parent message from thread with timestamp: {thread_ts}')

        # Combine messages from history, current prompt and system if not disabled
        messages = [
            *history_messages,
            {'role': 'user', 'content': prompt}
        ]
        if system_desc.lower() != 'none':
            messages.insert(0, {'role': 'system', 'content': system_desc})

        # Send request to ChatGPT
        response = openai.ChatCompletion.create(model=model, messages=messages)

        # Prepare response text
        text = response.choices[0].message.content.strip('\n')

        # Add messages to history
        chat_history[channel].append({'role': 'user', 'content': prompt, 'created_at': now, 'thread_ts': thread_ts})
        chat_history[channel].append(
            {'role': 'assistant', 'content': text, 'created_at': datetime.now(), 'thread_ts': thread_ts})

        # Remove the oldest history message if there are more than 4 messages in channel history for current thread
        if len(list(filter(lambda x: x['thread_ts'] == thread_ts, chat_history[channel]))) > 4:
            first_occurance = next(msg for msg in chat_history[channel] if msg['thread_ts'] == thread_ts)
            if first_occurance:
                chat_history[channel].remove(first_occurance)

        # Reply answer to thread
        client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=text)

    # Log response text
    log(f'ChatGPT response: {text}')


if __name__ == '__main__':
    try:
        print(f'ChatGPT Slackbot version {__version__}')
        SocketModeHandler(app, SLACK_APP_TOKEN).start()
    except KeyboardInterrupt:
        log('Stopping server')
