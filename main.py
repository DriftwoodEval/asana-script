import argparse
import os
import re
from datetime import datetime, timedelta

import asana
import colored
from asana.rest import ApiException
from dotenv import load_dotenv

load_dotenv()

configuration = asana.Configuration()
configuration.access_token = os.getenv("ASANA_TOKEN")
api_client = asana.ApiClient(configuration)

projects_api_instance = asana.ProjectsApi(api_client)
workspace_gid = os.getenv("ASANA_WORKSPACE_GID")
asana_color = os.getenv("ASANA_COLOR")
initials = os.getenv("USER_INITIALS").lower()
company_name = os.getenv("COMPANY_NAME")


def get_asana_tasks_by_color(color=asana_color, expired=False):
    opts = {
        "limit": 100,
        "archived": False,
        "opt_fields": "name,color,permalink_url,notes",
    }
    try:
        api_response = projects_api_instance.get_projects_for_workspace(
            workspace_gid, opts
        )
        for data in api_response:
            if data["color"] == color:
                data["name"] = re.sub(r"\[.*?\]|\{.*?\}|[^\w\s]", "", data["name"])
                data["name"] = re.sub(r"\s+", " ", data["name"]).strip()
                data["messages_sent"] = data["notes"].lower().count(f"lm {initials}")
                data["warnings_sent"] = data["notes"].lower().count(f"lw {initials}")
                data["messages_sent_top"] = (
                    sum(
                        1
                        for line in data["notes"].splitlines()[:3]
                        if f"lm {initials}" in line.lower()
                    )
                    if f"lm {initials}" in data["notes"].splitlines()[0].lower()
                    else 0
                )
                data["warning_on_top"] = (
                    f"lw {initials}" in data["notes"].splitlines()[0].lower()
                    if data["notes"]
                    else False
                )

                if expired:
                    data["name"] = re.sub(r"(ASD|ADHD)", "", data["name"])
                    data["name"] = re.sub(r"\s+", " ", data["name"]).strip()
                    get_expired(data)
                else:
                    if data["warning_on_top"]:
                        print(f"Skipping {data['name']}, already sent final warning.")
                        continue
                    if (
                        datetime.now().strftime("%m/%d")
                        in data["notes"].splitlines()[0]
                    ):
                        print(f"Skipping {data['name']}, already noted today.")
                        continue
                    print(
                        f"\nName: {data['name']}\nLink: {data['permalink_url']}\nNotes: {data['notes'].strip()}"
                    )
                    what_to_do(data)

    except ApiException as e:
        print(
            "Exception when calling ProjectsApi->get_projects_for_workspace: %s\n" % e
        )


def replace_notes(new_text, project_gid):
    body = {"data": {"notes": new_text}}
    try:
        api_response = projects_api_instance.update_project(
            body, project_gid, opts={"opt_fields": "name, notes"}
        )
        print(f"Added note to {api_response['name']}.")
    except ApiException as e:
        print("Exception when calling ProjectsApi->update_project:: %s\n" % e)


def add_to_notes(new_text, current_notes, project_gid):
    today_str = datetime.now().strftime("%m/%d")
    replace_notes(today_str + " " + new_text + "\n" + current_notes, project_gid)


def replace_link(body, link):
    return body.replace(link, link + " - DONE", 1)


def change_color(color, project_gid):
    body = {"data": {"color": color}}
    try:
        api_response = projects_api_instance.update_project(
            body, project_gid, opts={"opt_fields": "name, color"}
        )
        print(f"Changed color of {api_response['name']} to {color}.")
    except ApiException as e:
        print("Exception when calling ProjectsApi->update_project:: %s\n" % e)


def what_to_do(data):
    body = data["notes"]
    allowed_domains = os.getenv("Q_LINKS").split(",")
    links = [
        link
        for link in re.findall(r"(https?://\S+[\s\S]*?)(?=\n|$)", body)
        if " - DONE" not in link and any(domain in link for domain in allowed_domains)
    ]

    print("a <note> ".ljust(10) + "Add a note with the date")
    print("qs ".ljust(10) + "Add the self-report link and the parent/guardian link")
    if len(links) > 1:
        print("d ".ljust(10) + "Mark links as done")
    elif len(links) == 1:
        print("d ".ljust(10) + "Mark link as done")
    print("m ".ljust(10) + "Message sent")
    print("w ".ljust(10) + "Generate warning and mark as sent")
    print("s ".ljust(10) + "Skip")

    messages_left = 3 - data["messages_sent_top"]
    if messages_left > 0:
        if messages_left == 3:
            print(
                colored.stylize(
                    f"{messages_left} messages left before warning.",
                    colored.fg("green"),
                )
            )
        elif messages_left == 2:
            print(
                colored.stylize(
                    f"{messages_left} messages left before warning.",
                    colored.fg("yellow"),
                )
            )
        elif messages_left == 1 or messages_left == 0:
            print(
                colored.stylize(
                    f"{messages_left} message left before warning.",
                    colored.fg("orange_1"),
                )
            )
    elif messages_left == 0 and not data["warning_on_top"]:
        print(
            colored.stylize("It's time to send the final warning.", colored.fg("red"))
        )

    command = input("What's new? ")

    if command.startswith("a "):
        additional_text = command[2:].strip()
        add_to_notes(additional_text, data["notes"], data["gid"])
    elif command == "qs":
        sr = input("Self-Report Link: ")
        pg = input("Parent/Guardian Link: ")
        message = f"{sr} - Self-Report\n{pg} - Parent/Guardian"
        add_to_notes(
            message,
            data["notes"],
            data["gid"],
        )
        print(f"Send this message to {data['name']}:\n{message}")
    elif command == "m":
        add_to_notes(
            "lm " + initials,
            data["notes"],
            data["gid"],
        )
    elif command == "w":
        deadline = (datetime.now() + timedelta(days=7)).strftime("%m/%d")
        message = f"This is {company_name}. This will be our last attempt to reach you. We have left you multiple messages. You have outstanding paperwork to do so that we may begin the evaluation process. If we don't hear from you by {deadline}, we will close this referral. Thank you."
        add_to_notes(
            "lw " + initials + " " + deadline,
            data["notes"],
            data["gid"],
        )
        print(f"Send this message to {data['name']}:\n{message}")
    elif command == "d":
        if links:
            if len(links) == 1:
                new_body = replace_link(data["notes"], links[0])
                replace_notes(new_body, data["gid"])
            else:
                print("Which link to mark as completed?")
                for i, link in enumerate(links):
                    print(f"{i+1}. {link}")
                while True:
                    choice = input(
                        "Enter the numbers of the links to mark (space separated), or 'all' to mark all: "
                    )
                    if choice.lower() == "all":
                        new_body = data["notes"]
                        for link in links:
                            new_body = replace_link(new_body, link)
                        replace_notes(new_body, data["gid"])
                        break
                    else:
                        try:
                            choices = list(map(int, choice.split()))
                            if all(1 <= c <= len(links) for c in choices):
                                new_body = data["notes"]
                                for choice in choices:
                                    chosen_link = links[choice - 1]
                                    new_body = replace_link(new_body, chosen_link)
                                replace_notes(new_body, data["gid"])
                                break
                            else:
                                print("Invalid choice.")
                        except ValueError:
                            print("Invalid input.")
            new_links = [
                link
                for link in re.findall(r"(https?://\S+[\s\S]*?)(?=\n|$)", new_body)
                if " - DONE" not in link
                and any(domain in link for domain in allowed_domains)
            ]
            if not new_links:
                change_color("light-purple", data["gid"])
        else:
            print("No links found.")
            what_to_do(data)

    elif command == "s":
        pass
    else:
        print("Invalid command.")
        what_to_do(data)


def get_expired(data):
    if data["warning_on_top"]:
        first_line = data["notes"].splitlines()[0]
        last_word = first_line.split()[-1]
        try:
            current_month = datetime.now().month
            year = datetime.now().year
            if current_month in [1, 2] and last_word not in ["01", "02"]:
                year -= 1
            last_date = datetime.strptime(f"{last_word}/{year}", "%m/%d/%Y")
            if last_date < datetime.now():
                print(f"{data["name"]} - {last_word}")
                return True
        except ValueError:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Retrieve Asana tasks based on color or expiration status."
    )
    parser.add_argument(
        "-c",
        "--color",
        help="The color to filter by, can also be set with environment variable ASANA_COLOR",
    )
    parser.add_argument(
        "-e", "--expired", action="store_true", help="Get expired tasks"
    )
    args = parser.parse_args()

    if args.expired:
        get_asana_tasks_by_color(expired=True)
    elif args.color:
        get_asana_tasks_by_color(color=args.color)
    else:
        get_asana_tasks_by_color()
