from os import getenv

import asana
import keyring
from dotenv import load_dotenv

load_dotenv()

ADMIN_MODE = getenv("ADMIN_MODE", "True").lower() in ["true", "1", "yes"]


def get_consts():
    global configuration, projects_api_instance, WORKSPACE_GID, ASANA_COLORS, INITIALS

    configuration = asana.Configuration()

    configuration.access_token = get_secret("ASANA_TOKEN", "token")

    api_client = asana.ApiClient(configuration)
    projects_api_instance = asana.ProjectsApi(api_client)

    WORKSPACE_GID = get_secret("ASANA_WORKSPACE_GID", "workspace")

    ASANA_COLORS = getenv("ASANA_COLORS", "light-blue").split(",")

    INITIALS = get_secret("USER_INITIALS", "initials")


def get_secret(env_name, key_name):
    secret = getenv(env_name)
    if not secret:
        secret = keyring.get_password("asana", key_name)
        if not secret:
            secret = input(f"Enter your {key_name}: ")
            keyring.set_password("asana", key_name, secret)
    return secret


def reset(args):
    valid_keys = ["all", "token", "workspace", "initials"]
    if not all(key in valid_keys for key in args):
        raise ValueError("Invalid key. Must be one of: " + ", ".join(valid_keys))
    for key in args:
        if key == "all":
            if keyring.get_password("asana", "token"):
                keyring.delete_password("asana", "token")
            if keyring.get_password("asana", "workspace"):
                keyring.delete_password("asana", "workspace")
            if keyring.get_password("asana", "initials"):
                keyring.delete_password("asana", "initials")
            print("All keys deleted.")
        else:
            if keyring.get_password("asana", key):
                keyring.delete_password("asana", key)
                print(f"{key.capitalize()} deleted.")
            else:
                print(f"{key.capitalize()} not found.")
