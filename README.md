# ChatGPT Slack integration

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

![alt text](https://raw.githubusercontent.com/lmatosevic/chatgpt-slackbot/master/resources/chatgpt-slackbot-conversation.png)

### Conversation in thread

![alt text](https://raw.githubusercontent.com/lmatosevic/chatgpt-slackbot/master/resources/chatgpt-slackbot-thread.png)

### Generate images

![alt text](https://raw.githubusercontent.com/lmatosevic/chatgpt-slackbot/master/resources/chatgpt-slackbot-image.png)

## Recommendations

### ChatGPT-Cli

If you want to use the power of ChatGPT as a command-line tool, you should check out my other project which
allows interaction with ChatGPT using terminal: https://github.com/lmatosevic/chatgpt-cli

## License

ChatGPT-Slackbot is [MIT licensed](LICENSE).