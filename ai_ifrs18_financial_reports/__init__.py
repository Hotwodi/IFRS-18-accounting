from . import models
from . import wizard
from . import reports


def _post_init_hook(env):
    env['ifrs18.category']._bootstrap_categories()
