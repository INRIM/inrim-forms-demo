import sys

sys.path.append("..")
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from .services import *
import logging

logger = logging.getLogger(__name__)

client_api = FastAPI()


# client_api.mount("/static", StaticFiles(directory="themes/italia/static"), name="static")


def check_token_get_auth(token: str):
    logger.info("check_token_get_auth")
    return ""


@client_api.get("/{id}", response_class=HTMLResponse, tags=["base"])
async def client_form(
        request: Request, id: str,
        authtoken: str = Header(None)
):
    """
    Ritorna lo stato del servizio
    """
    check_token_get_auth(authtoken)
    page = await get_form_page(request, id, url_path="/client/")
    return page.render_page(
        "/italia/templates/components/page_layout/page_hero.html", {}, **{}
    )


@client_api.post("/{id}", tags=["inrim-forms"])
async def submit_form_data(
        request: Request, id: str,
        authtoken: str = Header(None)
):
    """
    Salva un form
    """
    check_token_get_auth(authtoken)
    saved = await submit_data_form(request, id)
    logger.info(saved)
    logger.info("--------")
    return {"status": "ok", "id": saved}


@client_api.get("/{id_form}/submissions", response_class=HTMLResponse, tags=["base"])
async def list_submission(
        request: Request, id_form: str,
        authtoken: str = Header(None)
):
    """
    Ritorna la lista dei forms
    """
    check_token_get_auth(authtoken)
    page = await get_table_submissions(request, id_form, url_path="/client/")
    return page.render_page(
        "/italia/templates/components/page_layout/page_hero.html", {}, **{}
    )


@client_api.get("/{id_form}/{id_submission}", response_class=HTMLResponse, tags=["client"])
async def form_submitted(
        request: Request, id_form: str, id_submission: str,
        authtoken: str = Header(None)
):
    """
    Ritorna lo stato del servizio
    """
    check_token_get_auth(authtoken)
    page = await get_form_page(request, id_form, id_submission, url_path="/client/")
    return page.render_page(
        "/italia/templates/components/page_layout/page_hero.html", {}, **{}
    )


@client_api.get("/grid/{key}/{id_form}/rows/", tags=["client"])
async def client_grid_rows(
        request: Request, key: str, id_form: str,
        authtoken: str = Header(None)
):
    check_token_get_auth(authtoken)
    return await grid_rows(request, key, id_form)


@client_api.get("/grid/{key}/{id_form}/rows/{id_submission}", tags=["client"])
async def client_grid_rows_data(
        request: Request, key: str, id_form: str, id_submission: str,
        authtoken: str = Header(None)
):
    check_token_get_auth(authtoken)
    return await grid_rows(request, key, id_form, id_submission)


@client_api.get("/grid/{key}/{id_form}/{num_rows}/newrow", tags=["client"])
async def client_grid_new_row(
        request: Request, key: str, id_form: str, num_rows: int,
        authtoken: str = Header(None)
):
    check_token_get_auth(authtoken)
    return await grid_add_row(request, key, id_form, num_rows)
