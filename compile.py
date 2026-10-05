# -*- coding: utf-8 -*-
"""Compilation Pipeline Script for T-Zero.

Handles verification of PyInstaller, automatic installation of missing builder tools,
building resource metadata, and packaging source packages into a single-file executable.
"""

import os
import sys
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


def build_binary():
    """Runs PyInstaller commands to bundle packages and resources into a single file."""
    # Ensure build environment is clean
    for folder in ("build", "dist"):
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                logger.info(f"Cleaned folder: {folder}")
            except Exception as e:
                logger.warning(f"Could not clean directory '{folder}': {e}")

    main_script = "main.py"
    if not os.path.exists(main_script):
        logger.critical(f"Fatal: Main execution entry point '{main_script}' not found.")
        sys.exit(1)

    logger.info("Starting PyInstaller compilation pipeline...")
    
    # Generate custom icon
    icon_file = generate_siber_akademi_icon()
    
    # Assembly build arguments
    # --onefile: build a single executable
    # --noconsole: run GUI without popping terminal logs console (disable CLI terminal)
    # --clean: clean cache directories before compilation
    build_args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--clean",
        "--name=TZeroAlgorithm",
        # keyring loads its OS backends dynamically; PyInstaller cannot see them on its own
        "--collect-submodules=keyring.backends",
        "--hidden-import=win32ctypes.core",
    ]
    
    if icon_file:
        build_args.append(f"--icon={icon_file}")
        
    build_args.append(main_script)
    
    try:
        subprocess.run(build_args, check=True)
        logger.info("Binary compilation completed successfully.")
        
        # Verify output target
        target_exe = os.path.join("dist", "TZeroAlgorithm.exe" if os.name == 'nt' else "TZeroAlgorithm")
        if os.path.exists(target_exe):
            logger.info(f"Target executable successfully built at: {os.path.abspath(target_exe)}")
            return True
        else:
            logger.error("Compilation succeeded but output file could not be verified.")
            return False
            
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
