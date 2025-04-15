import argparse
import logging
import subprocess
import sys
import shutil
from pathlib import Path
from typing import List

def fatal_error(message: str, exception: Exception = None) -> None:
    """Logs a fatal error and exits."""
    if exception:
        logging.exception(message)
    else:
        logging.critical(message)
    sys.exit(1)

def configure_logging(verbose: bool) -> None:
    """Configure logging based on verbose flag."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def get_project_root() -> Path:
    """Returns the project root directory (directory containing this script)."""
    return Path(__file__).resolve().parent

def run_command(cmd: List[str]) -> None:
    """
    Runs a command using subprocess.run.
    Captures output and logs it. Exits on command failure.
    """
    logging.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        if result.stdout:
            logging.debug(result.stdout)
        if result.stderr:
            logging.debug(result.stderr)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{' '.join(cmd)}' failed with exit code {e.returncode}")
        if e.stdout:
            logging.error(f"Output: {e.stdout}")
        if e.stderr:
            logging.error(f"Error: {e.stderr}")
        fatal_error("Command execution failed", e)

def prepare_build_directory(build_dir: Path) -> None:
    """
    Removes the build directory if it exists and then creates it.
    """
    try:
        if build_dir.exists():
            shutil.rmtree(build_dir)
        build_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Prepared build directory: {build_dir}")
    except Exception as e:
        fatal_error(f"Failed to prepare build directory: {build_dir}", e)

def copy_executable_and_assets(exe_name: str, build_dir: Path) -> None:
    """
    Copies the built executable and assets to the build directory.
    """
    project_root = get_project_root()
    exe_path = project_root / "dist" / exe_name
    target_exe = build_dir / exe_name

    if not exe_path.exists():
        fatal_error(f"Executable not found at {exe_path}. Ensure the build step completed successfully.")

    try:
        shutil.copy(exe_path, target_exe)
        logging.info(f"Copied executable to {target_exe}")
    except Exception as e:
        fatal_error("Failed to copy executable", e)

    assets_src = project_root / "assets"
    assets_dst = build_dir / "assets"

    if not assets_src.exists():
        fatal_error(f"Assets folder not found at {assets_src}")

    try:
        shutil.copytree(assets_src, assets_dst)
        logging.info(f"Copied assets to {assets_dst}")
    except Exception as e:
        fatal_error("Failed to copy assets", e)

def build_desktop(target_platform: str) -> None:
    """
    Builds the desktop executable for the specified platform.
    """
    project_root = get_project_root()
    platform_requirements = {
        "windows": "win",
        "linux": "linux",
        "macos": "darwin"
    }

    if target_platform in platform_requirements:
        required_prefix = platform_requirements[target_platform]
        if not sys.platform.startswith(required_prefix):
            fatal_error(f"Building for {target_platform.capitalize()} is only possible on a {target_platform.capitalize()} system.")

    # Determine the data separator for PyInstaller
    data_sep = ";" if target_platform == "windows" else ":"
    exe_name = "morphic.exe" if target_platform == "windows" else "morphic"
    cmd = [
        "pyinstaller",
        "--onefile",
        f"--add-data=assets{data_sep}assets",
        "--name", "morphic",
        str(project_root / "MainMenu.py")
    ]
    logging.info(f"Building desktop ({target_platform}) executable...")
    run_command(cmd)

    # Define build directories for each platform
    build_dirs = {
        "windows": project_root / "build" / "win64",
        "linux": project_root / "build" / "linux",
        "macos": project_root / "build" / "macos"
    }
    build_dir = build_dirs.get(target_platform, project_root / f"build_{target_platform}")

    prepare_build_directory(build_dir)
    copy_executable_and_assets(exe_name, build_dir)
    logging.info(f"Desktop build for {target_platform} created in {build_dir}")

def main() -> None:
    """
    Parses command-line arguments and triggers the build process.
    """
    parser = argparse.ArgumentParser(
        description="Build Morphic for Windows, Linux, macOS."
    )
    parser.add_argument(
        "--target",
        choices=["windows", "linux", "macos", "all"],
        default="all",
        help="Target build platform (default: all)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    args = parser.parse_args()

    configure_logging(args.verbose)

    # Create a list of platforms to build based on the arguments and current system.
    available_platforms = {
        "windows": sys.platform.startswith("win"),
        "linux": sys.platform.startswith("linux"),
        "macos": sys.platform.startswith("darwin")
    }
    
    targets = []
    if args.target == "all":
        targets = [plat for plat, available in available_platforms.items() if available]
    else:
        if available_platforms.get(args.target, False):
            targets = [args.target]
        else:
            fatal_error(f"Current system does not support building for {args.target.capitalize()}.")

    # Trigger builds for each selected target.
    for target in targets:
        logging.info(f"Starting build for {target.capitalize()}")
        build_desktop(target)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        fatal_error("A fatal error occurred during the build process", e)