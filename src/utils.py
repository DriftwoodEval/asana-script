import os
import re
from datetime import datetime, timedelta

from colored import fg, stylize

import src.api
import src.config
import src.utils


def add_to_notes(new_text, current_notes, project_gid):
    today_str = datetime.now().strftime("%m/%d")
    new_text = today_str + " " + new_text
    if src.config.ADMIN_MODE:
        new_text += " ///" + src.config.INITIALS
    src.api.replace_notes(new_text + "\n" + current_notes, project_gid)


def replace_link(body, link):
    return body.replace(link, link + " - DONE", 1)


def multiple_questionnaires(data):
    sr = input("Self-Report Link: ")
    pg = input("Parent/Guardian Link: ")
    message = f"{sr} - Self-Report\n{pg} - Parent/Guardian"
    add_to_notes(
        message,
        data["notes"],
        data["gid"],
    )
    print(f"Send this message to {data['name']}:\n{message}")


def generate_warning(data):
    COMPANY_NAME = os.getenv("COMPANY_NAME")
    deadline = (datetime.now() + timedelta(days=7)).strftime("%m/%d")
    message = f"This is {COMPANY_NAME}. This will be our last attempt to reach you. We have left you multiple messages. You have outstanding paperwork to do so that we may begin the evaluation process. If we don't hear from you by {deadline}, we will close this referral. Thank you."
    add_to_notes(
        "lw " + src.config.INITIALS + " " + deadline,
        data["notes"],
        data["gid"],
    )
    print(f"Send this message to {data['name']}:\n{message}")


def mark_links(data, allowed_domains, links):
    if len(links) == 1:
        new_body = replace_link(data["notes"], links[0])
        src.api.replace_notes(new_body, data["gid"])
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
                src.api.replace_notes(new_body, data["gid"])
                break
            else:
                try:
                    choices = list(map(int, choice.split()))
                    if all(1 <= c <= len(links) for c in choices):
                        new_body = data["notes"]
                        for choice in choices:
                            chosen_link = links[choice - 1]
                            new_body = replace_link(new_body, chosen_link)
                        src.api.replace_notes(new_body, data["gid"])
                        break
                    else:
                        print("Invalid choice.")
                except ValueError:
                    print("Invalid input.")
    new_links = [
        link
        for link in re.findall(r"(https?://\S+[\s\S]*?)(?=\n|$)", new_body)
        if " - DONE" not in link and any(domain in link for domain in allowed_domains)
    ]
    if not new_links:
        src.api.change_color("light-purple", data["gid"])


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


def what_to_do(data):
    body = data["notes"]
    if not src.config.ADMIN_MODE:
        allowed_domains = os.getenv("Q_LINKS").split(",")
        links = [
            link
            for link in re.findall(r"(https?://\S+[\s\S]*?)(?=\n|$)", body)
            if " - DONE" not in link
            and any(domain in link for domain in allowed_domains)
        ]

    print("a <note> ".ljust(10) + "Add a note with the date")
    if not src.config.ADMIN_MODE:
        print("qs ".ljust(10) + "Add the self-report link and the parent/guardian link")
        if len(links) > 1:
            print("d ".ljust(10) + "Mark links as done")
        elif len(links) == 1:
            print("d ".ljust(10) + "Mark link as done")
        print("m ".ljust(10) + "Message sent")
        print("w ".ljust(10) + "Generate warning and mark as sent")
    print("s ".ljust(10) + "Skip")

    if not src.config.ADMIN_MODE:
        messages_left = 3 - data["messages_sent_top"]
        if messages_left > 0:
            print(
                stylize(
                    f"{messages_left} {'message' if messages_left == 1 else 'messages'} left before warning.",
                    fg(
                        "green"
                        if messages_left > 2
                        else "yellow"
                        if messages_left == 2
                        else "orange_1"
                    ),
                )
            )
        elif messages_left == 0 and not data["warning_on_top"]:
            print(stylize("It's time to send the final warning.", fg("red")))

    command = input("What's new? ")

    if command.startswith("a "):
        additional_text = command[2:].strip()
        add_to_notes(additional_text, data["notes"], data["gid"])
        if src.config.ADMIN_MODE:
            src.api.change_color("light-purple", data["gid"])
    elif command == "s":
        pass
    elif not src.config.ADMIN_MODE:
        if command == "qs":
            multiple_questionnaires(data)
        elif command == "m":
            add_to_notes(
                "lm " + src.config.INITIALS,
                data["notes"],
                data["gid"],
            )
        elif command == "w":
            generate_warning(data)
        elif command == "d" and links:
            mark_links(data, allowed_domains, links)
        else:
            print("Invalid command.")
            what_to_do(data)
