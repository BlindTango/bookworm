# coding: utf-8

import logging
import platform
import winpaths
import bookworm
from pathlib import Path
from platform_utils import paths as paths_
from functools import wraps
from bookworm import app


log = logging.getLogger("bookworm.paths")


DATA_PATH_DEBUG = Path(bookworm.__path__[0]).parent / ".appdata"


def merge_paths(func):
    @wraps(func)
    def merge_paths_wrapper(*a):
        return func().joinpath(*a)

    return merge_paths_wrapper


@merge_paths
def data_path():
    if not app.is_frozen and app.debug:
        data_path = DATA_PATH_DEBUG
    else:
        data_path = Path(winpaths.get_appdata()) / app.display_name
    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)
    return data_path


@merge_paths
def app_path():
    return Path(paths_.app_path())


@merge_paths
def config_path():
    path = data_path("config")
    if not path.exists():
        log.debug("%s path does not exist, creating..." % (path,))
        path.mkdir(parents=True, exist_ok=True)
    return path


@merge_paths
def logs_path():
    path = data_path("logs")
    if not path.exists():
        log.debug("%s path does not exist, creating..." % (path,))
        path.mkdir(parents=True, exist_ok=True)
    return path


@merge_paths
def locale_path():
    return app_path("resources", "locales")


@merge_paths
def db_path():
    path = data_path("database")
    if not path.exists():
        log.debug("%s path does not exist, creating..." % (path,))
        path.mkdir(parents=True, exist_ok=True)
    return path


@merge_paths
def docs_path():
    if not app.is_frozen:
        parent = Path(DATA_PATH_DEBUG).parent
        path = parent / "docs"
    else:
        path = app_path("resources", "docs")
    if not path.exists():
        log.warning(f"Documentation files was not found in {path}. Folder not Found.")
    return path


@merge_paths
def home_data_path():
    if app.is_frozen:
        path = Path.home() / f".{app.name}"
    else:
        path = DATA_PATH_DEBUG / "home_data"
    if not path.exists():
        log.debug("%s path does not exist, creating..." % (path,))
        path.mkdir(parents=True, exist_ok=True)
    return path
