import subprocess
import sys
import os

def check_python_version():
    """Checks if the Python version is 3.7 or higher."""
    print("Checking Python version...")
    try:
        version_info = sys.version_info
        if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 7):
            print(f"Python version {version_info.major}.{version_info.minor} detected.")
            print("This game requires Python 3.7 or higher.")
            print("Please install or update Python from https://www.python.org/")
            return False
        print(f"Python version {version_info.major}.{version_info.minor}.{version_info.micro} detected. (OK)")
        return True
    except Exception as e:
        print(f"Could not determine Python version: {e}")
        print("Please ensure Python 3.7+ is installed and in your system's PATH.")
        return False

def check_pip():
    """Checks if pip is available to the current Python interpreter."""
    print("\nChecking for pip (Python package installer)...")
    try:
        # Try to import pip. This is a more reliable check than just running "pip --version"
        # as it confirms pip is available to the current Python interpreter.
        # However, directly importing pip can sometimes be problematic or not reflect CLI availability.
        # A subprocess call to 'pip --version' is often more indicative of CLI usability.
        subprocess.check_call([sys.executable, "-m", "pip", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("pip is available. (OK)")
        return True
    except subprocess.CalledProcessError:
        print("pip command check failed.")
        print("pip is usually installed by default with Python 3.4+.")
        print("If you have Python installed, try running: python -m ensurepip --upgrade")
        print("Or refer to https://pip.pypa.io/en/stable/installation/ for instructions.")
        return False
    except FileNotFoundError: # This can happen if sys.executable is odd, or python itself isn't found well
        print("Failed to execute Python for pip check. Ensure Python is correctly installed and in PATH.")
        return False
    except Exception as e:
        print(f"Error checking for pip: {e}")
        return False

def install_panda3d():
    """Checks for Panda3D and installs it if missing."""
    if not check_pip(): # check_pip already prints messages
        return False

    print("\nChecking if Panda3D is installed...")
    try:
        # Attempt to import Panda3D to check if it's installed
        import panda3d
        print("Panda3D is already installed. (OK)")
        return True
    except ImportError:
        print("Panda3D is not found. Attempting to install...")
        try:
            # Use sys.executable to ensure pip is called for the correct Python version
            print(f"Running: {sys.executable} -m pip install Panda3D")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Panda3D"])
            print("Panda3D installed successfully.")
            # Verify installation
            try:
                import panda3d
                print("Panda3D installation verified. (OK)")
                return True
            except ImportError:
                print("ERROR: Failed to import Panda3D after installation. This is unexpected.")
                print("Please check your Python environment or try installing manually.")
                return False
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Error installing Panda3D: {e}")
            print("This could be due to network issues, permission problems, or conflicts.")
            print("Please try installing Panda3D manually: python -m pip install Panda3D")
            return False
        except FileNotFoundError: # Should be caught by check_pip, but as a fallback
            print("ERROR: 'pip' command not found, even though Python is present.")
            print("Please ensure pip is correctly installed and in your PATH.")
            return False
    return False # Should ideally not be reached if logic is correct

def main():
    """Main function to run the setup checks and installations."""
    print("--- Panda3D Minecraft-like Game Setup ---")

    if not check_python_version():
        print("\nSetup aborted due to Python version issue.")
        sys.exit(1)

    if not install_panda3d():
        print("\nSetup failed during Panda3D installation.")
        print("Please ensure all prerequisites are met and try again or install Panda3D manually.")
        sys.exit(1)

    print("\n--------------------------------------------------")
    print("Setup process likely completed successfully!")
    print("If there were no errors above, Panda3D should be installed.")
    print("\nNext steps:")
    print("1. Ensure you have texture files in the 'assets/textures/' directory:")
    print("   - grass_side.png")
    print("   - stone.png")
    print("   (These are not provided by the game and must be added manually.)")
    print("\n2. To run the game, execute from the project root directory:")
    print("   python src/main.py")
    print("   (or 'python -m src.main')")
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
