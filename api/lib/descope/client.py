from descope.descope_client import DescopeClient
from ..env import env_info

DESCOPE_CLIENT = DescopeClient(project_id=env_info.DESCOPE_PROJECT_ID)
