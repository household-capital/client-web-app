
from .base_settings import *
from .log_settings import *

try:
    from .development import *
except ImportError as e:
    try:
        from .production import *
    except ImportError as e:
        pass
