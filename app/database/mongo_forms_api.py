import sys

sys.path.append("..")
from fastapi import FastAPI, Request, Header, HTTPException, Depends
from libs.services.utils_for_service import UtilsForService
from libs.services.utils_for_service import *
from .mongo_forms import *
from .models import *

mongoform_api = FastAPI()

def check_token_get_auth(token: str):
    logger.info("check_token_get_auth")
    return ""
    # if not token:
    #     raise HTTPException(status_code=401, detail="Auth invalid")

    # utils = UtilsForService()
    # jwt_settings = get_settings()._jwt_settings
    # data = utils.decode_token(token, jwt_settings)
    # if "username" in data and "password" in data:
    #     return auth
    # else:
    #     logger.error("jwt string invalid")
    #     raise HTTPException(status_code=401, detail="Auth invalid")

def check_response_data(res_data: dict) -> dict:
    if isinstance(res_data, dict) and res_data.get("status") and res_data.get("status") == "error":
        raise HTTPException(status_code=422, detail=res_data['message'])
    else:
        return res_data


@mongoform_api.get("/", response_model=ListForm, tags=["inrim-forms"])
async def mongo_forms(
        form_type: str,
        skip: int = 0,
        limit: int = 100,
        authtoken: str = Header(None)
):
    """
    Ritorna lo stato del servizio
    """
    check_token_get_auth()
    return retrieve_forms(form_type)


@mongoform_api.post("/", tags=["inrim-forms"])
async def mongo_add_form(
        form: Form,
        authtoken: str = Header(None)
):
    """
    Salva un form
    """
    saved = await save_form_schema(form)
    return saved


@mongoform_api.get("/{id}", response_model=Form, tags=["inrim-forms"])
async def mongo_form_id(
        id: str,
        skip: int = 0,
        limit: int = 100,
        authtoken: str = Header(None)
):
    """
    Ritorna lo stato del servizio
    """
    form = await retrieve_form(id)
    return form


@mongoform_api.delete("/{id}", response_model=Form, tags=["inrim-forms"])
async def delete_form_id(
        id: str,
        skip: int = 0,
        limit: int = 100,
        authtoken: str = Header(None)
):
    """
    Ritorna lo stato del servizio
    """
    form = await delete_form(id)
    return form

@mongoform_api.get("/{id}/submissions",
                   response_model=ListSubmission,
                   tags=["inrim-forms"])
async def mongo_submissions(
        id: str,
        skip: int = 0,
        limit: int = 100,
        authtoken: str = Header(None)
):
    """
    Ritorna lo stato del servizio
    """

    return await retrieve_submissions(id)


@mongoform_api.get("/{id}/submit",
                   tags=["inrim-forms"])
async def mongo_submit(
        submission: Submission,
        skip: int = 0,
        limit: int = 100,
        authtoken: str = Header(None)
):
    """
    Ritorna lo stato del servizio
    """

    return await save_submission(submission)


@mongoform_api.get("/{id}/submission",
                   response_model=Submission,
                   tags=["inrim-forms"])
async def mongo_submission(
        id: str,
        skip: int = 0,
        limit: int = 100,
        authtoken: str = Header(None)
):
    """
    Ritorna lo stato del servizio
    """

    return await retrieve_submission(id)


@mongoform_api.get("/{id}/submissions/resources",
                   response_model=ListSubmission,
                   tags=["inrim-forms"])
async def mongo_submissions_resources(
        id: str,
        skip: int = 0,
        limit: int = 100,
        authtoken: str = Header(None)
):
    """
    Ritorna lo stato del servizio
    """
    logger.info("get_submission")

    return await retrieve_submissions(id)
