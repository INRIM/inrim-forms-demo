from fastapi import HTTPException
from jose import jwt
import requests
from requests import Response

from libs.services.PeopleApi import People
from models import *
from libs.camundapy.process_form_service_base import *
from config import *

logger = logging.getLogger(__name__)


class ProcessService(ProcessServicBase):

    def __init__(self, auth: Auth, camunda_dest_url: str, settings: SettingsApp):
        super().__init__(camunda_dest_url, auth_header=auth._token)
        self.settings = settings.copy()
        self.people = None

    def curr_task_get_form_vars(self, instance_id: str) -> dict:
        variables = super().curr_task_get_form_vars(instance_id)
        return variables
