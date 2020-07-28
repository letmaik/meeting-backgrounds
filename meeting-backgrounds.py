import os
import sys
import json
import urllib.request
import platform
import subprocess
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
        os.makedirs(bg_dir, exist_ok=True)

    count = 0
    for bg_name in args.bg:
        bg = backgrounds[bg_name]
        for url in bg["image_urls"]:
            target_paths = []
            for app_name in args.app:
                bg_dir = get_bg_dir(app_name)
                filename = get_bg_filename(bg_name, url)
                path = os.path.join(bg_dir, filename)
                target_paths.append(path)
            if not args.force and all(os.path.exists(path) for path in target_paths):
                print(f"Skipping {url}, already downloaded")
                continue
            print(f"Downloading {url}")
            with urllib.request.urlopen(url) as r:
                img = r.read()
            for path in target_paths:
                print(f"Saving to {path}")
                with open(path, "wb") as f:
                    f.write(img)
            count += 1
    print(f"{count} backgrounds downloaded.")


def cli_open(args):
    bg_dir = get_bg_dir(args.app)
    if not os.path.exists(bg_dir):
        print(f"Folder does not exist: {bg_dir}")
        sys.exit(1)
    open_folder(bg_dir)


def cli_remove(args):
    count = 0
    for app_name in args.app:
        bg_dir = get_bg_dir(app_name)
        for bg_name in args.bg:
            bg = backgrounds[bg_name]
            for url in bg["image_urls"]:
                filename = get_bg_filename(bg_name, url)
                path = os.path.join(bg_dir, filename)
                if os.path.exists(path):
                    print(f"Removing {path}")
                    os.remove(path)
                    # Thumbs are automatically created by the meeting app.
                    path_thumb = get_bg_thumb_path(app_name, bg_name, url)
                    if path_thumb is not None and os.path.exists(path_thumb):
                        os.remove(path_thumb)
                    count += 1
    print(f"{count} backgrounds removed.")


def get_bg_dir(app_name: str) -> str:
    if app_name in get_bg_dir.cache:
        return get_bg_dir.cache[app_name]
    app = apps[app_name]
    bg_dir = app["bg_dir"].get(platform.system())
    if bg_dir is None:
        # If the platform is WSL, try the Windows version.
        if (platform.system() == "Linux") and \
           (os.environ["WSL_DISTRO_NAME"] is not None):
            print("No Linux app found, but this appears to be WSL, trying Windows version")
            # Get the Windows environment variables that we need:
            appdata = subprocess.check_output(["cmd.exe", "/C", "echo %APPDATA%"],
                                              cwd="/mnt/c").decode("utf-8").strip()
            appdata = subprocess.check_output(["wslpath", appdata]).decode("utf-8").strip()
            os.environ["APPDATA"] = appdata
            bg_dir = app["bg_dir"].get("Windows")
    if bg_dir is None:
        raise RuntimeError(f'Your operating system is not supported for "{app_name}".')
    bg_dir = os.path.expandvars(bg_dir)
    get_bg_dir.cache[app_name] = bg_dir
    return bg_dir

get_bg_dir.cache = {}

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


def open_folder(path):
    # https://stackoverflow.com/a/16204023
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


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
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
