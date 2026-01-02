"""
ANSI color codes for terminal output.
Author: IFF-3-2 Aleksandravicius Linas
"""


class Color:
    """ANSI escape codes for colored terminal output."""
    # pylint: disable=too-few-public-methods

    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"
