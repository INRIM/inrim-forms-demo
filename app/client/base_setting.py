import sys
sys.path.append("..")
from fastapi.templating import Jinja2Templates
from settings import get_settings

templates = Jinja2Templates(directory="themes")
