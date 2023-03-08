import os

from _info import __version__, __name__, __registry__

os.system(f'docker image build --rm -t {__registry__}/{__name__}:{__version__} -t {__registry__}/{__name__}:latest .')
