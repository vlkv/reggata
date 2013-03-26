"""
    A tagging system for managing local files on your computer.
"""

__major__ = 1  # for major interface/format changes
__minor__ = 0  # for minor interface/format changes
__release__ = "0b4"  # for tweaks, bug-fixes, or development
__version__ = "{}.{}.{}".format(__major__, __minor__, __release__)

__author__ = "Vitaly Volkov"
__license__ = "GPL v3+"
__author_email__ = "vitvlkv@gmail.com"
__url__ = "https://github.com/vlkv/reggata/wiki"
__download_url__ = "https://sourceforge.net/projects/reggata/files/"


# import for the launcher file
from reggata.main import main
