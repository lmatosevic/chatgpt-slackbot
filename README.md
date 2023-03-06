# ChatGPT Slack integration

> ChatGPT API and Slack bot integration service

## Requirements

* Python >= 3.8.0
* Slack app and bot tokens
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
| SLACK_BOT_TOKEN    | Slack Bot token used to send messages and listen to events (starts with xoxb-)     | -                                                          |
| SLACK_APP_TOKEN    | Slack App token used to interact with your workspace (starts with xapp-)           | -                                                          |
| OPENAI_API_KEY     | OpenAI API key used to send request (starts with sk-)                              | -                                                          |
| GPT_MODEL          | GPT model used for chat completion                                                 | gpt-3.5-turbo                                              |
| GPT_SYSTEM_DESC    | The description for the system on how to best tailor answers (disable with "None") | You are a very direct and straight-to-the-point assistant. |
| GPT_IMAGE_SIZE     | The generated image size (256x256, 512x512 or 1024x1024)                           | 512x512                                                    |
| HISTORY_EXPIRES_IN | Number of seconds to keep message history for the same channel as a context        | 900                                                        |

## Install & start

```sh
pip install -r requirements.txt

python main.py
```

## License

ChatGPT-Slackbot is [MIT licensed](LICENSE).