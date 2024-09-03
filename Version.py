import tkinter
import pandas
import hashlib
import datetime
import matplotlib
import os
import logging
import sklearn
import numpy
import decimal
import base64
import tkcalendar
import locale
import json
import copy
import sys

# Function to get the version of a module
def get_version(module):
    try:
        return module.__version__
    except AttributeError:
        return "Version not found"

# Collect versions
versions = {
    "Python": sys.version,
    "tkinter": tkinter.TkVersion,
    "pandas": pandas.__version__,
    "hashlib": hashlib.__doc__.split()[1],
    "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "matplotlib": matplotlib.__version__,
    "os": os.__doc__.split()[1],
    "logging": logging.__doc__.split()[1],
    "sklearn": sklearn.__version__,
    "numpy": numpy.__version__,
    "decimal": decimal.__doc__.split()[1],
    "base64": base64.__doc__.split()[1],
    "tkcalendar": tkcalendar.__version__,
    "locale": locale.__doc__.split()[1],
    "json": json.__doc__.split()[1],
    "copy": copy.__doc__.split()[1]
}

# Write versions to a text file
with open("Version.txt", "w") as file:
    for lib, version in versions.items():
        file.write(f"{lib}: {version}\n")

print("Library versions have been written to Version.txt")
