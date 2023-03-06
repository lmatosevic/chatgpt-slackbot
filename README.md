# ChatGPT Slack integration

> ChatGPT API and Slack bot integration service

## Requirements

* Python >= 3.8.0
* Slack app and bot tokens
* OpenAI account and valid API key

### Slack permissions

These are required permissions for your Slack App:

* app_mentions:read
* channels:history
* channels:read
* chat:write
* files:read
* files:write
* im:history

### Slack events

These are required events for your Slack App:

* app_mention
* message.im

## Configuration

All configurable environment variables for ChatGPT can be found in [.env.example](.env.example) file:

| Variable name      | Description                                                                    | Default value                                              |
|--------------------|--------------------------------------------------------------------------------|------------------------------------------------------------|
| SLACK_BOT_TOKEN    | Slack Bot token used to send messages and listen to events (starts with xoxb-) | -                                                          |
| SLACK_APP_TOKEN    | Slack App token used to interact with your workspace (starts with xapp-)       | -                                                          |
| OPENAI_API_KEY     | OpenAI API key used to send request (starts with sk-)                          | -                                                          |
| GPT_MODEL          | GPT model used for chat completion                                             | gpt-3.5-turbo                                              |
| GPT_SYSTEM_DESC    | The description for the system on how to best tailor answers                   | You are a very direct and straight-to-the-point assistant. |
| GPT_IMAGE_SIZE     | The generated image size (256x256, 512x512 or 1024x1024)                       | 512x512                                                    |
| HISTORY_EXPIRES_IN | Number of seconds to keep message history for the same channel as a context    | 900                                                        |

## Install & start

```sh
pip install -r requirements.txt

python main.py
```

## License

ChatGPT-Slackbot is [MIT licensed](LICENSE).