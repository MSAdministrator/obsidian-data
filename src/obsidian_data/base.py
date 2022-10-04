"""obsidian_data.base.

This Base class inherits from our LoggingBase metaclass and gives us
shared logging across any class inheriting from Base.
"""
import os

from .utils.logger import LoggingBase


class Base(metaclass=LoggingBase):
    """Base class to all other classes within this project."""
    
    def get_abs_path(self, value: str) -> str:
        """Formats and returns the absolute path for a path value.

        Args:
            value (str): A path string in many different accepted formats.

        Returns:
            str: The absolute path of the provided string.
        """
        return os.path.abspath(os.path.expanduser(os.path.expandvars(value)))
