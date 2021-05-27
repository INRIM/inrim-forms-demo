from typing import Optional

from pydantic import BaseSettings, PrivateAttr
import logging
import os

file_dir = os.path.split(os.path.realpath(__file__))[0]

logging.config.fileConfig(os.path.join(file_dir, 'logging.conf'), disable_existing_loggers=False)


class Settings(BaseSettings):
    app_name: str = "Awesome API"
    app_desc: str = ""
    app_version: str = ""
    base_url_ws: str = ""
    camunda_url: str = ""
    app_process: str = ""
    jwt_secret: str = ""
    jwt_alg: str = "HS256"
    jwt_expire_minute: Optional[int] = None
    _jwt_settings: dict = PrivateAttr()
    default_dn: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._jwt_settings = {
            "secret": self.jwt_secret,
            "alg": self.jwt_alg,
            "expire_minute": self.jwt_expire_minute,
        }

    class Config:
        env_file = ".env"


class SettingsApp(Settings):
    people_headerkey: str = ""
    people_url: str = ""
    people_key: str = ""
    ui_builder_url: str = ""
    ui_builder_key: str = ""
    data_builder_url: str = ""
    data_builder_key: str = ""
    data_builder_headerkey: str = ""
    mongo_url: str = ""
    mongo_user: str = ""
    mongo_pass: str = ""
    mongo_db: str = ""
    mongo_replica: str = ""
    server_datetime_mask: str = ""
    server_date_mask = ""
    ui_datetime_mask: str = ""
    ui_date_mask = ""
    time_zone: str = ""
    logo_img_url: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.mongo_replica == "":
            self.mongo_replica = None

    def get_service_dict(self, service_name):
        res = {}
        data = self.dict()
        for item in self.dict():
            if service_name in item:
                key = item.split("_")[1]
                res[key] = data[item]
        return res
