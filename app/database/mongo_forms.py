import sys
from datetime import datetime
import bson
from odmantic import AIOEngine
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.settings import get_settings
from .models import *

logger = logging.getLogger(__name__)

client = AsyncIOMotorClient(
    get_settings().mongo_url,
    # "docker.ininrim.it:27018",
    username=get_settings().mongo_user,
    password=get_settings().mongo_pass,
    replicaset="rs",
    serverSelectionTimeoutMS=10, connectTimeoutMS=20000)

engine = AIOEngine(motor_client=client, database=get_settings().mongo_db)


# forms_collection = database.get_collection("forms")
# submissions_collection = database.get_collection("submissions")


def data_helper(d):
    if isinstance(d, bson.objectid.ObjectId) or isinstance(d, datetime):
        return str(d)

    if isinstance(d, list):  # For those db functions which return list
        return [data_helper(x) for x in d]

    if isinstance(d, dict):
        for k, v in d.items():
            d.update({k: data_helper(v)})

    # return anything else, like a string or number
    return d


def get_schema_form_data_tabe(list_data, fields=["_id"], merge_field=""):
    new_list = []
    for i in list_data:
        new_list.append(data_helper_list(i.dict(), fields=fields, merge_field=merge_field))
    return new_list


def data_helper_list(d, fields=["_id"], merge_field=""):
    dres = {}
    data = data_helper(d)
    if not merge_field == "":
        dres = data[merge_field].copy()
        for k in fields:
            if not k == merge_field:
                dres[k] = data[k]
        # for k, v in dres.items():
        #     if isinstance(v, dict):
        #         dres[k] = v['data']['nome']
    else:
        for k, v in data.items():
            if k in fields:
                dres[k] = v
    return dres


async def retrieve_forms(type_form="form"):
    query = (Form.type == type_form) & (Form.deleted == None)
    forms = await engine.find(Form, query, sort=Form.title)
    return forms


async def save_form_schema(schema: Form):
    return await engine.save(schema)


async def delete_form(form_id: str):
    form = await retrieve_form(form_id)
    return await engine.delete(form)


# Retrieve a form with a matching ID
async def retrieve_form(form_id: str) -> Form:
    form = await engine.find_one(Form, Form.id == ObjectId(form_id))
    return form


async def retrieve_submissions(data_id):
    q = (Submission.form == ObjectId(data_id)) & (Submission.deleted == None)
    submissions = await engine.find(Submission, q, sort=Submission.id)
    return submissions


async def retrieve_submission(data_id):
    submission = await engine.find_one(Submission, Submission.id == ObjectId(data_id))
    return submission


async def save_submission(schema: Submission):
    return await engine.save(schema)
