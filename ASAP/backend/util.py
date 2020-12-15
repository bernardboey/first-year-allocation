def input_yes_no(message, /, *, full_message=None, true_input=("y", "Y"), false_input=('n', "N"),
                 try_again_text="Oops! Please enter 'y' or 'n': "):
    """Gets a boolean user input (typically 'y' or 'n').

    Repeats the prompt until a valid input is received.

    Args:
        message: (positional-only) A string representing the message shown to the user when asking for input.
            This will be appended by the following string: "\nEnter 'y' or 'n': "
        full_message: (optional, keyword-only) A string representing the full message shown to the user
            when asking for input.
        true_input: (optional, keyword-only) A tuple/list of strings that are allowed as the true/"yes" input.
        false_input: (optional, keyword-only) A tuple/list of strings that are allowed as the false/"no" input.
        try_again_text: (optional, keyword-only) The text to be shown to the user after failed input.

    Returns:
        A boolean indicating whether the user indicated yes or no.
    """
    if full_message:
        response = input(full_message)
    else:
        response = input(message + "\nEnter 'y' or 'n': ")
    while True:
        if response in true_input:
            return True
        elif response in false_input:
            return False
        response = input(try_again_text)