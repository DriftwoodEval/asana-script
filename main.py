import argparse

import keyring

import src.api
import src.config
import src.utils

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Retrieve Asana tasks based on color or expiration status."
    )
    parser.add_argument("-s", "--search", help="Search by name")
    parser.add_argument(
        "-c",
        "--color",
        help="The color to filter by, can also be set with environment variable ASANA_COLOR",
    )
    parser.add_argument(
        "-e",
        "--expired",
        action="store_true",
        help="Get expired tasks" if not src.config.ADMIN_MODE else argparse.SUPPRESS,
    )
    parser.add_argument(
        "-r",
        "--reset",
        nargs="?",
        const="all",
        help=argparse.SUPPRESS
        if not any(
            keyring.get_password("asana", key)
            for key in ["token", "initials"]
        )
        else "Reset stored token and workspace. Choose 'token', 'initials', or leave blank for all",
    )
    args = parser.parse_args()

    if args.expired:
        src.api.get_asana_tasks_by_color(expired=True)
    elif args.reset:
        src.config.reset(args.reset)
    elif args.color:
        src.api.get_asana_tasks_by_color(colors=[args.color])
    elif args.search:
        src.api.search_by_name(args.search)
    else:
        if src.config.ADMIN_MODE:
            print("s <term>".ljust(10) + "Search by name")
            print("c ".ljust(10) + "Go through color(s)")
            choice = input("Choose: ")
            if choice.startswith("s "):
                src.api.search_by_name(choice[2:].strip())
            elif choice == "c":
                src.api.get_asana_tasks_by_color(["light-blue"])
        else:
            src.api.get_asana_tasks_by_color()
