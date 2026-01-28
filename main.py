import os
import random
import sys
from datetime import datetime, timedelta
from typing import Optional
from urllib.request import urlopen

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from _info import __version__


def valid_input(value: Optional[str]) -> bool:
    """
    Checks if the provided input value is valid.

    A value is considered valid if it is not None and not just whitespace.

    Args:
        value (Optional[str]): The input value to check.

    Returns:
        bool: True if the input is valid; False otherwise.
    """
    return value is not None and value.strip() != ''


def get_env(key: str, default: Optional[str]) -> str:
    """
    Retrieves an environment variable, returning a default value if not found or invalid.

    Args:
        key (str): The name of the environment variable to retrieve.
        default (Optional[str]): The default value to return if the variable doesn't exist or is invalid.

    Returns:
        str: The value of the environment variable or the default value.
    """
    value = os.getenv(key, default)
    if not valid_input(value):
        value = default
    return value


def log(content: str, error: bool = False):
    """
    Logs a message to the console with a timestamp.

    Args:
        content (str): The content to log.
        error (bool): If True, log to stderr; otherwise, log to stdout.
    """
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
slack_client = WebClient(SLACK_BOT_TOKEN)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ChatGPT configuration
model = get_env('GPT_MODEL', 'gpt-5.1')
reasoning_effort = get_env('GPT_REASONING_EFFORT', 'low')
temperature = float(get_env('GPT_TEMPERATURE', '1.0'))
image_model = get_env('GPT_IMAGE_MODEL', 'dall-e-3')
system_desc = get_env('GPT_SYSTEM_DESC', 'You are a very direct and straight-to-the-point assistant.')
image_size = get_env('GPT_IMAGE_SIZE', '1024x1024')

# Keep chat history to provide context for future prompts
chat_history = {
    'general': []
}
history_expires_seconds = int(get_env('HISTORY_EXPIRES_IN', '900'))  # 15 minutes
history_size = int(get_env('HISTORY_SIZE', '3'))

# Keep timestamps of last requests per channel
last_request_datetime = {}


# Activated when the bot is tagged in a channel
@app.event('app_mention')
def handle_mention_events(body):
    """
    Handles events when the bot is mentioned in a channel.

    This function extracts the prompt from the event and passes it to the handle_prompt function.

    Args:
        body (dict): The event body containing the mention information.
    """
    prompt = str(str(body['event']['text']).split('>')[1]).strip()
    channel = body['event']['channel']
    thread_ts = body['event']['thread_ts'] if 'thread_ts' in body['event'] else None
    handle_prompt(prompt, channel, thread_ts)


# Activated when the bot receives a direct message
@app.event('message')
def handle_message_events(body):
    """
    Handles events when the bot receives a direct message.

    This function extracts the prompt from the event and passes it to the handle_prompt function.

    Args:
        body (dict): The event body containing the message information.
    """
    prompt = str(body['event']['text']).strip()
    user = body['event']['user']
    thread_ts = body['event']['thread_ts'] if 'thread_ts' in body['event'] else None
    handle_prompt(prompt, user, thread_ts, direct_message=True)


def handle_prompt(prompt, channel, thread_ts=None, direct_message=False):
    """
    Processes the incoming prompt, determines if it requires an image generation or a chat response,
    and logs the user request. Sends a response back to the Slack channel or direct message.

    Args:
        prompt (str): The prompt provided by the user.
        channel (str): The channel ID where the prompt was received.
        thread_ts (Optional[str]): The timestamp of the thread if applicable.
        direct_message (bool): Indicates if the prompt was a direct message.
    """
    # Log requested prompt
    log(f'Channel {channel} received message: {prompt}')

    # Initialize the last request datetime for this channel
    if channel not in last_request_datetime:
        last_request_datetime[channel] = datetime.fromtimestamp(0)

    # Let the user know that we are busy with the request if enough time has passed since last message
    if last_request_datetime[channel] + timedelta(seconds=history_expires_seconds) < datetime.now():
        slack_client.chat_postMessage(channel=channel,
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
        conversation = slack_client.conversations_replies(channel=channel, ts=thread_ts)
        if len(conversation['messages']) > 0 and valid_input(conversation['messages'][0]['text']):
            parent_message_text = conversation['messages'][0]['text']

    # Handle empty prompt
    if len(prompt.strip()) == 0 and parent_message_text is None:
        log('Empty prompt received')
        return

    if prompt.lower().startswith('image:'):
        # Generate DALL-E image command based on the prompt
        base_image_prompt = prompt[6:].strip()
        image_prompt = base_image_prompt

        # Append parent message text as prefix if exists
        if parent_message_text:
            image_prompt = f'{parent_message_text}. {image_prompt}'
            log('Using parent message inside thread')

        if len(image_prompt) == 0:
            text = 'Please check your input. To generate image use this format -> image: robot walking a dog'
        else:
            # Generate image based on prompt text
            try:
                response = openai_client.images.generate(model=image_model, prompt=image_prompt, n=1, size=image_size)
            except OpenAIError as e:
                log(f'ChatGPT image error: {e}', error=True)
                # Reply with an error message
                slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=str(e))
                return

            image_url = response.data[0].url

            if direct_message:
                # Send image URL as a message
                slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=image_url)
                text = image_url
            else:
                image_path = None
                try:
                    # Read image from URL
                    image_content = urlopen(image_url).read()

                    # Prepare image name and path
                    short_prompt = base_image_prompt if valid_input(base_image_prompt) else image_prompt[:30].strip()
                    image_name = f"{short_prompt.replace(' ', '_')}.png"
                    image_path = f'./tmp/{image_name}'

                    # Write a file in the temp directory
                    image_file = open(image_path, 'wb')
                    image_file.write(image_content)
                    image_file.close()

                    # Upload an image to Slack and send a message with image to channel
                    upload_response = slack_client.files_upload_v2(
                        channel=channel,
                        thread_ts=thread_ts,
                        title=short_prompt,
                        filename=image_name,
                        file=image_path
                    )

                    # Set text variable for logging purposes only
                    text = upload_response['file']['url_private']
                except SlackApiError as e:
                    text = None
                    log(f'Slack API error: {e}', error=True)

                # Remove temp image
                if image_path and os.path.exists(image_path):
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
        try:
            params = {
                'model': model,
                'messages': messages,
                'temperature': temperature
            }
            if 'o1' in model or 'o3' in model:
                params['reasoning_effort'] = reasoning_effort
                # O-series models don't support temperature, or it must be 1
                if 'temperature' in params:
                    del params['temperature']

            response = openai_client.chat.completions.create(**params)
        except OpenAIError as e:
            log(f'ChatGPT response error: {e}', error=True)
            # Reply with an error message
            slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=str(e))
            return

        # Prepare response text
        text = response.choices[0].message.content.strip('\n')

        # Add messages to history
        chat_history[channel].append({'role': 'user', 'content': prompt, 'created_at': now, 'thread_ts': thread_ts})
        chat_history[channel].append(
            {'role': 'assistant', 'content': text, 'created_at': datetime.now(), 'thread_ts': thread_ts})

        # Remove the oldest 2 history messages if the channel history size is exceeded for the current thread
        if len(list(filter(lambda x: x['thread_ts'] == thread_ts, chat_history[channel]))) >= (history_size + 1) * 2:
            # Create iterator for chat history list
            chat_history_list = (msg for msg in chat_history[channel] if msg['thread_ts'] == thread_ts)
            first_occurance = next(chat_history_list, None)
            second_occurance = next(chat_history_list, None)

            # Remove the first occurrence
            if first_occurance:
                chat_history[channel].remove(first_occurance)

            # Remove the second occurrence
            if second_occurance:
                chat_history[channel].remove(second_occurance)

        # Reply answer to thread
        slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=text)

    # Log response text
    log(f'ChatGPT response: {text}')


if __name__ == '__main__':
    try:
        print(f'ChatGPT Slackbot version {__version__}')
        SocketModeHandler(app, SLACK_APP_TOKEN).start()
    except KeyboardInterrupt:
        log('Stopping server')
