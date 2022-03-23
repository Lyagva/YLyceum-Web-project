def command_help(*args):
    from get_commands import get_all_commands

    return_data = "name \t syntax \t description\n"

    for command in get_all_commands():
        return_data += f"{command[0]} \t {command[1]} \t {command[2]}\n"

    return return_data

def command_debug(*args):
    return f"DEBUG MESSAGE"

