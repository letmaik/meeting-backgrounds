import os
import sys
import json
import urllib.request
import platform
import subprocess
import sqlite3
from functools import lru_cache as cached
import argparse

try:
    from typing import TypedDict, Dict, List

    class App(TypedDict):
        bg_dir: Dict[str, str]

    class BackgroundCollection(TypedDict):
        title: str
        url: str
        image_urls: List[str]

    Backgrounds = Dict[str, BackgroundCollection]
    Apps = Dict[str, App]
except ImportError:
    pass

this_dir = os.path.dirname(__file__)

with open(os.path.join(this_dir, "apps.json")) as f:
    apps = json.load(f)  # type: Apps

with open(os.path.join(this_dir, "backgrounds.json")) as f:
    backgrounds = json.load(f)  # type: Backgrounds


def cli_list(args):
    print()
    if args.markdown:
        print("Command Line | Title | Backgrounds")
        print("-------------|-------|------------")
    for bg_name, bg_details in backgrounds.items():
        if args.markdown:
            print(f'`--bg {bg_name}` | [{bg_details["title"]}]({bg_details["url"]}) | {len(bg_details["image_urls"])}')
        else:
            print(f"Name: {bg_name}")
            print(f'Title: {bg_details["title"]}')
            print(f'Website: {bg_details["url"]}')
            print(f'Backgrounds: {len(bg_details["image_urls"])}')
            downloaded = []
            for app_name in apps:
                bg_dir = get_bg_dir(app_name)
                paths = (
                    os.path.join(bg_dir, get_bg_filename(bg_name, url))
                    for url in bg_details["image_urls"]
                )
                if any(os.path.exists(path) for path in paths):
                    downloaded.append(app_name)
                    continue
            if downloaded:
                print(f'Downloaded: yes ({", ".join(downloaded)})')
            else:
                print("Downloaded: no")
            print()


def cli_download(args):
    for app_name in args.app:
        bg_dir = get_bg_dir(app_name)
        if not os.path.exists(bg_dir):
            # Teams may not have the "Uploads" subfolder yet.
            os.mkdir(bg_dir)

    count = 0
    for bg_name in args.bg:
        bg = backgrounds[bg_name]
        for url in bg["image_urls"]:
            target_paths = {}
            for app_name in args.app:
                bg_dir = get_bg_dir(app_name)
                filename = get_bg_filename(bg_name, url)
                path = os.path.join(bg_dir, filename)
                target_paths[app_name] = path
            if not args.force and all(os.path.exists(path) for path in target_paths.values()):
                print(f"Skipping {url}, already downloaded")
                continue
            print(f"Downloading {url}")
            request = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0"
            })
            with urllib.request.urlopen(request) as r:
                img = r.read()
            for app_name, path in target_paths.items():
                print(f"Saving to {path}")
                with open(path, "wb") as f:
                    f.write(img)
                zoom_db_path = get_zoom_db_path(app_name)
                if zoom_db_path is not None:
                    print(f"Updating {zoom_db_path}")
                    update_zoom_db(zoom_db_path, path, action='add')
            count += 1
    print(f"{count} backgrounds downloaded.")


def cli_open(args):
    bg_dir = get_bg_dir(args.app)
    if not os.path.exists(bg_dir):
        print(f"Folder does not exist: {bg_dir}")
        sys.exit(1)
    if "zoom_db" in apps[args.app]:
        print("WARNING: Do not add/remove images directly. "
              "Zoom stores image metadata in a database which must be kept in sync.")
    open_folder(bg_dir)


def cli_remove(args):
    count = 0
    for app_name in args.app:
        bg_dir = get_bg_dir(app_name)
        zoom_db_path = get_zoom_db_path(app_name)
        for bg_name in args.bg:
            bg = backgrounds[bg_name]
            for url in bg["image_urls"]:
                filename = get_bg_filename(bg_name, url)
                path = os.path.join(bg_dir, filename)
                if os.path.exists(path):
                    print(f"Removing {path}")
                    if zoom_db_path is not None:
                        print(f"Updating {zoom_db_path}")
                        update_zoom_db(zoom_db_path, path, action='remove')
                    os.remove(path)
                    # Thumbs are automatically created by the meeting app.
                    path_thumb = get_bg_thumb_path(app_name, bg_name, url)
                    if path_thumb is not None and os.path.exists(path_thumb):
                        print(f"Removing {path_thumb}")
                        os.remove(path_thumb)
                    count += 1
    print(f"{count} backgrounds removed.")


@cached()
def get_bg_dir(app_name: str) -> str:
    app = apps[app_name]
    # Note that only the parent folder must exist.
    # See `cli_download()` for creation of the subfolder if necessary.
    bg_dir = get_platform_path(app["bg_dir"], is_file=False)
    return bg_dir


def get_bg_filename(bg_name: str, url: str) -> str:
    filename = f"{bg_name}_{os.path.basename(url)}"
    return filename


def get_bg_thumb_path(app_name: str, bg_name: str, url: str):
    bg_dir = get_bg_dir(app_name)
    filename = get_bg_filename(bg_name, url)
    app = apps[app_name]
    thumb_path = app.get("bg_path_pattern")  # type: str
    if thumb_path is None:
        return None
    thumb_path = thumb_path.replace("${BG_DIR}", bg_dir)
    stem, ext = os.path.splitext(filename)
    ext = ext[1:]
    thumb_path = thumb_path.replace("${STEM}", stem)
    thumb_path = thumb_path.replace("${EXT}", ext)
    return thumb_path


@cached()
def get_zoom_db_path(app_name):
    app = apps[app_name]
    db = app.get("zoom_db")
    if db is None:
        return None
    db_path = get_platform_path(db, is_file=True)
    return db_path


def update_zoom_db(zoom_db_path: str, bg_path: str, action: str):
    conn = sqlite3.connect(zoom_db_path, isolation_level="EXCLUSIVE")
    c = conn.cursor()
    bg_path_norm = os.path.normpath(bg_path)
    if is_wsl():
        bg_path_norm = subprocess.check_output(["wslpath", "-w", bg_path_norm]).decode("utf-8").strip()
    if action == "add":
        filename = os.path.basename(bg_path)
        stem, _ = os.path.splitext(filename)
        c.execute("INSERT INTO zoom_conf_video_background_a (path, name, type, customIndex, thumbPath) "
                  "VALUES (?, ?, 1, 100, '')", (bg_path_norm, stem))
    elif action == "remove":
        c.execute("DELETE FROM zoom_conf_video_background_a WHERE path == ?", (bg_path_norm,))
    else:
        assert False
    conn.commit()
    conn.close()


def open_folder(path):
    # https://stackoverflow.com/a/16204023
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        try:
            subprocess.Popen(["xdg-open", path])
        except FileNotFoundError:
            if "WSL_DISTRO_NAME" not in os.environ:
                raise
            path = subprocess.check_output(["wslpath", "-w", path]).decode("utf-8").strip()
            subprocess.Popen(["explorer.exe", path])


def get_platform_path(d: dict, is_file: bool) -> str:
    unsupported_os = True
    paths_tried = []
    path = d.get(platform.system())
    if path is not None:
        unsupported_os = False
        path = os.path.expandvars(path)
        paths_tried.append(path)
        if (is_file and not os.path.exists(path)) or \
           (not is_file and not os.path.exists(os.path.join(path, os.pardir))):
            path = None
    if path is None and is_wsl():
        path = d.get('Windows')
        if path is not None:
            unsupported_os = False
            path = os.path.expandvars(path)
            paths_tried.append(path)
            if (is_file and not os.path.exists(path)) or \
               (not is_file and not os.path.exists(os.path.join(path, os.pardir))):
                path = None
    if path is None:
        if unsupported_os:
            raise RuntimeError(f'Operating system not supported for the specified app')
        else:
            raise RuntimeError(f'Folder/file not found for the specified app, tried: {paths_tried}')
    return path


def is_wsl():
    return platform.system() == "Linux" and "WSL_DISTRO_NAME" in os.environ


def update_wsl_env_vars():
    # Get the Windows environment variables that we need:
    appdata = subprocess.check_output(["cmd.exe", "/C", "echo %APPDATA%"],
                                       cwd="/mnt/c").decode("utf-8").strip()
    appdata = subprocess.check_output(["wslpath", appdata]).decode("utf-8").strip()
    os.environ["APPDATA"] = appdata


def main(argv):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser(
        "list", help="List available/downloaded backgrounds"
    )
    list_parser.add_argument(
        "--markdown",
        action='store_true'
    )
    list_parser.set_defaults(func=cli_list)

    download_parser = subparsers.add_parser("download", help="Download backgrounds")
    download_parser.set_defaults(func=cli_download)
    download_parser.add_argument(
        "--app",
        choices=list(apps.keys()),
        nargs="+",
        required=True,
        help="Meeting app(s) for which to add downloaded backgrounds",
    )
    download_parser.add_argument(
        "--bg",
        choices=list(backgrounds.keys()),
        default=list(backgrounds.keys()),
        nargs="+",
        help="Background collection(s) to download (default: all)",
    )
    download_parser.add_argument(
        "--force",
        action="store_true",
        help="Download backgrounds even if already downloaded",
    )

    open_parser = subparsers.add_parser(
        "open", help="Open meeting app folder with backgrounds"
    )
    open_parser.set_defaults(func=cli_open)
    open_parser.add_argument(
        "--app",
        choices=list(apps.keys()),
        required=True,
        help="Meeting app for which to open its background images folder",
    )

    remove_parser = subparsers.add_parser(
        "remove", help="Remove downloaded backgrounds"
    )
    remove_parser.set_defaults(func=cli_remove)
    remove_parser.add_argument(
        "--app",
        choices=list(apps.keys()),
        nargs="+",
        required=True,
        help="Meeting app(s) for which to remove downloaded backgrounds",
    )
    remove_parser.add_argument(
        "--bg",
        choices=list(backgrounds.keys()),
        default=list(backgrounds.keys()),
        nargs="+",
        help="Background collection(s) to remove (default: all)",
    )

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_usage()
        sys.exit(0)

    if is_wsl():
        update_wsl_env_vars()

    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
