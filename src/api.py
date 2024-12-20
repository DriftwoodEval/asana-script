import re
import sys
from datetime import datetime, timedelta

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
                src.config.WORKSPACE_GID,
                opts,  # pyright: ignore (asana api is strange)
            )
        )

    except ApiException as e:
        print(
            "Exception when calling ProjectsApi->get_projects_for_workspace: %s\n" % e
        )
        return

    if api_response:
        filtered_projects = [data for data in api_response if data["color"] in colors]
        return filtered_projects


def go_through_by_color(colors=None, expired=False):
    filtered_projects = get_asana_tasks_by_color()

    if not filtered_projects:
        print("No projects found.")
        return

    project_count = len(filtered_projects)

    if project_count == 1:
        print("Found 1 project.")
    else:
        print(f"Found {project_count} projects.")

    if not expired and not src.config.ADMIN_MODE:
        filtered_projects = [
            data
            for data in filtered_projects
            if data["notes"]
            and f"lw {src.config.INITIALS}" not in data["notes"].splitlines()[0].lower()
        ]
        project_count = len(filtered_projects)
        print(
            f"Removed projects with warnings on top. New project count: {project_count}"
        )

    for i, data in enumerate(filtered_projects, 1):
        if not src.config.ADMIN_MODE:
            data["name"] = re.sub(r"\[.*?\]|\{.*?\}|[^\w\s]", "", data["name"])
        data["name"] = re.sub(r"\s+", " ", data["name"]).strip()
        data["messages_sent"] = data["notes"].lower().count(f"lm {src.config.INITIALS}")
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
        hold_match = re.search(r"hold\s+(\d{1,2}/\d{1,2})", data["notes"])
        data["hold"] = hold_match.group(1) if hold_match else None

        if expired:
            data["name"] = re.sub(r"(ASD|ADHD)", "", data["name"])
            data["name"] = re.sub(r"\s+", " ", data["name"]).strip()
            src.utils.get_expired(data)
        else:
            if data["hold"]:
                current_month = datetime.now().month
                year = datetime.now().year
                if current_month in [1, 2] and data["hold"] not in ["01", "02"]:
                    year -= 1
                hold_date = datetime.strptime(f"{data['hold']}/{year}", "%m/%d/%Y")
                if hold_date > datetime.now():
                    print(f"Skipping {data['name']}, on hold until {data['hold']}.")
                    continue
            if not src.config.ADMIN_MODE:
                if data["notes"] and (
                    datetime.now().strftime("%m/%d") in data["notes"].splitlines()[0]
                    or (datetime.now() - timedelta(days=1)).strftime("%m/%d")
                    in data["notes"].splitlines()[0]
                    and "hold" not in data["notes"].splitlines()[0].lower()
                ):
                    print(f"Skipping {data['name']}, already noted today or yesterday.")
                    continue

            src.utils.what_to_do(data, count=[i, project_count], source="colors")

    if sys.platform != "linux":
        input("End of list! You can close this window now.")


def search_by_name(name):
    src.config.get_consts()
    opts = {
        "limit": 100,
        "archived": False,
        "opt_fields": "name,color,permalink_url,notes",
    }
    try:
        print(f"Searching projects for {name}...")

        api_response = list(
            src.config.projects_api_instance.get_projects_for_workspace(
                src.config.WORKSPACE_GID,
                opts,  # pyright: ignore (asana api is strange)
            )
        )

    except ApiException as e:
        print(
            "Exception when calling ProjectsApi->get_projects_for_workspace: %s\n" % e
        )
        return

    if api_response:
        filtered_projects = [
            data for data in api_response if name.lower() in data["name"].lower()
        ]
        project_count = len(filtered_projects)

        correct_project = None

        if project_count == 0:
            input("No projects found.")
        elif project_count == 1:
            print("Found 1 project.")
            correct_project = filtered_projects[0]
        else:
            print(f"Found {project_count} projects.")
            for i, data in enumerate(filtered_projects, 1):
                data["name"] = re.sub(r"\s+", " ", data["name"]).strip()
                src.utils.print_project(data, count=[i, project_count], fields=["name"])
            while True:
                choice = input(
                    f"Enter the number of the correct project (1-{project_count}): "
                )
                try:
                    correct_project = filtered_projects[int(choice) - 1]
                    break
                except (ValueError, IndexError):
                    print("Invalid input.")
        if correct_project:
            print("\n")
            src.utils.what_to_do(correct_project, source="search")


def replace_notes(new_text, project_gid):
    body = {"data": {"notes": new_text}}
    try:
        api_response = src.config.projects_api_instance.update_project(
            body, project_gid, opts={"opt_fields": "name, notes"}
        )
        if isinstance(api_response, dict) and "name" in api_response:
            print(f"Added note to {api_response['name'].strip()}.")
        else:
            print("Added note to project")
    except ApiException as e:
        print("Exception when calling ProjectsApi->update_project:: %s\n" % e)


def change_color(color, project_gid):
    body = {"data": {"color": color}}
    try:
        api_response = src.config.projects_api_instance.update_project(
            body, project_gid, opts={"opt_fields": "name, color"}
        )
        if isinstance(api_response, dict) and "name" in api_response:
            print(f"Changed color of {api_response['name'].strip()} to {color}.")
        else:
            print(f"Changed project color to {color}.")
    except ApiException as e:
        print("Exception when calling ProjectsApi->update_project:: %s\n" % e)
