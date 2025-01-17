from .base import *
# Set an environment variable ENVIROMENT to 'prod' to use production settings
if 'prod' in os.environ.get('COPTIC_ENVIROMENT','dev'):
    print("Using production settings")
    from .prod import *
else:
    print("Using development settings")
    from .dev import *