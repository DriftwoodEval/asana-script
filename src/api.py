import re
import sys
from datetime import datetime

import colored
from asana.rest import ApiException

import src.config
import src.utils


def get_asana_tasks_by_color(colors=None, expired=False):
    src.config.get_consts()
    if colors is None:
        colors = src.config.ASANA_COLORS
    opts = {
        "limit": 100,
        "archived": False,
        "opt_fields": "name,color,permalink_url,notes",
    }
    try:
        print("Fetching projects...")

        api_response = list(
            src.config.projects_api_instance.get_projects_for_workspace(
                src.config.WORKSPACE_GID, opts
            )
        )

        filtered_projects = [data for data in api_response if data["color"] in colors]
        project_count = len(filtered_projects)

        print(f"Found {project_count} projects.")

        for i, data in enumerate(filtered_projects, 1):
            if not src.config.ADMIN_MODE:
                data["name"] = re.sub(r"\[.*?\]|\{.*?\}|[^\w\s]", "", data["name"])
            data["name"] = re.sub(r"\s+", " ", data["name"]).strip()
            data["messages_sent"] = (
                data["notes"].lower().count(f"lm {src.config.INITIALS}")
            )
            data["warnings_sent"] = (
                data["notes"].lower().count(f"lw {src.config.INITIALS}")
            )
            data["messages_sent_top"] = 0
            lines = data["notes"].splitlines()
            for j, line in enumerate(lines):
                if f"lm {src.config.INITIALS}" in line.lower():
                    data["messages_sent_top"] = j + 1
                else:
                    break
            data["warning_on_top"] = (
                f"lw {src.config.INITIALS}" in data["notes"].splitlines()[0].lower()
                if data["notes"]
                else False
            )

            if expired:
                data["name"] = re.sub(r"(ASD|ADHD)", "", data["name"])
                data["name"] = re.sub(r"\s+", " ", data["name"]).strip()
                src.utils.get_expired(data)
            else:
                if not src.config.ADMIN_MODE:
                    if data["warning_on_top"]:
                        print(f"Skipping {data['name']}, already sent final warning.")
                        continue
                    if data["notes"] and (
                        datetime.now().strftime("%m/%d")
                        in data["notes"].splitlines()[0]
                    ):
                        print(f"Skipping {data['name']}, already noted today.")
                        continue
                if sys.platform == "linux":
                    print(
                        f"\n({i}/{project_count})\n{colored.Fore.cyan}{colored.Style.bold}Name:{colored.Style.reset} {data['name']}\n{colored.Fore.magenta}{colored.Style.bold}Link:{colored.Style.reset} {data['permalink_url']}\n{colored.Fore.blue}{colored.Style.bold}Notes:{colored.Style.reset} {data['notes'].strip()}"
                    )
                else:
                    print(
                        f"\n({i}/{project_count})\nName: {data['name']}\nLink: {data['permalink_url']}\nNotes: {data['notes'].strip()}"
                    )
                src.utils.what_to_do(data)

        if sys.platform != "linux":
            input("End of list! You can close this window now.")
    except ApiException as e:
        print(
            "Exception when calling ProjectsApi->get_projects_for_workspace: %s\n" % e
        )


def replace_notes(new_text, project_gid):
    body = {"data": {"notes": new_text}}
    try:
        api_response = src.config.projects_api_instance.update_project(
            body, project_gid, opts={"opt_fields": "name, notes"}
        )
        print(f"Added note to {api_response['name']}.")
    except ApiException as e:
        print("Exception when calling ProjectsApi->update_project:: %s\n" % e)


def change_color(color, project_gid):
    body = {"data": {"color": color}}
    try:
        api_response = src.config.projects_api_instance.update_project(
            body, project_gid, opts={"opt_fields": "name, color"}
        )
        print(f"Changed color of {api_response['name']} to {color}.")
    except ApiException as e:
        print("Exception when calling ProjectsApi->update_project:: %s\n" % e)
