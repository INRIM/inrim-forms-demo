from typing import List, Optional, Dict, Any, Literal
from bson.objectid import ObjectId

from odmantic import Model, Field, Reference, ObjectId
from slugify import slugify


class Role(Model):
    title: str
    description: str
    type: Literal['user', 'perissioin']
    deleted: Optional[int]
    default: bool = False
    admin: bool = False


class User(Model):
    uid: str
    functions: List[Role]
    data: Dict
    deleted: Optional[int]


class PermissionSchema(Model):
    type: Literal[
        'create_all',
        'read_all',
        'update_all',
        'delete_all',
        'create_own',
        'read_own',
        'update_own',
        'delete_own',
        'self'
    ]
    roles: List[Role]


class FieldPermission(Model):
    read: List[PermissionSchema]
    write: List[PermissionSchema]
    create: List[PermissionSchema]
    admin: List[PermissionSchema]


class Project(Model):
    title: str
    description: str
    deleted: Optional[int]
    path: str = ""

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #     if self.path == "":
    #         self.path = slugify(self.name)


class Form(Model):
    title: str
    name: str
    components: List[Dict]
    path: str = ""
    type: Literal['form', 'resource'] = 'form'
    display: str = ""
    action: str = ""
    tags: Optional[List[str]] = []
    deleted: Optional[int]
    access: List[PermissionSchema] = []
    submissionAccess: List[PermissionSchema] = []
    fieldMatchAccess: Optional[ObjectId]
    owner: Optional[ObjectId]
    settings: Dict = {}
    properties: Dict = {}
    project: Optional[ObjectId]
    sys_form: bool = False


class Submission(Model):
    form: ObjectId
    data: Dict
    owner: Optional[ObjectId]
    deleted: Optional[int]
    roles: List[Role] = []
    access: List[PermissionSchema] = []


class Action(Model):
    title: str
    name: str
    handler: List[str]
    method: List[str]
    condition: Dict = {}
    priority: int = 0
    settings: Dict = {}
    form: Form = Reference()
    deleted: Optional[int]


class ActionItemSchema(Model):
    title: str
    form: Form = Reference()
    submission: Submission = Reference()
    action: str
    handler: str
    method: str
    state: Literal['new', 'inprogress', 'complete', 'error'] = 'new'
    messages: List[Any] = []
    data: Dict = {}


class Access(Model):
    type: Literal[
        'read',
        'create',
        'update',
        'delete',
        'write',
        'admin'
    ]
    resources: List[Form]


class ListForm(Model):
    forms: List[Form]


class ListSubmission(Model):
    forms: List[Submission]
