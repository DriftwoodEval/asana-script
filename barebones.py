import re
from datetime import datetime
from os import getenv

import asana
from asana.rest import ApiException

configuration = asana.Configuration()

configuration.access_token = getenv("ASANA_TOKEN")

api_client = asana.ApiClient(configuration)
projects_api_instance = asana.ProjectsApi(api_client)

WORKSPACE_GID = getenv("ASANA_WORKSPACE_GID")


def get_projects_by_color(colors):
    options = {
        "limit": 100,
        "archived": False,
        "opt_fields": "name,color,permalink_url,notes",
    }

    try:
        projects = projects_api_instance.get_projects_for_workspace(
            WORKSPACE_GID, options
        )
        for project in projects:
            if project["color"] not in colors:
                continue

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
    except ApiException as e:
        print(f"Exception when calling ProjectsApi->get_projects_for_workspace: {e}")


get_projects_by_color(["light-pink", "dark-pink"])
