import sys
from typing import Optional

from starlette.responses import RedirectResponse

sys.path.append("..")
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from .services import *
import logging

logger = logging.getLogger(__name__)

builder_api = FastAPI()


def form_builder_tabs(request, id_form="", id_submission="", url_path="/builder/"):
    tabs = {
        "rows": [
            {
                "url": f"{url_path}forms",
                "label": "Forms",
                "active": request.url.path == f"{url_path}forms"
            },
            {
                "url": f"{url_path}builder/{id_form}",
                "label": "Design",
                "active": (
                        request.url.path == f"{url_path}builder/" or
                        request.url.path == f"{url_path}builder/{id_form}"
                )
            },
            {
                "url": f"{url_path}form/{id_form}",
                "label": "Form",
                "active": request.url.path == f"{url_path}form/{id_form}" and id_form
            },
            {
                "url": f"{url_path}form/{id_form}/submissions",
                "label": "Submissions",
                "active": request.url.path == f"{url_path}form/{id_form}/submissions"
            },
            {
                "url": f"{url_path}form/{id_form}/{id_submission}",
                "label": "Submission",
                "active": request.url.path == f"{url_path}form/{id_form}/{id_submission}"
            }
        ]}
    template = templates.get_template("/italia/templates/components/bolck_tabs.html")
    tab = template.render(tabs)
    return tab


def check_token_get_auth(token: str):
    logger.info("check_token_get_auth")
    return ""


@builder_api.get("/forms", response_class=HTMLResponse)
async def r_get_forms(
        request: Request,
        authtoken: str = Header(None)
):
    check_token_get_auth(authtoken)
    page = await get_forms(request, url_path="/builder/")
    page.beforerows.append(form_builder_tabs(request))
    return page.render_page(
        "/italia/templates/components/page_layout/page_hero.html", {}, **{}
    )


@builder_api.get("/builder/", response_class=HTMLResponse)
async def builder_iframe(
        request: Request,
):
    page = await get_builder_page(request, "/formio/builder_frame.html", id="")
    page.beforerows.append(form_builder_tabs(request))
    return page.render_page(
        "/italia/templates/components/page_layout/page_hero.html", {}, **{}
    )


@builder_api.get("/builder/{id}", response_class=HTMLResponse)
async def builder_iframe(
        request: Request,
        id: Optional[str]
):
    page = await get_builder_page(request, "/formio/builder_frame.html", id=id)
    page.beforerows.append(form_builder_tabs(request, id_form=id))
    return page.render_page(
        "/italia/templates/components/page_layout/page_hero.html", {}, **{}
    )


@builder_api.get("/formio_builder/", response_class=HTMLResponse)
async def r_get_builder(
        request: Request,
        authtoken: str = Header(None)
):
    check_token_get_auth(authtoken)
    page = await get_builder(request)
    return page.render_page(
        "/formio/builder.html", {}, **{}
    )


@builder_api.get("/formio_builder/{id}", response_class=HTMLResponse)
async def r_get_builder(
        request: Request,
        id: Optional[str] = "",
        authtoken: str = Header(None)
):
    check_token_get_auth(authtoken)
    page = await get_builder(request, id)
    return page.render_page(
        "/formio/builder.html", {}, **{}
    )


@builder_api.post("/builder", tags=["builder"])
async def add_new_form(
        request: Request,
        authtoken: str = Header(None)
):
    """
    Salva un form
    """
    check_token_get_auth(authtoken)
    saved = await builder_add_form(request)
    return {"status": "ok", "link": f"/builder/builder/{saved}", "reload": True}


@builder_api.post("/builder/{id}", tags=["builder"])
async def add_form(
        request: Request,
        id: Optional[str],
        authtoken: str = Header(None)
):
    """
    Salva un form
    """
    check_token_get_auth(authtoken)
    saved = await builder_add_form(request, id)
    return {"status": "ok", "link": f"/builder/builder/{saved}", "reload": True}


@builder_api.delete("/builder/{id}", tags=["builder"])
async def r_delete_form(
        request: Request,
        id: Optional[str],
        authtoken: str = Header(None)
):
    """
    Salva un form
    """
    check_token_get_auth(authtoken)
    saved = await builder_delete_form(request, id)
    return {"status": "ok", "link": "/builder/forms", "reload": True}


@builder_api.get("/form/", response_class=HTMLResponse, tags=["builder"])
async def form_no_id(
        request: Request,
        authtoken: str = Header(None)
):
    check_token_get_auth(authtoken)
    return RedirectResponse("/builder/builder/")


@builder_api.get("/form/{id}", response_class=HTMLResponse, tags=["builder"])
async def form_form(
        request: Request, id: Optional[str] = "",
        authtoken: str = Header(None)
):
    """
    Ritorna lo stato del servizio
    """

    check_token_get_auth(authtoken)
    page = await get_form_page(request, id, url_path="/builder/form/")
    page.beforerows.append(form_builder_tabs(request, id_form=id))
    return page.render_page(
        "/italia/templates/components/page_layout/page_hero.html", {}, **{}
    )


@builder_api.post("/form/{id}", tags=["builder"])
async def submit_form_data(
        request: Request, id: str,
        authtoken: str = Header(None)
):
    """
    Salva un form
    """
    check_token_get_auth(authtoken)
    saved = await submit_data_form(request, id)
    return {"status": "ok", "link": f"/builder/form/{id}/submissions", "reload": True}


@builder_api.get("/form/{id_form}/submissions", response_class=HTMLResponse, tags=["builder"])
async def list_submission(
        request: Request, id_form: str,
        authtoken: str = Header(None)
):
    """
    Ritorna la lista dei forms
    """
    check_token_get_auth(authtoken)
    page = await get_table_submissions(request, id_form, url_path="/builder/form/")
    page.beforerows.append(form_builder_tabs(request, id_form=id_form))
    return page.render_page(
        "/italia/templates/components/page_layout/page_hero.html", {}, **{}
    )


@builder_api.post("/form/{id_form}/{id_submission}", tags=["builder"])
async def form_submitted_submit(
        request: Request, id_form: str, id_submission: str,
        authtoken: str = Header(None)
):
    """
    Ritorna lo stato del servizio
    """
    check_token_get_auth(authtoken)
    saved = await submit_data_form(request, id_form, id_submission, url_path="/builder/form/")
    return {"status": "ok", "link": f"/builder/form/{id_form}/submissions", "reload": True}


@builder_api.get("/form/{id_form}/{id_submission}", response_class=HTMLResponse, tags=["builder"])
async def form_submitted(
        request: Request, id_form: str, id_submission: str,
        authtoken: str = Header(None)
):
    """
    Ritorna lo stato del servizio
    """
    check_token_get_auth(authtoken)
    page = await get_form_page(request, id_form, id_submission, url_path="/builder/form/")
    page.beforerows.append(form_builder_tabs(request, id_form=id_form, id_submission=id_submission))
    return page.render_page(
        "/italia/templates/components/page_layout/page_hero.html", {}, **{}
    )


@builder_api.get("/forms", response_class=HTMLResponse, tags=["builder"])
async def list_forms(
        request: Request,
        authtoken: str = Header(None)
):
    """
    Ritorna la lista dei forms
    """
    check_token_get_auth(authtoken)
    page = await get_list_forms_type(request, form_type="form", url_path="/builder/")
    return page.render_page(
        "/italia/templates/components/page_layout/page_hero.html", {}, **{}
    )


@builder_api.get("/resources", response_class=HTMLResponse, tags=["builder"])
async def list_resurces(
        request: Request,
        authtoken: str = Header(None)
):
    """
    Ritorna la lista dei forms
    """
    check_token_get_auth(authtoken)
    page = await get_list_forms_type(request, form_type="resource", url_path="/builder/")
    return page.render_page(
        "/italia/templates/components/page_layout/page_hero.html", {}, **{}
    )
