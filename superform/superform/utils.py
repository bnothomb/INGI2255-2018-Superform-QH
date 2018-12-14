from datetime import datetime
from enum import Enum
from functools import wraps
from flask import render_template, session, current_app


def login_required(admin_required=False):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get("logged_in", False) or (admin_required and not session.get("admin", False)):
                return render_template("403.html"), 403
            else:
                return f(*args, **kwargs)
        return decorated_function
    return decorator


def datetime_converter(stri):
    return datetime.strptime(stri, "%Y-%m-%d")


def time_converter(stri):
    return datetime.strptime(stri, "%H:%M")


def str_converter(datet):
    return datetime.strftime(datet, "%Y-%m-%d")


def str_time_converter(datet):
    return datetime.strftime(datet, "%H:%M")


def get_instance_from_module_path(module_p):
    import os
    module_p = module_p.replace(".", os.sep) # use the os file path separator
    import importlib.util
    spec = importlib.util.spec_from_file_location("module.name", module_p+".py")
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)
    return foo


def get_modules_names(modules_keys):
    return [m.split('.')[2] for m in modules_keys]


def get_module_full_name(module_name):
    for m in current_app.config["PLUGINS"].keys():
        if m.split('.')[2] == module_name:
            return m


class StatusCode(Enum):
    OK = 0
    ERROR = 1
    URL = 2
