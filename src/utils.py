import os
import re
import sys
from datetime import datetime, timedelta

from colored import Fore, Style, fg, stylize

import src.api
import src.config
import src.utils
import src.websites


def print_project(
    data: dict,
    count: list[int] | None = None,
    fields: list[str] = ["name", "link", "notes"],
):
    print_str = []
    if "name" in fields:
        name_str = f"Name: {data['name']}"
        if sys.platform == "linux":
            name_str = f"{Fore.cyan}{Style.bold}Name:{Style.reset} {data['name']}"
        print_str.append(name_str)

    if "link" in fields:
        link_str = f"Link: {data['permalink_url']}"
        if sys.platform == "linux":
            link_str = (
                f"{Fore.magenta}{Style.bold}Link:{Style.reset} {data['permalink_url']}"
            )
        print_str.append(link_str)

    if "notes" in fields:
        notes_str = f"Notes: {data['notes'].strip()}"
        if sys.platform == "linux":
            notes_str = (
                f"{Fore.blue}{Style.bold}Notes:{Style.reset} {data['notes'].strip()}"
            )
        print_str.append(notes_str)

    count_str = f"\n({count[0]}/{count[1]})\n" if count else ""
    print(f"{count_str}" + "\n".join(print_str))


def add_to_notes(new_text, current_notes, project_gid, with_initials=False):
    today_str = datetime.now().strftime("%m/%d")
    new_text = today_str + " " + str(new_text)
    if with_initials:
        new_text += f" {'///' if src.config.ADMIN_MODE else ''}{src.config.INITIALS}"
    src.api.replace_notes(new_text + "\n" + current_notes, project_gid)


def replace_link(body, link):
    return body.replace(link, link + " - DONE", 1)


def multiple_questionnaires(data):
    sr = input("Self-Report Link: ")
    pg = input("Parent/Guardian Link: ")
    message = f"{sr} - Self-Report - {src.config.INITIALS}\n{pg} - Parent/Guardian - {src.config.INITIALS}"
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


def mark_links(data, allowed_domains, links: list[str]):
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
        return True
    return new_body


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


def mark_done_links():
    src.config.get_consts()
    projects = src.api.get_asana_tasks_by_color()
    for project in projects:  # pyright: ignore
        links = [
            link
            for link in re.findall(r"(https?://\S+[\s\S]*?)(?=\n|$)", project["notes"])
            if " - DONE" not in link
            and any(domain in link for domain in src.config.allowed_domains)
        ]
        for link in links:
            name = project["name"].strip()
            done = src.websites.check_q_done(link, name)
            if done:
                mark_links(project, src.config.allowed_domains, [link])


def what_to_do(
    data: dict,
    count: list[int] | None = None,
    fields: list[str] = ["name", "link", "notes"],
    source: str | None = None,
):
    body = data["notes"]
    allowed_domains = ["mhs.com", "pearsonassessments.com"]
    links = []
    if not src.config.ADMIN_MODE:
        links = [
            link
            for link in re.findall(r"(https?://\S+[\s\S]*?)(?=\n|$)", body)
            if " - DONE" not in link
            and any(domain in link for domain in allowed_domains)
        ]
        for link in links:
            done = src.websites.check_q_done(link, data["name"])
            if done:
                no_more_links = mark_links(data, allowed_domains, [link])
                if no_more_links is True:
                    return
                else:
                    data["notes"] = no_more_links

    print_project(data, count, fields)
    print("a <note> ".ljust(20) + "Add a note with the date")
    print(
        "h <days or date> ".ljust(20)
        + "Add a hold for <days> or until <date> in MM/DD format"
    )
    if not src.config.ADMIN_MODE:
        print("qs ".ljust(20) + "Add the self-report link and the parent/guardian link")
        print("m ".ljust(20) + "Message sent")
        print("w ".ljust(20) + "Generate warning and mark as sent")
    print("s ".ljust(20) + "Skip")

    if not src.config.ADMIN_MODE and data.get("messages_sent_top"):
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
        add_to_notes(additional_text, data["notes"], data["gid"], True)
        if src.config.ADMIN_MODE:
            if source == "search":
                print("Select a color:")

                current_color = data["color"]
                if current_color == "light-purple":
                    current_color = "purple"
                elif current_color == "dark-pink":
                    current_color = "pink"
                elif current_color == "light-blue":
                    current_color = "blue"
                elif current_color == "dark-teal":
                    current_color = "light blue"

                print(f"<Enter> - No change (currently {current_color})")
                print("1 - Purple")
                print("2 - Pink")
                color = input("Color to change to: ")

                if color == "1":
                    src.api.change_color("light-purple", data["gid"])
                elif color == "2":
                    src.api.change_color("dark-pink", data["gid"])
            else:
                src.api.change_color("light-purple", data["gid"])
    elif command.startswith("h "):
        hold_date = None
        additional_text = command[2:].strip()
        if "/" in additional_text:
            hold_date = additional_text
        else:
            try:
                days = int(additional_text)
                hold_date = (datetime.now() + timedelta(days=days)).strftime("%m/%d")
            except ValueError:
                print("Invalid input.")
                what_to_do(data)
        if hold_date is not None:
            add_to_notes("hold " + hold_date, data["notes"], data["gid"], True)
    elif command == "s":
        pass
    elif not src.config.ADMIN_MODE:
        if command == "qs":
            multiple_questionnaires(data)
        elif command == "m":
            add_to_notes("lm", data["notes"], data["gid"], True)
        elif command == "w":
            generate_warning(data)
        elif command == "d" and links:
            mark_links(data, allowed_domains, links)
        else:
            print("Invalid command.")
            what_to_do(data)
