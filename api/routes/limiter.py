from slowapi import Limiter
from slowapi.util import get_remote_address

# https://slowapi.readthedocs.io/en/latest/examples/#disable-the-limiter-entirely
limiter = Limiter(key_func=get_remote_address, enabled=True)
