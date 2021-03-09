import sys
from typing import Optional

from bson import ObjectId

sys.path.append("..")
import requests

from libs.services.utils_for_service import *
from database.mongo_forms import *
from database.models import *
from database.mongo_forms_api import *
from database.mongo_forms_api import *
from .base_setting import *
from fastapi import FastAPI, Request, Header, HTTPException, Depends
from themes.server.main.components.widgets_table_form import TableFormWidget
from themes.server.main.components.widgets_table import TableWidget
from themes.server.main.components.widgets_form import FormIoWidget
from themes.server.main.components.widgets_content import PageWidget
from themes.server.main.components.widgets_form_builder import FormIoBuilderWidget
import logging

logger = logging.getLogger(__name__)


def get_ext_submission(id):
    headers = {
        "Content-Type": "application/json",
        get_settings().data_builder_headerkey: get_settings().data_builder_key
    }
    url = f"{get_settings().data_builder_url}/{id}/submissions/resources"
    res = requests.request("get", url, headers=headers)
    return res.json()


async def get_forms(request: Request, url_path="/") -> TableWidget:
    settings = get_settings()
    # schema = await formio_api.get_forms("form")
    schema = await retrieve_forms("form")
    data = get_schema_form_data_tabe(schema, fields=["id", "title"])
    page = TableWidget(
        templates, request, settings, schema=data, resource_ext=get_ext_submission, base_path=url_path
    )
    page.title = "Moduli"
    table = page.make_def_table(data, click_url=f"{url_path}builder/")
    page.rows.append(table)
    return page


async def get_builder_page(
        request: Request, tmp_name,
        id: Optional[str] = "",
        builder_type_path="formio_builder/"
) -> PageWidget:
    settings = get_settings()
    page = PageWidget(templates, request, settings)
    block = page.render_custom(tmp_name, {"page_api_action": f"{builder_type_path}{id}"})
    page.rows.append(block)
    return page


async def get_builder(
        request: Request,
        form_id: Optional[str] = "",
        builder_type_path="formio_builder/"
) -> PageWidget:
    settings = get_settings()
    action_buttons = []
    components = []
    name = ""
    title = ""
    preview_link = ""
    if form_id == "":
        action_buttons.append(
            {"id": "save_form", "label": "Salva", "url_action": "/builder/builder", "icon": "it-plus-circle",
             "type": "POST", "cls": "offset-3"}
        )

    else:
        form = await mongo_form_id(form_id)
        components = form.components
        name = form.name
        title = form.title
        preview_link = f"/builder/form/{form_id}"
        action_buttons.append(
            {"id": "update_form", "label": "Aggiorna", "url_action": f"/builder/builder/{form_id}",
             "icon": "it-refresh",
             "type": "POST", "cls": "offset-3"}
        )
        action_buttons.append(
            {"id": "copy_form", "label": "Duplica", "url_action": f"/builder/builder", "icon": "it-copy",
             "type": "POST"}
        )
        action_buttons.append(
            {"id": "delete_form", "label": "Elimina", "url_action": f"/builder/builder/{form_id}", "icon": "it-delete",
             "type": "DELETE"}
        )
    page = FormIoBuilderWidget(
        templates, request, settings, components, form_id, name=name, title=title, preview_link=preview_link,
        page_api_action=f"{builder_type_path}{form_id}",
        action_buttons=action_buttons)
    return page


async def builder_add_form(request: Request, form_id: Optional[str] = ""):
    util = UtilsForService()
    forms = await request.json()
    formx = util.deserialize_list_key_values(forms)
    if "tags" in formx:
        formx['tags'] = formx['tags'].split(",")

    if not form_id == "":
        formx['id'] = form_id
    form = Form(**formx)
    saved = await mongo_add_form(form)
    return str(form.id)


async def builder_delete_form(request: Request, form_id: Optional[str], ):
    logger.info("xxxxxxxxxxxxxxxxs")
    return await delete_form_id(form_id)


async def submit_data_form(request: Request, id: str, id_submission: Optional[str] = "", url_path="/"):
    util = UtilsForService()
    settings = get_settings()
    forms = await request.form()
    data = util.clean_save_form_data(forms)
    form = await mongo_form_id(id)
    schema = data_helper(form.dict())
    page = FormIoWidget(
        templates, request, settings, schema=schema
    )
    data = page.compute_component_data(data)
    logger.info(data)
    if not id_submission == "":
        submission = Submission(
            id=ObjectId(id_submission), form=ObjectId(id), data=data
        )
    else:
        submission = Submission(
            form=ObjectId(id), data=data
        )

    saved = await mongo_submit(submission)
    return str(submission.id)


async def get_form_page(request: Request, id_form: str, id_submission: str = "", url_path="/") -> FormIoWidget:
    settings = get_settings()

    form = await mongo_form_id(id_form)
    schema = data_helper(form.dict())

    disabled = False

    page = FormIoWidget(
        templates, request, settings, schema=schema, resource_ext=get_ext_submission, disabled=disabled,
        base_path=url_path
    )
    page.api_action = f"{url_path}{id_form}/{id_submission}"

    if not id_submission == "":
        data = await mongo_submission(id_submission)
        schema_data = data_helper(data.dict())
        page.submission_id = id_submission
        form = page.make_form(schema_data['data'])
    else:
        form = page.make_form({})

    page.rows.append(form)
    return page


async def get_table_submissions(request: Request, id: str, url_path="/") -> TableFormWidget:
    settings = get_settings()
    form_schema = await mongo_form_id(id)
    schema = await mongo_submissions(id)
    data = get_schema_form_data_tabe(schema, fields=["id", "data"], merge_field="data")
    page = TableFormWidget(
        templates, request, settings,
        schema=data, form_schema=data_helper(form_schema.dict()), resource_ext=get_ext_submission,
        base_path=url_path
    )
    page.title = ""
    table = page.make_def_table(data, click_url=f"{url_path}{id}/")
    page.rows.append(table)
    return page


async def get_list_forms_type(request: Request, form_type: str = 'form', url_path="/builder/") -> TableWidget:
    settings = get_settings()
    schema = await mongo_forms(form_type)
    page = TableWidget(
        templates, request, settings, schema=schema, resource_ext=get_ext_submission,
        base_path=url_path
    )
    page.title = "Moduli"
    table = page.make_def_table(schema)
    page.rows.append(table)
    return page


async def grid_rows(request: Request, key: str, id_form: str, id_submission: str = ""):
    settings = get_settings()

    form = await mongo_form_id(id_form)
    schema = data_helper(form.dict())
    disabled = False
    page = FormIoWidget(
        templates, request, settings, schema=schema, resource_ext=get_ext_submission, disabled=disabled)

    if not id_submission == "":
        data = await mongo_submission(id_submission)
        schema_data = data_helper(data.dict())
        page.load_data(schema_data['data'])
    res = page.grid_rows(key, render=True)
    return res


async def grid_add_row(
        request: Request, key: str, id_form: str, num_rows: int, id_submission: str = ""):
    settings = get_settings()

    form = await mongo_form_id(id_form)
    schema = data_helper(form.dict())

    page = FormIoWidget(
        templates, request, settings, schema=schema, resource_ext=get_ext_submission)

    if not id_submission == "":
        data = await mongo_submission(id_submission)
        schema_data = data_helper(data.dict())
        page.load_data(schema_data['data'])
    res = page.grid_add_row(key, num_rows, render=True)
    return res


async def survey_rows(request: Request, key: str, id_form: str, id_submission: str = ""):
    settings = get_settings()

    form = await mongo_form_id(id_form)
    schema = data_helper(form.dict())

    page = FormIoWidget(
        templates, request, settings, schema=schema, resource_ext=get_ext_submission, disabled=not id_submission == "")

    if not id_submission == "":
        data = await mongo_submission(id_submission)
        schema_data = data_helper(data.dict())
        page.load_data(schema_data['data'])
    res = page.survey_rows(key, render=True)
    return res
