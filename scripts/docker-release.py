import os

from _info import __version__, __name__, __registry__

os.system(f'docker push {__registry__}/{__name__}:{__version__}')
os.system(f'docker push {__registry__}/{__name__}:latest')
