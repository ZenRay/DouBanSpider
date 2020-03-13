#-*-coding:utf-8 -*-
"""
Customize exceptions class
"""

# Configuration exceptions
class InvalidateConfigure(Exception):
    """Indicate a invalidate configuration"""
    pass


class InappropriateArgument(Exception):
    """Argument is in appropriate"""
    pass


class LostArgument(Exception):
    """Argument is missing"""
    pass


class ConnectionError(Exception):
    """Can't Connect Target Server"""
    pass