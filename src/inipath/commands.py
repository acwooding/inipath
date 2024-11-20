import configparser
from pathlib import Path
from .pathstore import PathStore
from .kvstore import KVStore

import logging
import os
import subprocess
import sys

logger = logging.getLogger()

CONFIG_FILE = "pathstore.ini"
DEFAULT_CONFIG_SECTION = "PROJECT_PATHS"
DEFAULT_BASE_NAME = "project_dir"
DEFAULT_CONFIG_PATHS = {
    DEFAULT_BASE_NAME: "${ini_path}",
    "data_dir": "${DEFAULT_BASE_NAME}/data",
}


def initialize(input_value=None):
    config_path = Path.cwd() / CONFIG_FILE

    if config_path.exists():
        logger.warning("path.ini exists already")
        if input_value is None:
            overwrite_value = input(
                "Would you like to reinitialize (this will overwrite the existing path.ini file)? (y/n) "
            ).lower()
        else:
            overwrite_value = input_value
        if overwrite_value != "y":
            return load()
        else:
            config_path.unlink()

    PathStore(
        DEFAULT_CONFIG_PATHS,
        config_file=config_path,
        config_section=DEFAULT_CONFIG_SECTION,
    )
    return PathStore(config_file=config_path, config_section=DEFAULT_CONFIG_SECTION)


def load(die_on_error=True, kind='PathStore'):
    """
    Load the config file

    kind can be one of PathStore or KVStore
    """
    pathstore = find_pathstore_ini(die_on_error=die_on_error)

    if pathstore is not None:
        logger.debug("Loading path store")
        if kind.lower() == "pathstore":
            config = PathStore(config_file=pathstore, config_section=DEFAULT_CONFIG_SECTION)
        elif kind.lower() == "kvstore":
            config = KVStore(config_file=pathstore, config_section=DEFAULT_CONFIG_SECTION)
        else:
            logger.error(f"Unrecognized kind: {kind}, must be one of PathStore or KVStore")
            sys.exit(1)
    else:
        config = None

    return config


def add(name, path, parent=None):
    config = load()
    print(name, path, parent)
    if parent is not None:
        config[name] = "${" + parent + "}/" + path
    elif path[0] == "/":
        config[name] = path
    else:
        config[name] = "${" + DEFAULT_BASE_NAME + "}/" + path

    print(f"Added path: {name} -> {config[name]}")


def remove(name):
    config = load()
    try:
        config.get(name)
        del config[name]
        print(f"Removed path: {name}")
    except configparser.NoOptionError:
        print(f"No path named {name} was found")

def list_paths():
    config = load()
    print("Stored paths:")
    for name, path in config.items():
        print(f"    {name} -> {path}")

def edit_config():
    config = load()
    print(config)
    filename = config["project_dir"] / CONFIG_FILE
    open_file_in_editor(filename)


def rename(old_name, new_name):
    print(old_name, new_name)
    config = load(kind="PathStore")
    old_path = config.get_raw(old_name)

    if old_path is not None:
        config[new_name] = old_path
        del config[old_name]
        print(f"Renamed path '{old_name}' to '{new_name}'")
    else:
        print(f"Path '{old_name}' not found")


############################################
#
# Helper Functions
#
############################################


def find_pathstore_ini(die_on_error=True):
    """
    Locate the pathstore ini file.

    Searches current and all parent directories.

    die_on_error: Boolean
        if ops_dir is not found:
            if True, exit with error
            if False, return None
    """
    logger.debug("Searching for pathstore ini.")
    config_path = find_upwards(Path.cwd(), CONFIG_FILE)
    if config_path is None:
        message = "No path ini file found (here or in parent directories)."
        if die_on_error:
            logger.error(message)
        else:
            logger.warning(message)
        logger.info("To initialize an inipath for this directory:")
        logger.info(">>> inipath init")

        if die_on_error:
            sys.exit(1)
    return config_path


def find_upwards(cwd, filename):
    """
    Search recursively for a file/directory.

    Start searching in current directory, then upwards through all parents,
    stopping at the root directory.

    Arguments:
    ---------
    cwd :: string, current working directory
    filename :: string, the filename or directory to look for.

    Returns
    -------
    pathlib.Path, the location of the first file found or
    None, if none was found
    """
    if cwd == cwd.parent or cwd == Path(cwd.root):
        return None

    fullpath = cwd / filename

    try:
        return fullpath if fullpath.exists() else find_upwards(cwd.parent, filename)
    except RecursionError:
        return None


def open_file_in_editor(filename, editor=None):
    """
    Open a file in the default text editor based on the platform.

    Arguments:
    - filename (str): The name of the file to open in the editor.
    - editor (str): The name of an editor to open. If set, this takes precedence over any environment variables.

    Raises:
    - subprocess.CalledProcessError: If opening the file in the editor fails.

    Notes:
    - On macOS and Linux, the function uses the 'VISUAL' environment variable to determine the default text editor.
      If 'VISUAL is not set, it falls back to 'EDITOR' and then 'vi'.
    - On Windows, the function uses the 'EDITOR' environment variable if set. If 'EDITOR' is not set, it falls back
      to 'notepad.exe' as the default text editor.
    - For unsupported platforms, the function displays a message indicating that opening the file in the editor is not supported.

    Here is a reference: https://github.com/pallets/click/blob/2cfb61ebba129dacc902dde94fff8bb16619cf12/src/click/_termui_impl.py#L454
    """
    path = Path(filename).resolve()

    if editor is None:
        if sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
            editor = os.environ.get("VISUAL", None)
            if editor is None:
                if sys.platform.startswith("darwin"):
                    # Use 'vim' instead of 'vi' for proper exit codes if no changes are made
                    editor = os.environ.get("EDITOR", "vim")
                else:
                    editor = os.environ.get(
                        "EDITOR", "vi"
                    )  # Use 'vi' if EDITOR is not set
        elif sys.platform.startswith("win"):
            editor = os.environ.get(
                "EDITOR", "notepad"
            )  # Use 'notepad' if EDITOR is not set
        else:
            logger.error(
                "Unsupported platform: Cannot open file in editor. Please file an issue to have this fixed."
            )
    try:
        subprocess.run([editor, path], check=True)
    except subprocess.CalledProcessError as exception:
        logger.error(f"Failed to open the file in the editor {editor}: {exception}")
