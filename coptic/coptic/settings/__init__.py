from .base import *
# Set an environment variable ENVIROMENT to 'prod' to use production settings
if 'prod' in os.environ.get('COPTIC_ENVIROMENT','dev'):
    from .prod import *
else:
    from .dev import *