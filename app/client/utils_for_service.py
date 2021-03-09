from requests import Response
from jose import JWTError, jwt
from datetime import date, datetime, time, timedelta
import logging

logger = logging.getLogger(__name__)


class UtilsForService:

    def _finditem(self, obj, key):
        if key in obj: return obj[key]
        for k, v in obj.items():
            if isinstance(v, dict):
                item = self._finditem(v, key)
                if item is not None:
                    return item

    def deserialize_list_key_values(self, list_data):
        res = {item['name']: item['value'] for item in list_data}
        return res

    def clean_save_form_data(self, data):
        """
        Clean data dictionary
        :param data:
        :return:
        """
        dat = {}

        dat = {k.replace('_in', '').replace('_tl', '').replace('_ck', '').replace('_sel', ''): True if v == 'on' else v
               for k, v in data.items()}
        return dat

    def log_req_resp(self, req_resp: object):
        logger.info("------")
        logger.info("------")
        logger.info("--LOG RESP---")
        logger.info("..................................")
        logger.info(req_resp)
        logger.info("------")
        logger.info("------")

    def extract_jwt(self, token: str, jwt_settings: dict) -> dict:
        pass

    def create_token(self, data: dict) -> str:
        to_encode = data.copy()
        secret_key = data.pop('secret')
        algorithm = data.pop('alg')
        if "expire_minute" in data:
            if data['expire_minute']:
                data['expire'] = datetime.utcnow() + data['expire_minute']
            else:
                data.pop('expire_minute')
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
        return encoded_jwt

    def create_int_token(self, data: dict, jwt_settings: dict) -> str:
        to_encode = {**data, **jwt_settings}
        return self.create_token(to_encode)

    def decode_token(self, token: str, jwt_settings: dict) -> dict:
        return jwt.decode(token, jwt_settings.get('secret'), algorithms=[jwt_settings.get('alg')])
