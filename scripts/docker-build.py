import os

verstrline = open(f'{os.getcwd()}/_version.py', "rt").readline()
version = verstrline.split('=')[-1].strip().replace('\'', '')

os.system(
    f'docker image build --rm -t lukamatosevic/chatgpt-slackbot:{version} -t lukamatosevic/chatgpt-slackbot:latest .')
