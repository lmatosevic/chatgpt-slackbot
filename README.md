# ChatGPT Slack integration

![docker](https://img.shields.io/docker/v/lukamatosevic/chatgpt-slackbot)
![License](https://img.shields.io/github/license/lmatosevic/chatgpt-slackbot)
![build](https://img.shields.io/badge/build-passing-brightgreen)

> Slack bot service for seamless ChatGPT integration

## Requirements

* Python >= 3.8.0
* Slack App and Bot tokens
* OpenAI account and valid API key

### OpenAI

In order to generate OpenAI API key, you will first need to register and create an API key (if you haven't done already)
on the [official OpenAI website](https://platform.openai.com/account/api-keys).

### Slack

You can find more information how to create and configure Slack app, events, permissions and generate tokens on
the [official Slack documentation](https://api.slack.com/authentication/basics).

### Slack permissions

These are required permissions for your Slack App:

* app_mentions:read
* channels:history
* channels:read
* chat:write
* files:read
* files:write
* groups:history
* im:history
* mpim:history

### Slack events

These are required events for your Slack App:

* app_mention
* message.im

## Configuration

All configurable environment variables can be found in [.env.example](.env.example) file:

| Variable name      | Description                                                                        | Default value                                              |
|--------------------|------------------------------------------------------------------------------------|------------------------------------------------------------|
| *SLACK_BOT_TOKEN   | Slack Bot token used to send messages and listen to events (starts with xoxb-)     | -                                                          |
| *SLACK_APP_TOKEN   | Slack App token used to interact with your workspace (starts with xapp-)           | -                                                          |
| *OPENAI_API_KEY    | OpenAI API key used to send request (starts with sk-)                              | -                                                          |
| GPT_MODEL          | GPT model used for chat completion                                                 | gpt-3.5-turbo                                              |
| GPT_SYSTEM_DESC    | The description for the system on how to best tailor answers (disable with "None") | You are a very direct and straight-to-the-point assistant. |
| GPT_IMAGE_SIZE     | The generated image size (256x256, 512x512 or 1024x1024)                           | 512x512                                                    |
| HISTORY_EXPIRES_IN | Number of seconds to keep message history for the same channel as a context        | 900                                                        |
| HISTORY_SIZE       | Number of last messages to keep in history as a context for the next question      | 3                                                          |

_Variables with * prefix are mandatory for running this service_

## Install & start

First you should copy [.env.example](.env.example) file into new .env file, and fill Slack tokens and OpenAI API key.

(optional) You should create a new python virtual environment for this project. Run following command from the root
of this project using python version 3.8 or greater:

```sh
python -m venv ./.venv
```

Activate virtual environment by running one of the following scripts:

```sh
# linux
./.venv/bin/activate

# windows
./.venv/Scripts/activate
```

Then you can install python requirements by running following command:

```sh
pip install -r requirements.txt
```

Finally, you can start the Slack chatbot service:

```sh
python main.py
```

## Docker support

This service has full docker support with provided by [Dockerfile](Dockerfile).

The easiest way to pull & run docker image is to use already built public image
from [official DockerHub repository](https://hub.docker.com/repository/docker/lukamatosevic/chatgpt-slackbot):

```sh
docker pull lukamatosevic/chatgpt-slackbot:latest

docker run --env-file .env lukamatosevic/chatgpt-slackbot
```

Or, you can build the image yourself with docker command:

```sh
docker image build --rm -t chatgpt-slackbot .
```

Then you can start the chatbot service with any of the following commands:

```sh
# provide .env file with configured tokens and api key
docker run --env-file .env chatgpt-slackbot

# also, you can set required environment variables as parameters
docker run --env "SLACK_BOT_TOKEN=xoxb-..." \
           --env "SLACK_APP_TOKEN=xapp-..." \
           --env "OPENAI_API_KEY=sk-..." chatgpt-slackbot
```

## Examples

### Conversation

This example shows a conversation with ChatGPT Slack app. You can start conversation directly with ChatGPT by sending it
a private message, or you can add it to any channel or group conversation. If you are speaking to the ChatGPT directly,
you don't need to mention it by **@ChatGPT**.

The conversation will keep a specified number of messages in history (default: 3) for some time (default: 15 minutes)
which are used as context when ChatGPT is generating new responses in the same thread and channel / private / group
chat.

![alt text](https://github.com/lmatosevic/chatgpt-slackbot/blob/main/resources/chatgpt-slackbot-conversation.png?raw=true)

### Conversation in thread

Here is shown the possible use case for asking ChatGPT to answer or do something with the parent message in a thread.

![alt text](https://github.com/lmatosevic/chatgpt-slackbot/blob/main/resources/chatgpt-slackbot-thread.png?raw=true)

### Generate images

You can also ask ChatGPT to generate images by starting the message with `image:` prefix. You can also use this in a
thread where the parent message will be added to the context when prompting the DALL-E 2 OpenAI API endpoint.

![alt text](https://github.com/lmatosevic/chatgpt-slackbot/blob/main/resources/chatgpt-slackbot-image.png?raw=true)

## Recommendations

### ChatGPT-Cli

If you want to use the power of ChatGPT as a command-line tool, you should check out my other project which
allows interaction with ChatGPT using terminal: https://github.com/lmatosevic/chatgpt-cli

## License

ChatGPT-Slackbot is [MIT licensed](LICENSE).