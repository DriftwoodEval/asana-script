import re
from datetime import datetime
from os import getenv

import asana
from asana.rest import ApiException
from dotenv import load_dotenv

load_dotenv()

configuration = asana.Configuration()

access_token = getenv("ASANA_TOKEN")
if access_token is not None:
    configuration.access_token = access_token
else:
    raise ValueError("ASANA_TOKEN environment variable must be set")

api_client = asana.ApiClient(configuration)
projects_api_instance = asana.ProjectsApi(api_client)

WORKSPACE_GID = getenv("ASANA_WORKSPACE_GID")


def get_projects_by_color(colors) -> list[dict]:
    options = {
        "limit": 100,
        "archived": False,
        "opt_fields": "name,color,permalink_url,notes",
    }

    try:
        projects = projects_api_instance.get_projects_for_workspace(
            WORKSPACE_GID, options
        )
        filtered_projects = []
        for project in projects:  # type: ignore
            if project["color"] not in colors:
                continue
            else:
                filtered_projects.append(project)
        return filtered_projects
    except ApiException as e:
        print(f"Exception when calling ProjectsApi->get_projects_for_workspace: {e}")
        return []


def write_projects_to_file(projects: list[dict]):
    for project in projects:
        project_name = re.sub(r"\s+", " ", project["name"]).strip()
        today_date = datetime.now().strftime("%Y-%m-%d")

        try:
            with open("output.txt", "r+") as file:
                lines = file.readlines()
                if not any(project["permalink_url"] in line for line in lines):
                    if not any(today_date in line for line in lines):
                        file.write(f"\nClients found on {today_date}\n")
                    file.write(f"{project_name}: {project['permalink_url']}\n")
        except FileNotFoundError:
            with open("output.txt", "w") as file:
                file.write(
                    f"Clients found on {today_date}\n{project_name}: {project['permalink_url']}\n"
                )


def get_projects_with_dates(projects: list[dict]) -> list[dict]:
    filtered_projects = []
    for project in projects:
        if re.search(r"\d{1,2}.\d{1,2}(.\d{1,4})?", project["name"]):
            filtered_projects.append(project)
    return filtered_projects


if getenv("M_MODE"):
    write_projects_to_file(get_projects_by_color(["light-pink", "dark-pink"]))
elif getenv("K_MODE"):
    write_projects_to_file(
        get_projects_with_dates(get_projects_by_color(["light-purple"]))
    )
