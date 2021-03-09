import logging
import os
import string
import time
import uuid
from functools import lru_cache
import requests

from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.responses import HTMLResponse

from services import *
from models import *
from datetime import *
import time as time_
from settings import get_settings
from libs.services.utils_for_service import *

from fastapi.staticfiles import StaticFiles

from client.client_api import client_api
from client.builder_api import builder_api

logger = logging.getLogger(__name__)

tags_metadata = [
    {
        "name": ":-)",
        "description": "Forms Inrim",
    },
    {
        "name": "base",
        "description": "API Base",
    },
]

responses = {
    401: {
        "description": "Token non valido",
        "content": {"application/json": {"example": {"detail": "Auth invalid"}}}},
    422: {
        "description": "Dati richiesta non corretti",
        "content": {"application/json": {"example": {"detail": "err messsage"}}}}
}

app = FastAPI(
    title=get_settings().app_name,
    description=get_settings().app_desc,
    version="1.0.0",
    openapi_tags=tags_metadata,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.mount("/client", client_api)
app.mount("/builder", builder_api)
app.mount("/static", StaticFiles(directory="themes/italia/static"), name="static")


def check_token_get_auth(token: str) -> Auth:
    if not token:
        raise HTTPException(status_code=401, detail="Auth invalid")
    logger.info("check_token_get_auth")
    utils = UtilsForService()
    jwt_settings = get_settings()._jwt_settings
    data = utils.decode_token(token, jwt_settings)
    if "username" in data and "password" in data:
        auth = Auth(username=data['username'], password=data['password'], base_url_ws=get_settings().base_url_ws)
        return auth
    else:
        logger.error("jwt string invalid")
        raise HTTPException(status_code=401, detail="Auth invalid")


def check_response_data(res_data: dict) -> dict:
    if res_data.get("status") and res_data.get("status") == "error":
        raise HTTPException(status_code=422, detail=res_data['message'])
    else:
        return res_data


@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = str(uuid.uuid4())
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time_.time()

    response = await call_next(request)
    process_time = (time_.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response


@app.get("/", tags=["base"])
async def service_status():
    """
    Ritorna lo stato del servizio
    """
    return {"status": "live"}


@app.post(
    "/genera-token",
    responses=responses,
    tags=["base"])
async def genera_token(tokendata: Token):
    """
    Genera un token JWT
    """
    utils = UtilsForService()
    token_str = utils.create_token(tokendata.dict())

    return {"token": token_str}


@app.get("/test/{id}", response_class=HTMLResponse)
async def read_test(request: Request, id: str):
    return templates.TemplateResponse("item.html", {"request": request, "id": id})
