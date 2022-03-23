from get_commands import get_all_commands
from commands import *


def parse_command(text):
    all_commands = get_all_commands()
    command, *args = text.lower().split()

    for db_command in all_commands:
        if command == db_command[0]:
            args = [f"'{arg}'" for arg in args]
            return eval(f"{db_command[3]}({', '.join(args)})")


if __name__ == "__main__":
    print(parse_command("help"))