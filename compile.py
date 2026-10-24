# -*- coding: utf-8 -*-
"""Compilation Pipeline Script for T-Zero.

Handles verification of PyInstaller, automatic installation of missing builder tools,
building resource metadata, and packaging source packages into a single-file executable.
"""

import os
import sys
import time
import shutil
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TZero.Compile")


def check_and_install_pyinstaller():
    """Checks if PyInstaller is installed in active Python context and installs if missing."""
    try:
        import PyInstaller
        logger.info("PyInstaller builder resolved in environment.")
    except ImportError:
        logger.warning("PyInstaller package not found. Installing now...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            logger.info("Successfully installed PyInstaller.")
        except subprocess.CalledProcessError as e:
            logger.critical(f"Fatal: PyInstaller installation failed: {e}")
            sys.exit(1)


def generate_siber_akademi_icon():
    """Generates a custom Siber Akademi icon dynamically using Pillow if missing."""
    icon_path = "siber_akademi.ico"

    if os.path.exists(icon_path):
        logger.info("Siber Akademi icon already resolved in workspace.")
        return icon_path
        
    try:
        from PIL import Image, ImageDraw
        # Create a high-res square image
        img = Image.new("RGBA", (256, 256), color=(11, 12, 16, 255)) # Dark background
        draw = ImageDraw.Draw(img)
        
        # Draw a beautiful glowing border circle
        draw.ellipse([20, 20, 236, 236], outline=(132, 204, 22, 255), width=8) # Neon Green / Cyan border
        draw.ellipse([30, 30, 226, 226], fill=(22, 24, 33, 255)) # Darker inner card
        
        # Draw letters 'SA'
        # S:
        draw.line([70, 75, 125, 75], fill=(251, 191, 36, 255), width=12) # Gold Top
        draw.line([70, 75, 70, 125], fill=(251, 191, 36, 255), width=12)
        draw.line([70, 125, 125, 125], fill=(251, 191, 36, 255), width=12) # Gold Center
        draw.line([125, 125, 125, 175], fill=(251, 191, 36, 255), width=12)
        draw.line([70, 175, 125, 175], fill=(251, 191, 36, 255), width=12) # Gold Bottom
        
        # A:
        draw.line([145, 175, 165, 75], fill=(132, 204, 22, 255), width=12) # Green Left
        draw.line([185, 175, 165, 75], fill=(132, 204, 22, 255), width=12) # Green Right
        draw.line([153, 130, 177, 130], fill=(132, 204, 22, 255), width=12) # Green Crossbar
        
        # Save as multi-size ICO
        img.save(icon_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        logger.info("Siber Akademi custom icon successfully generated.")
        return icon_path
    except Exception as e:
        logger.warning(f"Unable to generate custom icon: {e}. Fallback to generic compile.")
        return None


def kill_running_tzero_processes():
    """Kill any running T-Zero binaries to avoid file locking on Windows."""
    if os.name == "nt":
        for proc_name in ("TZeroAlgorithm.exe", "TZeroMCP.exe", "AddMCP.exe"):
            try:
                subprocess.run(["taskkill", "/F", "/IM", proc_name, "/T"], capture_output=True, text=True)
            except Exception:
                pass


def prepare_target_file(proc_name: str):
    """Ensure specific target binary is free to be written, renaming if locked."""
    target_path = os.path.join("dist", proc_name)
    if os.path.exists(target_path):
        try:
            os.remove(target_path)
        except Exception:
            try:
                os.rename(target_path, f"{target_path}.old_{int(time.time())}")
            except Exception:
                pass


def build_binary():
    """Runs PyInstaller commands to bundle packages and resources into a single file."""
    kill_running_tzero_processes()
    # Clean build environment
    if os.path.exists("build"):
        try:
            shutil.rmtree("build")
            logger.info("Cleaned folder: build")
        except Exception as e:
            logger.warning(f"Could not clean directory 'build': {e}")
    main_binary = os.path.join("dist", "TZeroAlgorithm.exe" if os.name == "nt" else "TZeroAlgorithm")
    icon_file = generate_siber_akademi_icon()
    
    try:
        main_script = "main.py"
        build_args = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--noconsole",
            "--clean",
            "--noconfirm",
            "--name=TZeroAlgorithm",
            "--distpath=dist",
            "--workpath=build/TZeroAlgorithm",
            "--specpath=build/specs",
            "--hidden-import=tzero_v3",
            "--hidden-import=tzero_features",
            "--hidden-import=tzero_deps",
            "--hidden-import=addmcp",
            "--hidden-import=tzero_mcp",
            "--hidden-import=tzero_polyglot",
            "--hidden-import=tzero_dashboard",
            "--hidden-import=tzero_jarvis",
            "--hidden-import=tzero_superdesign",
            "--hidden-import=win32ctypes.core",
            "--collect-all=tzero_jarvis",
            "--collect-all=keyring",
            "--collect-all=win32ctypes",
            "--collect-all=pygments",
            "--collect-all=requests",
            "--collect-all=urllib3",
            "--collect-all=certifi",
            "--collect-all=PIL",
            "--collect-all=darkdetect",
            "--copy-metadata=keyring",
            "--copy-metadata=requests",
            "--copy-metadata=pygments",
            "--copy-metadata=Pillow",
        ]
        if icon_file:
            abs_icon = os.path.abspath(icon_file)
            build_args.append(f"--icon={abs_icon}")
            build_args.append(f"--add-data={abs_icon}{os.pathsep}.")
        build_args.append(main_script)
        prepare_target_file("TZeroAlgorithm.exe" if os.name == "nt" else "TZeroAlgorithm")
        subprocess.run(build_args, check=True)

        server_args = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--clean",
            "--noconfirm",
            "--name=TZeroMCP",
            "--distpath=dist",
            "--workpath=build/TZeroMCP",
            "--specpath=build/specs",
            "--hidden-import=tzero_v3",
            "--hidden-import=tzero_features",
            "--hidden-import=tzero_deps",
            "--hidden-import=tzero_polyglot",
            "--hidden-import=tzero_dashboard",
            "--hidden-import=tzero_jarvis",
            "--hidden-import=tzero_superdesign",
            "--hidden-import=win32ctypes.core",
            "--collect-all=tzero_jarvis",
            "--collect-submodules=mcp.server",
            "--collect-submodules=mcp.types",
            "--collect-data=mcp",
            "--exclude-module=mcp.cli",
            "--collect-all=anyio",
            "--collect-all=pydantic",
            "--collect-all=pydantic_core",
            "--collect-all=keyring",
            "--collect-all=win32ctypes",
            "--collect-all=requests",
            "--collect-all=urllib3",
            "--collect-all=certifi",
            "--copy-metadata=mcp",
            "--copy-metadata=keyring",
            "--copy-metadata=requests",
        ]
        if icon_file:
            server_args.append(f"--icon={os.path.abspath(icon_file)}")
        server_args.append("tzero_mcp.py")
        server_name = "TZeroMCP.exe" if os.name == "nt" else "TZeroMCP"
        prepare_target_file(server_name)
        subprocess.run(server_args, check=True)

        server_binary = os.path.join("dist", server_name)
        if not os.path.exists(server_binary):
            logger.error("MCP server executable was not created.")
            return False

        installer_args = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--noconsole",
            "--clean",
            "--noconfirm",
            "--name=AddMCP",
            "--distpath=dist",
            "--workpath=build/AddMCP",
            "--specpath=build/specs",
            "--hidden-import=win32ctypes.core",
            "--collect-all=keyring",
            "--collect-all=win32ctypes",
            f"--add-binary={os.path.abspath(server_binary)}{os.pathsep}.",
        ]
        if icon_file:
            installer_args.append(f"--icon={os.path.abspath(icon_file)}")
            installer_args.append(f"--add-data={os.path.abspath(icon_file)}{os.pathsep}.")
        installer_args.append("addmcp.py")
        installer_name = "AddMCP.exe" if os.name == "nt" else "AddMCP"
        prepare_target_file(installer_name)
        subprocess.run(installer_args, check=True)

        # Cleanup leftover .old_ backup files if any
        if os.path.exists("dist"):
            for fname in os.listdir("dist"):
                if ".old" in fname:
                    try:
                        os.remove(os.path.join("dist", fname))
                    except Exception:
                        pass

        suffix = ".exe" if os.name == "nt" else ""
        expected_outputs = [
            os.path.join("dist", f"TZeroAlgorithm{suffix}"),
            os.path.join("dist", f"TZeroMCP{suffix}"),
            os.path.join("dist", f"AddMCP{suffix}"),
        ]
        missing = [path for path in expected_outputs if not os.path.exists(path)]
        if missing:
            logger.error("Build outputs could not be verified: %s", ", ".join(missing))
            return False

        for path in expected_outputs:
            logger.info("Binary successfully built at: %s", os.path.abspath(path))
        return True
            
    except subprocess.CalledProcessError as cpe:
        logger.critical(f"Compilation pipeline failed with command exception: {cpe}")
        return False


def main():
    check_and_install_pyinstaller()
    success = build_binary()
    if success:
        logger.info("T-Zero context compiler execution completed successfully.")
    else:
        logger.error("Compilation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
