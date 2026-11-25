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
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TZero.Compile")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
    icon_path = str(PROJECT_ROOT / "tzero" / "siber_akademi.ico")

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
        for proc_name in ("TZeroAlgorithm.exe", "TZeroCLI.exe", "TZeroMCP.exe", "AddMCP.exe", "TZeroCI.exe"):
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
            "--hidden-import=addmcp",
            "--collect-all=tiktoken",
            "--collect-submodules=tiktoken_ext",
            "--hidden-import=win32ctypes.core",
            "--collect-all=tzero",
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
            "--hidden-import=win32ctypes.core",
            "--collect-all=tzero",
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
        server_args.extend(["--paths=.", "tzero/tzero_mcp.py"])
        server_name = "TZeroMCP.exe" if os.name == "nt" else "TZeroMCP"
        prepare_target_file(server_name)
        subprocess.run(server_args, check=True)

        server_binary = os.path.join("dist", server_name)
        if not os.path.exists(server_binary):
            logger.error("MCP server executable was not created.")
            return False

        cli_args = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--clean",
            "--noconfirm",
            "--name=TZeroCLI",
            "--distpath=dist",
            "--workpath=build/TZeroCLI",
            "--specpath=build/specs",
            "--collect-all=tiktoken",
            "--collect-submodules=tiktoken_ext",
            "--hidden-import=win32ctypes.core",
            "--collect-all=tzero",
            "--collect-all=keyring",
            "--collect-all=win32ctypes",
            "--collect-all=pygments",
            "--collect-all=requests",
            "--collect-all=urllib3",
            "--collect-all=certifi",
            "--copy-metadata=keyring",
            "--copy-metadata=requests",
            "--copy-metadata=pygments",
        ]
        if icon_file:
            cli_args.append(f"--icon={os.path.abspath(icon_file)}")
        cli_args.extend(["--paths=.", "tzero/tzero_v3.py"])
        cli_name = "TZeroCLI.exe" if os.name == "nt" else "TZeroCLI"
        prepare_target_file(cli_name)
        subprocess.run(cli_args, check=True)

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
            installer_args.append(f"--add-data={os.path.abspath(icon_file)}{os.pathsep}tzero")
        installer_args.append("addmcp.py")
        installer_name = "AddMCP.exe" if os.name == "nt" else "AddMCP"
        prepare_target_file(installer_name)
        subprocess.run(installer_args, check=True)

        ci_args = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--clean",
            "--noconfirm",
            "--name=TZeroCI",
            "--distpath=dist",
            "--workpath=build/TZeroCI",
            "--specpath=build/specs",
            "--collect-all=tzero",
            "--collect-all=keyring",
            "--collect-all=requests",
            "--copy-metadata=keyring",
            "--copy-metadata=requests",
        ]
        if icon_file:
            ci_args.append(f"--icon={os.path.abspath(icon_file)}")
        ci_args.extend(["--paths=.", "tzero/tzero_ci.py"])
        ci_name = "TZeroCI.exe" if os.name == "nt" else "TZeroCI"
        prepare_target_file(ci_name)
        subprocess.run(ci_args, check=True)

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
            os.path.join("dist", f"TZeroCLI{suffix}"),
            os.path.join("dist", f"TZeroMCP{suffix}"),
            os.path.join("dist", f"AddMCP{suffix}"),
            os.path.join("dist", f"TZeroCI{suffix}"),
        ]
        missing = [path for path in expected_outputs if not os.path.exists(path)]
        if missing:
            logger.error("Build outputs could not be verified: %s", ", ".join(missing))
            return False

        for path in expected_outputs:
            logger.info("Binary successfully built at: %s", os.path.abspath(path))

        # Apply military-grade Anti-REA binary shielding against pyinstxtractor
        try:
            from tzero.tzero_armor import shield_executable
            for path in expected_outputs:
                if os.path.exists(path) and path.endswith((".exe", ".bin")):
                    shield_res = shield_executable(path)
                    if shield_res.get("shielded"):
                        logger.info("Anti-REA Armor successfully shielded executable: %s", path)
        except Exception as e:
            logger.warning("Could not apply Anti-REA binary shielding: %s", e)

        return True
            
    except subprocess.CalledProcessError as cpe:
        logger.critical(f"Compilation pipeline failed with command exception: {cpe}")
        return False


def create_release_bundle():
    """Packages all compiled binaries and documentation into a single zip archive for release."""
    import zipfile
    import tomllib
    
    version = "12.2.1"
    try:
        with open(PROJECT_ROOT / "pyproject.toml", "rb") as f:
            version = tomllib.load(f)["project"]["version"]
    except Exception:
        pass

    suffix = ".exe" if os.name == "nt" else ""
    bundle_name = f"TZero-v{version}-Windows-x64.zip" if os.name == "nt" else f"TZero-v{version}-Linux-x64.tar.gz"
    bundle_path = os.path.join("dist", bundle_name)
    
    binaries = [
        f"TZeroAlgorithm{suffix}",
        f"TZeroCLI{suffix}",
        f"TZeroMCP{suffix}",
        f"AddMCP{suffix}",
        f"TZeroCI{suffix}",
    ]
    
    if os.name == "nt":
        with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for b in binaries:
                p = os.path.join("dist", b)
                if os.path.exists(p):
                    zf.write(p, arcname=b)
            for doc in ("README.md", "README.tr.md", "LICENSE"):
                doc_p = PROJECT_ROOT / doc
                if doc_p.is_file():
                    zf.write(str(doc_p), arcname=doc)
    logger.info("Master release bundle successfully generated at: %s", os.path.abspath(bundle_path))
    return bundle_path


def main():
    os.chdir(PROJECT_ROOT)
    check_and_install_pyinstaller()
    success = build_binary()
    if success:
        logger.info("T-Zero context compiler execution completed successfully.")
        create_release_bundle()
    else:
        logger.error("Compilation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
