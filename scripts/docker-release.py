import os

verstrline = open(f'{os.getcwd()}/_version.py', "rt").readline()
version = verstrline.split('=')[-1].strip().replace('\'', '')

os.system(f'docker push lukamatosevic/chatgpt-slackbot:{version}')
os.system('docker push lukamatosevic/chatgpt-slackbot:latest')
