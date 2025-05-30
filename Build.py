import argparse
import logging
import subprocess
import os
import sys
import shutil
from pathlib import Path
from typing import List

# --- Constants ---
VENV_DIR_NAME = ".venv"
ADDITIONAL_SCRIPTS = ["MainMenu.py", "ModchartCore.py", "Game.py", "DevTools.py"]
REQUIREMENTS_FILE = "requirements.txt"

# --- Utility Functions ---
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

def run_command(cmd: List[str], cwd: Path = None) -> None:
    """
    Runs a command using subprocess.run.
    Captures output and logs it. Exits on command failure.
    """
    logging.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True, cwd=cwd)
        if result.stdout:
            logging.debug(f"Stdout: {result.stdout.strip()}")
        if result.stderr:
            logging.debug(f"Stderr: {result.stderr.strip()}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{' '.join(cmd)}' failed with exit code {e.returncode}")
        if e.stdout:
            logging.error(f"Output: {e.stdout.strip()}")
        if e.stderr:
            logging.error(f"Error: {e.stderr.strip()}")
        fatal_error("Command execution failed", e)
    except FileNotFoundError as e:
        logging.error(f"Command not found: {cmd[0]}. Ensure it is installed and in PATH.")
        fatal_error(f"Command '{cmd[0]}' not found.", e)
    except Exception as e:
        logging.error(f"An unexpected error occurred while running command: {' '.join(cmd)}")
        fatal_error("Command execution failed with unexpected error", e)

# --- Venv Management Functions ---
def is_venv_active() -> bool:
    """Checks if a virtual environment is currently active."""
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
            os.environ.get("VIRTUAL_ENV") is not None)

def get_venv_python_executable(venv_dir: Path) -> str:
    """Gets the path to the python executable in the venv."""
    if sys.platform.startswith("win"):
        python_exe_path = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe_path = venv_dir / "bin" / "python"
    
    if not python_exe_path.exists():
        fatal_error(f"Python executable not found in venv at {python_exe_path}")
    return str(python_exe_path)

def create_venv(venv_dir: Path) -> None:
    """Creates a virtual environment."""
    if venv_dir.exists():
        logging.info(f"Virtual environment already exists at: {venv_dir}")
        return

    logging.info(f"Creating virtual environment at: {venv_dir}...")
    try:
        # Use the current Python interpreter (could be global Python) to create the venv
        run_command([sys.executable, "-m", "venv", str(venv_dir)])
        logging.info("Virtual environment created successfully.")
    except Exception as e: # run_command handles CalledProcessError and FileNotFoundError
        fatal_error(f"Failed to create virtual environment at {venv_dir}", e)


def relaunch_in_venv(venv_dir: Path) -> None:
    """Relaunches the script using the venv's Python interpreter."""
    venv_python_exe = get_venv_python_executable(venv_dir)
    logging.info(f"Relaunching script with venv Python: {venv_python_exe} {' '.join(sys.argv)}")
    try:
        os.execv(venv_python_exe, [venv_python_exe] + sys.argv)
    except OSError as e:
        fatal_error(f"Failed to relaunch script in venv: {e}", e)
    # This part of the code will not be reached if execv is successful.

def install_dependencies(project_root: Path) -> None:
    """Installs dependencies from requirements.txt using the active venv's pip."""
    requirements_path = project_root / REQUIREMENTS_FILE
    if not requirements_path.exists():
        logging.warning(
            f"{REQUIREMENTS_FILE} not found at {requirements_path}. "
            f"Skipping dependency installation. Ensure '{REQUIREMENTS_FILE}' exists and lists all dependencies, including pyinstaller."
        )
        return

    logging.info(f"Installing dependencies from {REQUIREMENTS_FILE}...")
    try:
        # Assumes 'pip' is now the venv's pip because the script is running in the venv
        run_command(["pip", "install", "-r", str(requirements_path)])
        logging.info("Dependencies installed successfully.")
    except Exception as e: # run_command handles CalledProcessError and FileNotFoundError
        fatal_error(f"Failed to install dependencies from {REQUIREMENTS_FILE}", e)

# --- Build Process Functions ---
def prepare_build_directory(build_dir: Path) -> None:
    """
    Removes the build directory if it exists and then creates it.
    """
    try:
        if build_dir.exists():
            logging.info(f"Removing existing build directory: {build_dir}")
            shutil.rmtree(build_dir)
        build_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Prepared build directory: {build_dir}")
    except Exception as e:
        fatal_error(f"Failed to prepare build directory: {build_dir}", e)

def copy_executable_and_assets(exe_name: str, build_dir: Path, project_root: Path) -> None:
    """
    Copies the built executable and assets to the build directory.
    """
    dist_dir = project_root / "dist"
    exe_path = dist_dir / exe_name
    target_exe = build_dir / exe_name

    if not exe_path.exists():
        fatal_error(f"Executable not found at {exe_path}. Ensure PyInstaller ran successfully.")

    try:
        shutil.copy(exe_path, target_exe)
        logging.info(f"Copied executable to {target_exe}")
    except Exception as e:
        fatal_error(f"Failed to copy executable from {exe_path} to {target_exe}", e)

    assets_src = project_root / "assets"
    assets_dst = build_dir / "assets"

    if not assets_src.exists():
        logging.warning(f"Assets folder not found at {assets_src}. Skipping asset copy.")
        return # Changed to warning, as assets might be optional for some builds

    try:
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst)
        logging.info(f"Copied assets to {assets_dst}")
    except Exception as e:
        fatal_error(f"Failed to copy assets from {assets_src} to {assets_dst}", e)

def build_desktop(target_platform: str, project_root: Path) -> None:
    """
    Builds the desktop executable for the specified platform.
    """
    platform_requirements = {
        "windows": "win",
        "linux": "linux",
        "macos": "darwin"
    }

    if target_platform in platform_requirements:
        required_prefix = platform_requirements[target_platform]
        if not sys.platform.startswith(required_prefix):
            fatal_error(f"Building for {target_platform.capitalize()} is only possible on a {target_platform.capitalize()} system.")

    data_sep = ";" if target_platform == "windows" else ":"
    exe_name = "morphic.exe" if target_platform == "windows" else "morphic"
    
    add_data_args = []
    # Add assets
    assets_path = project_root / "assets"
    if assets_path.exists():
        add_data_args.append(f"--add-data={assets_path}{data_sep}assets")
    else:
        logging.warning(f"Assets directory not found at {assets_path}, not adding to PyInstaller build.")

    # Add additional scripts
    for script_name in ADDITIONAL_SCRIPTS:
        script_path = project_root / script_name
        if script_path.exists():
            add_data_args.append(f"--add-data={script_path}{data_sep}.") # Add to root of bundle
        else:
            logging.warning(f"Additional script {script_name} not found at {script_path}, skipping.")
            
    main_script_path = project_root / "main.py"
    if not main_script_path.exists():
        fatal_error(f"Main script main.py not found at {main_script_path}")

    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "morphic",
        *add_data_args,
        str(main_script_path)
    ]
    
    logging.info(f"Building desktop ({target_platform}) executable...")
    # PyInstaller creates 'dist' and 'build' folders in the CWD.
    # Run it from project_root to keep these folders there.
    run_command(cmd, cwd=project_root)

    build_dirs = {
        "windows": project_root / "build_output" / "win64",
        "linux": project_root / "build_output" / "linux",
        "macos": project_root / "build_output" / "macos"
    }
    build_dir = build_dirs.get(target_platform, project_root / "build_output" / f"unknown_{target_platform}")

    prepare_build_directory(build_dir)
    copy_executable_and_assets(exe_name, build_dir, project_root)
    logging.info(f"Desktop build for {target_platform} created in {build_dir}")
    logging.info(f"Cleaning up PyInstaller build files (build/{exe_name.replace('.exe','')}, dist, *.spec)...")
    try:
        pyinstaller_build_dir = project_root / "build" / "morphic" # Default PyInstaller build dir name
        if pyinstaller_build_dir.exists():
            shutil.rmtree(pyinstaller_build_dir.parent) # remove the 'build' folder itself
        
        pyinstaller_dist_dir = project_root / "dist"
        if pyinstaller_dist_dir.exists():
            shutil.rmtree(pyinstaller_dist_dir)
        
        spec_file = project_root / "morphic.spec"
        if spec_file.exists():
            os.remove(spec_file)
        logging.info("PyInstaller temporary files cleaned up.")
    except Exception as e:
        logging.warning(f"Could not fully clean up PyInstaller files: {e}")


def main() -> None:
    """
    Manages venv, installs dependencies, parses command-line arguments, and triggers the build process.
    """
    parser = argparse.ArgumentParser(
        description="Build Morphic for Windows, Linux, macOS. Manages a .venv automatically."
    )
    parser.add_argument(
        "--target",
        choices=["windows", "linux", "macos", "all"],
        default="all", # Default to current system if 'all' is not viable
        help="Target build platform (default: current system or 'all' if viable)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    args = parser.parse_args()

    configure_logging(args.verbose)
    project_root = get_project_root()
    venv_dir = project_root / VENV_DIR_NAME

    if not is_venv_active():
        logging.info("Not running in an active virtual environment.")
        if not venv_dir.exists():
            create_venv(venv_dir)
        else:
            logging.info(f"Virtual environment found at {venv_dir}.")
        relaunch_in_venv(venv_dir) # This will exit and restart the script in the venv
        return # Should not be reached

    logging.info(f"Running in active virtual environment: {sys.prefix}")
    install_dependencies(project_root)

    # Determine build targets
    available_platforms = {
        "windows": sys.platform.startswith("win"),
        "linux": sys.platform.startswith("linux"),
        "macos": sys.platform.startswith("darwin")
    }
    
    targets_to_build = []
    if args.target == "all":
        # Build for all platforms supported by the current OS
        targets_to_build = [plat for plat, runnable in available_platforms.items() if runnable]
        if not targets_to_build:
            # This case should ideally not happen if script is run on win/linux/macos
            fatal_error("Cannot determine a build target for 'all' on the current system.")
    else:
        # Build for a specific target
        if available_platforms.get(args.target):
            targets_to_build = [args.target]
        else:
            fatal_error(f"Building for {args.target.capitalize()} is not supported on this system ({sys.platform}).")

    if not targets_to_build:
        logging.info("No valid targets specified or current system cannot build for 'all'. Defaulting to current system.")
        current_os_target = None
        if sys.platform.startswith("win"): current_os_target = "windows"
        elif sys.platform.startswith("linux"): current_os_target = "linux"
        elif sys.platform.startswith("darwin"): current_os_target = "macos"
        
        if current_os_target:
            targets_to_build = [current_os_target]
        else:
            fatal_error("Could not determine a default build target for the current operating system.")


    logging.info(f"Selected build targets: {', '.join(targets_to_build)}")

    for target_platform in targets_to_build:
        logging.info(f"Starting build for {target_platform.capitalize()}...")
        build_desktop(target_platform, project_root)
        logging.info(f"Successfully built for {target_platform.capitalize()}.")

    logging.info("All builds completed.")

if __name__ == "__main__":
    try:
        main()
    except SystemExit: # Allow sys.exit() to pass through
        raise
    except Exception as e:
        fatal_error("A critical error occurred during the build process", e)
