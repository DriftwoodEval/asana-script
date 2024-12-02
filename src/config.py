from os import getenv

import asana
import keyring
from dotenv import load_dotenv

load_dotenv()

ADMIN_MODE = getenv("ADMIN_MODE", "True").lower() in ["true", "1", "yes"]


# This is a hack to fix AttributeError: 'NoneType' object has no attribute 'dumps', which seems to not actually effect the functionality, but prints a Traceback
class CustomApiClient(asana.ApiClient):
    def __del__(self):
        try:
            super().__del__()
        except AttributeError:
            pass


def get_consts():
    global \
        configuration, \
        projects_api_instance, \
        WORKSPACE_GID, \
        ASANA_COLORS, \
        INITIALS, \
        allowed_domains

    configuration = asana.Configuration()

    configuration.access_token = get_secret("ASANA_TOKEN", "token")

    api_client = CustomApiClient(configuration)
    projects_api_instance = asana.ProjectsApi(api_client)

    WORKSPACE_GID = get_secret("ASANA_WORKSPACE_GID", "workspace")

    ASANA_COLORS = getenv("ASANA_COLORS", "light-blue").split(",")

    INITIALS = get_secret("USER_INITIALS", "initials")

    allowed_domains = ["mhs.com", "pearsonassessments.com"]


def get_secret(env_name, key_name):
    secret = getenv(env_name)
    if not secret:
        secret = keyring.get_password("asana", key_name)
        if not secret:
            secret = input(f"Enter your {key_name}: ")
            keyring.set_password("asana", key_name, secret)
    return secret


def reset(key: str):
    valid_keys = ["all", "token", "initials"]
    if key not in valid_keys:
        raise ValueError(f"Invalid key. Must be one of: {', '.join(valid_keys)}")
    if key == "all":
        if keyring.get_password("asana", "token"):
            keyring.delete_password("asana", "token")
        if keyring.get_password("asana", "initials"):
            keyring.delete_password("asana", "initials")
        print("All keys deleted.")
    else:
        if keyring.get_password("asana", key):
            keyring.delete_password("asana", key)
            print(f"{key.capitalize()} deleted.")
        else:
            print(f"{key.capitalize()} not found.")
