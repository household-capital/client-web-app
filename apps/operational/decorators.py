import traceback
from functools import wraps

from apps.lib.site_Utilities import raiseTaskAdminError

def email_admins_on_failure(task_name):
    def inner_wrapper(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                fn(*args, **kwargs)
            except Exception as e: 
                tb = traceback.format_exc()
                raiseTaskAdminError(
                    "Periodic Task - {}".format(task_name),
                    tb
                )
                raise e
        return wrapper
    return inner_wrapper