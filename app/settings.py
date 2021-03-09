
from pydantic.tools import lru_cache

import config


@lru_cache()
def get_settings():
    return config.SettingsApp()
