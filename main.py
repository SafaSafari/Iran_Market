import os
import json
import uuid
import random
import requests
from hashlib import sha1
import argparse
import time
import zipfile
import subprocess
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
import urllib.request
import urllib.parse
import platform
from pathlib import Path


import sys
import tty
import termios


ARCHITECTURES = {
    "arm64": {
        "abis": ["arm64-v8a", "armeabi-v7a", "armeabi"],
        "cpu": "arm64-v8a,armeabi-v7a,armeabi",
        "tag": "modern phones",
    },
    "arm32": {
        "abis": ["armeabi-v7a", "armeabi"],
        "cpu": "armeabi-v7a,armeabi",
        "tag": "chinese or old phones",
    },
    "x86": {"abis": ["x86"], "cpu": "x86", "tag": "emulator"},
    "x86_64": {"abis": ["x86_64", "x86"], "cpu": "x86_64,x86", "tag": "emulator"},
}

STORES = {
    "both": "Both (Myket + Bazaar)",
    "myket": "Myket only",
    "bazaar": "Bazaar only",
}


TOOLS_CONFIG = {
    "apkeditor": {
        "repo": "REAndroid/APKEditor",
        "filename": "APKEditor.jar",
        "pattern": r"APKEditor-.*\.jar$",
    },
    "uber_signer": {
        "repo": "patrickfav/uber-apk-signer",
        "filename": "uber-apk-signer.jar",
        "pattern": r"uber-apk-signer-.*\.jar$",
    },
}


def get_user_config_dir():
    """Get user configuration directory"""
    home = Path.home()
    if platform.system() == "Windows":
        config_dir = home / "AppData" / "Local" / "IranianAppDownloader"
    elif platform.system() == "Darwin":
        config_dir = home / "Library" / "Application Support" / "IranianAppDownloader"
    else:
        config_dir = home / ".config" / "IranianAppDownloader"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


class ToolInstaller:
    """Automatic tool installer and manager"""

    def __init__(self):
        self.config_dir = get_user_config_dir()
        self.tools_dir = self.config_dir / "tools"
        self.tools_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Iranian-App-Downloader/1.0"})

    def get_github_latest_release(self, repo):
        """Get latest release info from GitHub"""
        try:
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to get release info for {repo}: {e}")
            return None

    def download_file_with_progress(self, url, filepath):
        """Download file with progress bar"""
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            filename = filepath.name

            if total_size > 0:
                progress = ProgressBar(total_size, f"📥 {filename}")

                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress.update(len(chunk))
                progress.finish()
            else:

                print(f"📥 Downloading {filename}...")
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"✅ Downloaded {filename}")

            return True
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False

    def install_apkeditor(self):
        """Install APKEditor.jar"""
        config = TOOLS_CONFIG["apkeditor"]
        target_path = self.tools_dir / config["filename"]

        if target_path.exists():
            print(f"✅ APKEditor already installed at {target_path}")
            return str(target_path)

        print("🔍 Getting APKEditor latest release...")
        release_info = self.get_github_latest_release(config["repo"])

        if not release_info:
            return None

        jar_asset = None
        import re

        pattern = re.compile(config["pattern"])

        for asset in release_info.get("assets", []):
            if pattern.match(asset["name"]):
                jar_asset = asset
                break

        if not jar_asset:
            print("❌ APKEditor jar file not found in release assets")
            return None

        print(f"📦 Found APKEditor {release_info['tag_name']}")

        if self.download_file_with_progress(
            jar_asset["browser_download_url"], target_path
        ):
            print(f"✅ APKEditor installed to {target_path}")
            return str(target_path)

        return None

    def install_uber_signer(self):
        """Install uber-apk-signer.jar"""
        config = TOOLS_CONFIG["uber_signer"]
        target_path = self.tools_dir / config["filename"]

        if target_path.exists():
            print(f"✅ Uber APK Signer already installed at {target_path}")
            return str(target_path)

        print("🔍 Getting Uber APK Signer latest release...")
        release_info = self.get_github_latest_release(config["repo"])

        if not release_info:
            return None

        jar_asset = None
        import re

        pattern = re.compile(config["pattern"])

        for asset in release_info.get("assets", []):
            if pattern.match(asset["name"]):
                jar_asset = asset
                break

        if not jar_asset:
            print("❌ Uber APK Signer jar file not found in release assets")
            return None

        print(f"📦 Found Uber APK Signer {release_info['tag_name']}")

        if self.download_file_with_progress(
            jar_asset["browser_download_url"], target_path
        ):
            print(f"✅ Uber APK Signer installed to {target_path}")
            return str(target_path)

        return None

    def get_adb_download_url(self):
        """Get ADB platform-tools download URL for current OS"""
        system = platform.system().lower()

        urls = {
            "windows": "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
            "darwin": "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip",
            "linux": "https://dl.google.com/android/repository/platform-tools-latest-linux.zip",
        }

        return urls.get(system)

    def install_adb(self):
        """Install ADB platform tools"""
        adb_dir = self.tools_dir / "platform-tools"
        adb_exe = "adb.exe" if platform.system() == "Windows" else "adb"
        adb_path = adb_dir / adb_exe

        if adb_path.exists():
            print(f"✅ ADB already installed at {adb_path}")
            return str(adb_path)

        download_url = self.get_adb_download_url()
        if not download_url:
            print(f"❌ ADB download not available for {platform.system()}")
            return None

        print("📥 Downloading Android Platform Tools (ADB)...")

        zip_path = self.tools_dir / "platform-tools.zip"

        if not self.download_file_with_progress(download_url, zip_path):
            return None

        try:
            print("📦 Extracting platform-tools...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(self.tools_dir)

            zip_path.unlink()

            if adb_path.exists():

                if platform.system() != "Windows":
                    os.chmod(adb_path, 0o755)

                print(f"✅ ADB installed to {adb_path}")
                return str(adb_path)
            else:
                print("❌ ADB executable not found after extraction")
                return None

        except Exception as e:
            print(f"❌ Failed to extract platform-tools: {e}")
            return None

    def setup_tools_interactive(self):
        """Interactive setup for missing tools"""
        menu = InteractiveMenu()

        if not CapabilityChecker.check_java():
            print("❌ Java is required but not found!")
            print("   Please install Java first:")
            print("   Ubuntu/Debian: sudo apt install openjdk-11-jdk")
            print("   macOS: brew install openjdk@11")
            print("   Windows: Download from Oracle or use scoop/chocolatey")
            input("\nPress Enter after installing Java...")

            if not CapabilityChecker.check_java():
                print("❌ Java still not detected. Skipping Java-dependent tools.")
                java_available = False
            else:
                java_available = True
        else:
            java_available = True

        tools_to_install = []

        if java_available and not CapabilityChecker().find_apkeditor():
            options = [
                "Yes, download APKEditor automatically",
                "No, I'll install it manually",
                "Skip",
            ]
            choice = menu.show_menu(
                "APKEditor not found. Download automatically?",
                options,
                [
                    "Recommended - Downloads latest version automatically",
                    "You can install it manually later",
                    "APKEditor merge method will be disabled",
                ],
            )

            if choice == 0:
                tools_to_install.append("apkeditor")

        if java_available and not CapabilityChecker().find_uber_signer():
            options = [
                "Yes, download Uber APK Signer",
                "No, use default Android tools",
                "Skip",
            ]
            choice = menu.show_menu(
                "Download Uber APK Signer for better APK signing?",
                options,
                [
                    "Recommended - Better compatibility and features",
                    "Use system apksigner if available",
                    "Full merge method may be limited",
                ],
            )

            if choice == 0:
                tools_to_install.append("uber_signer")

        if not CapabilityChecker.check_tool("adb"):
            options = [
                "Yes, download ADB platform tools",
                "No, I'll install it manually",
                "Skip",
            ]
            choice = menu.show_menu(
                "ADB not found. Download platform tools?",
                options,
                [
                    "Downloads official Android platform tools",
                    "You can install Android SDK separately",
                    "ADB install method will be disabled",
                ],
            )

            if choice == 0:
                tools_to_install.append("adb")

        if tools_to_install:
            print(f"\n🔧 Installing {len(tools_to_install)} tools...")

            for tool in tools_to_install:
                if tool == "apkeditor":
                    self.install_apkeditor()
                elif tool == "uber_signer":
                    self.install_uber_signer()
                elif tool == "adb":
                    self.install_adb()

        print("\n✅ Tool setup completed!")
        input("Press Enter to continue...")

    def get_tool_path(self, tool_name):
        """Get path to installed tool"""
        if tool_name == "apkeditor":
            return self.tools_dir / TOOLS_CONFIG["apkeditor"]["filename"]
        elif tool_name == "uber_signer":
            return self.tools_dir / TOOLS_CONFIG["uber_signer"]["filename"]
        elif tool_name == "adb":
            adb_dir = self.tools_dir / "platform-tools"
            adb_exe = "adb.exe" if platform.system() == "Windows" else "adb"
            return adb_dir / adb_exe
        return None


class InteractiveMenu:
    def __init__(self):
        self.selected = 0

    def get_key(self):
        """Get a single keypress from terminal"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)
            if key == "\x1b":
                key += sys.stdin.read(2)
            return key
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def show_menu(self, title, options, descriptions=None):
        """Show interactive menu with arrow navigation"""
        while True:

            os.system("clear" if os.name == "posix" else "cls")

            print(f"\n{title}")
            print("=" * len(title))
            print("Use ↑/↓ arrows to navigate, Enter to select, q to quit\n")

            for i, option in enumerate(options):
                prefix = "→ " if i == self.selected else "  "
                suffix = (
                    f" - {descriptions[i]}"
                    if descriptions and i < len(descriptions)
                    else ""
                )
                if i == self.selected:
                    print(f"\033[1;32m{prefix}{option}{suffix}\033[0m")
                else:
                    print(f"{prefix}{option}{suffix}")

            key = self.get_key()

            if key == "\x1b[A":
                self.selected = (self.selected - 1) % len(options)
            elif key == "\x1b[B":
                self.selected = (self.selected + 1) % len(options)
            elif key == "\r" or key == "\n":
                return self.selected
            elif key.lower() == "q" or key == chr(3):
                exit()


class CapabilityChecker:
    """Check availability of merge tools and capabilities"""

    def __init__(self):
        self.installer = ToolInstaller()

    @staticmethod
    def check_tool(tool_name):
        """Check if a tool is available in PATH"""
        try:
            result = subprocess.run(
                [tool_name, "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ):
            return False

    @staticmethod
    def check_java():
        """Check if Java is available"""
        try:
            result = subprocess.run(
                ["java", "-version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def find_apkeditor(self):
        """Find APKEditor.jar in common locations including installed tools"""

        installed_path = self.installer.get_tool_path("apkeditor")
        if installed_path and installed_path.exists():
            return str(installed_path)

        paths = [
            "APKEditor.jar",
            "apkeditor.jar",
            "tools/APKEditor.jar",
            os.path.expanduser("~/APKEditor.jar"),
            "/usr/local/bin/APKEditor.jar",
        ]
        return next((path for path in paths if os.path.exists(path)), None)

    def find_uber_signer(self):
        """Find uber-apk-signer.jar"""
        installed_path = self.installer.get_tool_path("uber_signer")
        if installed_path and installed_path.exists():
            return str(installed_path)

        paths = [
            "uber-apk-signer.jar",
            "tools/uber-apk-signer.jar",
            os.path.expanduser("~/uber-apk-signer.jar"),
        ]
        return next((path for path in paths if os.path.exists(path)), None)

    def check_adb(self):
        """Check if ADB is available and device connected"""

        adb_cmd = "adb"
        adb_available = False

        try:
            result = subprocess.run(
                [adb_cmd, "version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                adb_available = True
        except:

            installed_adb = self.installer.get_tool_path("adb")
            if installed_adb and installed_adb.exists():
                adb_cmd = str(installed_adb)
                try:
                    result = subprocess.run(
                        [adb_cmd, "version"], capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        adb_available = True
                except:
                    pass

        if not adb_available:
            return False, "ADB not found"

        try:
            result = subprocess.run(
                [adb_cmd, "devices"], capture_output=True, text=True, timeout=10
            )
            if "device" in result.stdout and "offline" not in result.stdout:
                return True, "ADB ready with connected device"
            else:
                return False, "No device connected to ADB"
        except:
            return False, "ADB connection failed"

    def get_available_methods(self):
        """Get list of available merge methods with their status"""
        methods = []

        methods.append(
            {
                "id": 1,
                "name": "XAPK bundle",
                "description": "Create XAPK file (recommended)",
                "available": True,
                "status": "Always available",
            }
        )

        methods.append(
            {
                "id": 2,
                "name": "APKS bundle",
                "description": "Create APKS file",
                "available": True,
                "status": "Always available",
            }
        )

        java_available = self.check_java()
        apkeditor_path = self.find_apkeditor()
        apkeditor_available = java_available and apkeditor_path is not None

        status = "Ready" if apkeditor_available else []
        if not java_available:
            status.append("Java not found")
        if not apkeditor_path:
            status.append("APKEditor.jar not found")
        status = " | ".join(status) if isinstance(status, list) else status

        methods.append(
            {
                "id": 3,
                "name": "APKEditor merge",
                "description": "Merge using APKEditor",
                "available": apkeditor_available,
                "status": status,
            }
        )

        adb_available, adb_status = self.check_adb()
        methods.append(
            {
                "id": 4,
                "name": "Install via ADB",
                "description": "Direct install to device",
                "available": adb_available,
                "status": adb_status,
            }
        )

        uber_signer_path = self.find_uber_signer()

        if uber_signer_path and java_available:
            full_merge_available = True
            status = "Ready with Uber APK Signer"
        else:
            full_merge_available = False
            missing = ["uber-apk-signer"]
            if not java_available:
                missing.append("Java")
            status = f"Missing: {', '.join(missing)}"

        methods.append(
            {
                "id": 5,
                "name": "Full merge + resign",
                "description": "Complete merge and sign",
                "available": full_merge_available,
                "status": status,
            }
        )

        return methods


class ProgressBar:
    def __init__(self, total_size, filename):
        self.total_size = total_size
        self.filename = filename
        self.downloaded = 0
        self.start_time = time.time()
        self.last_update = 0

    def update(self, chunk_size):
        self.downloaded += chunk_size
        current_time = time.time()

        if current_time - self.last_update > 0.2:
            self.last_update = current_time
            progress = (
                (self.downloaded / self.total_size) * 100 if self.total_size > 0 else 0
            )
            speed = self.downloaded / (current_time - self.start_time)

            speed_str = (
                f"{speed/1024/1024:.1f} MB/s"
                if speed > 1024 * 1024
                else f"{speed/1024:.1f} KB/s"
            )
            downloaded_mb = self.downloaded / 1024 / 1024
            total_mb = self.total_size / 1024 / 1024

            bar_length = 30
            filled_length = int(bar_length * progress / 100)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)

            print(
                f"\r{self.filename}: [{bar}] {progress:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f}MB) {speed_str}",
                end="",
            )

    def finish(self):
        print()


class SplitManager:
    def __init__(self, package_name):
        self.package_name = package_name
        self.base_apk = None
        self.splits = []
        self.checker = CapabilityChecker()

    def add_files(self, base_apk, splits):
        self.base_apk = base_apk
        self.splits = splits

    def merge(self, method=None):
        if method is None:
            method = self.choose_merge_method()

        if method is None:
            return None

        try:
            methods = {
                1: self._create_xapk,
                2: self._create_apks,
                3: self._use_apkeditor,
                4: self._install_adb,
                5: self._full_merge,
            }
            return methods[method]()
        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            self._cleanup()

    def choose_merge_method(self):
        """Interactive method selection with capability checking"""
        available_methods = self.checker.get_available_methods()

        enabled_methods = [m for m in available_methods if m["available"]]

        if not enabled_methods:
            print("❌ No merge methods available!")
            return None

        menu = InteractiveMenu()

        options = []
        descriptions = []
        method_ids = []

        for method in available_methods:
            if method["available"]:
                options.append(f"✅ {method['name']}")
                descriptions.append(f"{method['description']} ({method['status']})")
                method_ids.append(method["id"])
            else:
                options.append(f"❌ {method['name']}")
                descriptions.append(f"{method['description']} - {method['status']}")

        print(f"\n📱 Choose merge method for {self.package_name}:")
        print("\n🔍 Checking available tools...")

        for method in available_methods:
            status_icon = "✅" if method["available"] else "❌"
            print(f"{status_icon} {method['name']}: {method['status']}")

        input("\nPress Enter to continue to selection menu...")

        available_options = [f"{m['name']}" for m in enabled_methods]
        available_descriptions = [
            f"{m['description']} ({m['status']})" for m in enabled_methods
        ]
        available_ids = [m["id"] for m in enabled_methods]

        choice = menu.show_menu(
            f"Select merge method for {self.package_name}",
            available_options,
            available_descriptions,
        )

        if choice is not None:
            return available_ids[choice]
        return None

    def _create_xapk(self):
        output = f"{self.package_name}.xapk"
        print(f"Creating XAPK: {output}")

        with zipfile.ZipFile(output, "w") as xapk:
            if self.base_apk:
                xapk.write(self.base_apk, "base.apk")

            for i, split in enumerate(self.splits):
                xapk.write(split, f"config.{i}.apk")

            manifest = {
                "xapk_version": 2,
                "package_name": self.package_name,
                "name": self.package_name,
            }
            xapk.writestr("manifest.json", json.dumps(manifest))

        print(f"✓ Created: {output}")
        return output

    def _create_apks(self):
        output = f"{self.package_name}.apks"
        print(f"Creating APKS: {output}")

        with zipfile.ZipFile(output, "w") as apks:
            if self.base_apk:
                apks.write(self.base_apk, "base-master.apk")

            for i, split in enumerate(self.splits):
                apks.write(split, f"base-{i}.apk")

        print(f"✓ Created: {output}")
        return output

    def _use_apkeditor(self):
        apkeditor = self.checker.find_apkeditor()
        if not apkeditor:
            print("Error: APKEditor.jar not found")
            return None

        with tempfile.TemporaryDirectory() as temp_dir:

            if self.base_apk:
                shutil.copy2(self.base_apk, os.path.join(temp_dir, "base.apk"))

            for i, split in enumerate(self.splits):
                shutil.copy2(split, os.path.join(temp_dir, f"split_{i}.apk"))

            output = f"{self.package_name}_merged.apk"
            cmd = ["java", "-jar", apkeditor, "m", "-i", temp_dir, "-o", output]

            if subprocess.run(cmd).returncode == 0:
                print(f"✓ Merged: {output}")
                return output
        return None

    def _install_adb(self):
        cmd = ["adb", "install-multiple", self.base_apk] + self.splits

        if subprocess.run(cmd).returncode == 0:
            print("✓ Installed via ADB")
            return "INSTALLED"
        return None

    def _full_merge(self):
        """Full merge using direct ZIP manipulation and Uber APK Signer"""
        uber_signer = self.checker.find_uber_signer()

        if not uber_signer:
            print("Error: uber-apk-signer.jar not found")
            return None

        merged_output = f"{self.package_name}_merged.apk"

        try:
            print("🔧 Merging APK splits using ZIP manipulation...")

            with zipfile.ZipFile(
                merged_output, "w", zipfile.ZIP_DEFLATED
            ) as merged_zip:

                if self.base_apk and os.path.exists(self.base_apk):
                    with zipfile.ZipFile(self.base_apk, "r") as base_zip:
                        for file_info in base_zip.infolist():

                            if not file_info.filename.startswith("META-INF/"):
                                file_data = base_zip.read(file_info.filename)
                                merged_zip.writestr(file_info, file_data)

                for i, split_file in enumerate(self.splits):
                    if os.path.exists(split_file):
                        print(f"  📦 Processing split {i+1}/{len(self.splits)}")
                        with zipfile.ZipFile(split_file, "r") as split_zip:
                            for file_info in split_zip.infolist():

                                if (
                                    not file_info.filename.startswith("META-INF/")
                                    and file_info.filename != "AndroidManifest.xml"
                                ):

                                    try:

                                        merged_zip.getinfo(file_info.filename)
                                        print(
                                            f"    ⚠️  Skipping duplicate: {file_info.filename}"
                                        )
                                    except KeyError:

                                        file_data = split_zip.read(file_info.filename)
                                        merged_zip.writestr(file_info, file_data)

            print("✅ APK merge completed")

            print("🔏 Signing APK with Uber APK Signer...")
            final_output = f"{self.package_name}_signed.apk"

            sign_cmd = [
                "java",
                "-jar",
                uber_signer,
                "--overwrite",
                "--allowResign",
                "-a",
                merged_output,
            ]

            result = subprocess.run(sign_cmd, capture_output=True, text=True)

            if result.returncode == 0:

                possible_outputs = [
                    f"{self.package_name}_merged-aligned-debugSigned.apk",
                    f"{self.package_name}_merged-debugSigned.apk",
                    merged_output.replace(".apk", "-aligned-debugSigned.apk"),
                    merged_output.replace(".apk", "-debugSigned.apk"),
                ]

                signed_file = None
                for output_file in possible_outputs:
                    if os.path.exists(output_file):
                        signed_file = output_file
                        break

                if signed_file:

                    os.rename(signed_file, final_output)

                    if os.path.exists(merged_output):
                        os.remove(merged_output)

                    print(f"✅ Signed and saved: {final_output}")
                    return final_output
                else:
                    print(
                        "⚠️  Signing completed but output file not found in expected location"
                    )
                    print(
                        f"   Check directory for files starting with: {self.package_name}_merged"
                    )
                    return merged_output
            else:
                print(f"❌ Uber APK Signer failed: {result.stderr}")
                return merged_output

        except Exception as e:
            print(f"❌ Merge failed: {e}")
            return None

    def _cleanup(self):
        files = [self.base_apk] + self.splits
        for file in files:
            if file and os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass


class Downloader:
    def __init__(self):
        self.chunk_size = 8192
        self.max_retries = 3

    def download_file(self, url, filename):
        for attempt in range(self.max_retries):
            try:
                response = requests.head(url, timeout=10)
                total_size = int(response.headers.get("content-length", 0))

                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()

                progress = ProgressBar(total_size, filename)

                with open(filename, "wb") as file:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            file.write(chunk)
                            progress.update(len(chunk))

                progress.finish()
                return True

            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"Retry {attempt + 1}...")
                    time.sleep(1)
                else:
                    print(f"Download failed: {e}")
                    return False
        return False

    def download_app(self, download_info, package_name, merge_method=None):
        if "fullPathUrls" in download_info:
            return self._download_bazaar_format(
                download_info, package_name, merge_method
            )
        elif "uriPath" in download_info:
            return self._download_myket_format(
                download_info, package_name, merge_method
            )
        return False

    def _download_bazaar_format(self, download_info, package_name, merge_method):
        base_filename = f"{package_name}_base.apk"
        if not self._download_from_urls(
            download_info.get("fullPathUrls", []), base_filename
        ):
            return False

        split_files = []
        splits = download_info.get("splits", [])

        if splits:
            print(f"Downloading {len(splits)} split files...")

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []

                for i, split in enumerate(splits):
                    split_filename = f"{package_name}_split_{i}.apk"
                    future = executor.submit(
                        self._download_from_urls, split["fullPathUrls"], split_filename
                    )
                    futures.append((future, split_filename))

                for future, filename in futures:
                    if future.result():
                        split_files.append(filename)

        return self._handle_merge_or_rename(
            base_filename, split_files, package_name, merge_method
        )

    def _download_myket_format(self, download_info, package_name, merge_method):
        base_filename = f"{package_name}_base.apk"
        base_urls = [
            server + download_info["uriPath"] for server in download_info["uriServers"]
        ]

        if not self._download_from_urls(base_urls, base_filename):
            return False

        split_files = []
        splits = download_info.get("split", [])

        if splits:
            print(f"Downloading {len(splits)} Myket split files...")

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []

                for i, split in enumerate(splits):
                    split_filename = f"{package_name}_{split['type']}"
                    split_urls = [
                        server + split["uriPath"] for server in split["uriServers"]
                    ]
                    future = executor.submit(
                        self._download_from_urls, split_urls, split_filename
                    )
                    futures.append((future, split_filename))

                for future, filename in futures:
                    if future.result():
                        split_files.append(filename)

        return self._handle_merge_or_rename(
            base_filename, split_files, package_name, merge_method
        )

    def _handle_merge_or_rename(
        self, base_filename, split_files, package_name, merge_method
    ):
        if split_files:
            manager = SplitManager(package_name)
            manager.add_files(base_filename, split_files)
            result = manager.merge(merge_method)
            return result is not None
        else:
            final_name = f"{package_name}.apk"
            os.rename(base_filename, final_name)
            print(f"✓ Downloaded: {final_name}")
            return True

    def _download_from_urls(self, urls, filename):
        return any(self.download_file(url, filename) for url in urls)


class Main:
    def __init__(self, architecture="arm64", store_preference="both"):
        self.architecture = architecture
        self.arch_config = ARCHITECTURES[architecture]
        self.store_preference = store_preference
        self.config_dir = get_user_config_dir()
        self.config_path = self.config_dir / "config.json"
        self.menu = InteractiveMenu()
        self.installer = ToolInstaller()
        self.first_run_check()
        self.load_config()

    def first_run_check(self):
        """Check if this is first run and setup tools if needed"""
        if not self.config_path.exists():
            print("🎉 Welcome to Iranian App Store Downloader!")
            print("This appears to be your first run. Let's set up the tools.\n")

            can_use_interactive = hasattr(sys.stdin, "fileno")

            if can_use_interactive:
                try:
                    import termios

                    termios.tcgetattr(sys.stdin.fileno())
                except (ImportError, OSError):
                    can_use_interactive = False

            if can_use_interactive:
                self.installer.setup_tools_interactive()
            else:
                print(
                    "⚙️ Interactive setup not available. Please install tools manually:"
                )
                print("   - Java JDK 11+ for APKEditor and Uber APK Signer")
                print("   - Android SDK Build Tools for ADB and signing tools")
                print("   - Download APKEditor.jar and uber-apk-signer.jar manually")
                input("\nPress Enter to continue...")

    def load_config(self):
        if self.config_path.exists():
            with open(self.config_path) as f:
                config = json.load(f)
            self.myket = Myket(config.get("myket"), self.arch_config["abis"])
        else:
            self.myket = Myket(None, self.arch_config["abis"])
            config = {"myket": self.myket.token}
            with open(self.config_path, "w") as f:
                json.dump(config, f)

    def search(self, query):
        print(f"Searching for: {query}")
        print(f"Architecture: {self.architecture} - {self.arch_config['tag']}")
        print(f"Store: {STORES[self.store_preference]}")
        print("-" * 50)

        results = {}

        if self.store_preference in ["both", "myket"]:
            try:
                myket_results = self.myket.search(query)
                for pkg, info in myket_results.items():
                    results[pkg] = {
                        "name": info["name"],
                        "myket_version": info["version"],
                        "bazaar_version": None,
                        "store": "Myket",
                    }
            except Exception as e:
                print(f"Myket search failed: {e}")

        if self.store_preference in ["both", "bazaar"]:
            try:
                bazaar_results = Bazaar(self.arch_config["cpu"]).search(query)
                for pkg, info in bazaar_results.items():
                    if pkg in results:
                        results[pkg]["bazaar_version"] = info["version"]
                        results[pkg]["store"] = "Both"
                    else:
                        results[pkg] = {
                            "name": info["name"],
                            "myket_version": None,
                            "bazaar_version": info["version"],
                            "store": "Bazaar",
                        }
            except Exception as e:
                print(f"Bazaar search failed: {e}")

        return results

    def format_version_info(self, info):
        myket_v, bazaar_v = info["myket_version"], info["bazaar_version"]

        if myket_v and bazaar_v:
            if myket_v > bazaar_v:
                return f"Myket: {myket_v} ⭐ | Bazaar: {bazaar_v}"
            elif bazaar_v > myket_v:
                return f"Myket: {myket_v} | Bazaar: {bazaar_v} ⭐"
            else:
                return f"Myket: {myket_v} | Bazaar: {bazaar_v}"
        elif myket_v:
            return f"Myket: {myket_v}"
        elif bazaar_v:
            return f"Bazaar: {bazaar_v}"
        return ""

    def interactive_search(self, query=None):
        if not query:
            query = input("Search: ").strip()

        if not query:
            return

        results = self.search(query)
        if not results:
            print("No results found")
            return

        packages = list(results.keys())
        options = []
        descriptions = []

        for pkg in packages:
            info = results[pkg]
            options.append(info["name"])
            version_str = self.format_version_info(info)
            descriptions.append(f"{pkg} - {version_str}")

        choice = self.menu.show_menu("Search Results", options, descriptions)

        if choice is not None:
            selected_pkg = packages[choice]
            selected_info = results[selected_pkg]

            if selected_info["myket_version"] and selected_info["bazaar_version"]:
                store_choice = self.choose_store_for_download(selected_info)
                self.download(selected_pkg, store_choice=store_choice)
            else:
                self.download(selected_pkg)

    def choose_store_for_download(self, info):
        options = []
        descriptions = []

        myket_str = f"Myket (version: {info['myket_version']})"
        bazaar_str = f"Bazaar (version: {info['bazaar_version']})"

        if info["myket_version"] > info["bazaar_version"]:
            myket_str += " ⭐ (newer)"
        elif info["bazaar_version"] > info["myket_version"]:
            bazaar_str += " ⭐ (newer)"

        options = [myket_str, bazaar_str]

        choice = self.menu.show_menu("Choose Store", options)

        if choice == 0:
            return "myket"
        elif choice == 1:
            return "bazaar"
        return None

    def download(self, package_name, merge_method=None, store_choice=None):
        print(f"\nGetting download links for: {package_name}")
        print(f"Architecture: {self.architecture} - {self.arch_config['tag']}")

        if store_choice == "myket":
            stores_to_try = ["myket"]
        elif store_choice == "bazaar":
            stores_to_try = ["bazaar"]
        elif self.store_preference == "myket":
            stores_to_try = ["myket"]
        elif self.store_preference == "bazaar":
            stores_to_try = ["bazaar"]
        else:
            stores_to_try = ["bazaar", "myket"]

        for store in stores_to_try:
            if store == "bazaar":
                try:
                    print("Trying Bazaar...")
                    bazaar_info = Bazaar(self.arch_config["cpu"]).get_download_link(
                        package_name
                    )
                    if isinstance(bazaar_info, dict) and not bazaar_info.get(
                        "translatedMessage"
                    ):
                        print("Found Bazaar download info")
                        downloader = Downloader()
                        if downloader.download_app(
                            bazaar_info, package_name, merge_method
                        ):
                            return
                except Exception as e:
                    print(f"Bazaar failed: {e}")

            elif store == "myket":
                try:
                    print("Trying Myket...")
                    myket_info = self.myket.get_download_link(package_name)
                    if (
                        isinstance(myket_info, dict)
                        and myket_info.get("resultCode") == "Successful"
                    ):
                        print("Found Myket download info")
                        downloader = Downloader()
                        if downloader.download_app(
                            myket_info, package_name, merge_method
                        ):
                            return
                    elif isinstance(myket_info, list):
                        downloader = Downloader()
                        filename = f"{package_name}.apk"
                        if downloader._download_from_urls(myket_info, filename):
                            print(f"✓ Downloaded: {filename}")
                            return
                except Exception as e:
                    print(f"Myket failed: {e}")

        print("All sources failed")


class Bazaar:
    def __init__(self, cpu="arm64-v8a,armeabi-v7a,armeabi"):
        self.cpu = cpu

    def get_download_link(self, package_name):
        response = requests.post(
            "https://api.cafebazaar.ir/rest-v1/process/AppDownloadInfoRequest",
            json={
                "properties": {
                    "androidClientInfo": {"cpu": self.cpu, "sdkVersion": 33},
                    "clientVersionCode": 2300300,
                },
                "singleRequest": {
                    "appDownloadInfoRequest": {
                        "packageName": package_name,
                        "referrers": [],
                    }
                },
            },
        ).json()

        return (
            response["properties"]["errorMessage"]
            if response["properties"]
            else response["singleReply"]["appDownloadInfoReply"]
        )

    def search(self, query, offset=0):
        response = requests.post(
            "https://api.cafebazaar.ir/rest-v1/process/SearchBodyV2Request",
            headers={
                "User-Agent": "Bazaar/2600200 (Android 35; Xiaomi 2311DRK48G)",
                "x-device-info": "PHONE/arm64-v8a|GMS",
            },
            json={
                "singleRequest": {
                    "searchBodyV2Request": {
                        "query": query,
                        "offset": offset,
                        "language": "fa",
                        "scope": "app",
                    }
                }
            },
        ).json()

        if response.get("properties", {}).get("errorMessage"):
            return {}

        results = {}
        for item in response["singleReply"]["searchBodyV2Reply"]["pageBody"]["rows"]:
            if (
                not item.get("appItemWithCustomDetail")
                or item["appItemWithCustomDetail"]["isAd"]
            ):
                continue
            info = item["appItemWithCustomDetail"]["info"]
            results[info["packageName"]] = {
                "name": info["name"],
                "version": info["versionCode"],
            }
        return results


class Myket:
    AES_KEY = bytes.fromhex("51863A124995CA387F6199A397582D7E")
    SALT_HASH = b"NZe*x:38_Jh@#LM6)!9&wb5:32D"
    UUID = str(uuid.uuid4()).encode()

    def __init__(self, token=None, supported_abis=None):
        self.session = requests.Session()
        self.session.headers.update({"Myket-Version": "963"})
        self.supported_abis = supported_abis or ["arm64-v8a", "armeabi-v7a", "armeabi"]
        self.servers = self.get_servers()
        self.token = token if token else self.auth()
        self.session.headers.update({"Authorization": self.token})

    def auth(self):
        data = {
            "acId": "",
            "acKey": "",
            "api": "33",
            "adId": "de46304b-89ac-4ffa-a9bf-4ecc9ee9c857",
            "andId": "8f2ff66584cc50ef",
            "hsh": sha1(
                b"-".join([self.SALT_HASH, self.UUID, b"", b"", b""])
            ).hexdigest(),
            "supportedAbis": self.supported_abis,
            "uuid": self.UUID.decode(),
        }
        return self.session.post(
            "https://apiserver.myket.ir/v1/devices/authorize/", json=data
        ).json()["token"]

    def get_servers(self):
        return self.session.get("https://apiserver.myket.ir/v1/apiservers/").json()

    def search(self, query, offset=0):
        response = self.session.get(
            random.choice(self.servers["asl"])[:-3] + "/v2/applications/search/",
            params={"limit": 20, "offset": offset, "query": query, "tab": "app_app"},
        ).json()

        results = {}
        for item in response["items"]:
            if item["app"]["application"].get("adInfo", False):
                continue
            app = item["app"]["application"]
            results[app["packageName"]] = {
                "name": app["englishTitle"],
                "version": app["versionCode"],
            }
        return results

    def get_download_link(self, package_name):
        info = self.session.get(
            random.choice(self.servers["asl"])[:-3] + f"/v2/applications/{package_name}"
        ).json()

        if info.get("translatedMessage"):
            return info["translatedMessage"]

        version = info["version"]["code"]
        uri_info = self.session.post(
            random.choice(self.servers["asl"])[:-3]
            + f"/v2/applications/{package_name}/uri",
            json={"requestedVersion": version},
        ).json()

        if uri_info.get("resultCode") == "Successful" and (
            "split" in uri_info or "uriPath" in uri_info
        ):
            return uri_info

        if "uriServers" in uri_info and "uriPath" in uri_info:
            return [
                server[:-1] + uri_info["uriPath"] for server in uri_info["uriServers"]
            ]

        return "No download links found"


def choose_architecture():
    """Interactive architecture selection with arrow keys"""
    menu = InteractiveMenu()
    archs = list(ARCHITECTURES.keys())
    options = [f"{arch}" for arch in archs]
    descriptions = [ARCHITECTURES[arch]["tag"] for arch in archs]

    choice = menu.show_menu("Choose Architecture", options, descriptions)

    if choice is not None:
        return archs[choice]
    return "arm64"


def choose_store():
    """Interactive store selection with arrow keys"""
    menu = InteractiveMenu()
    stores = list(STORES.keys())
    options = [STORES[store] for store in stores]

    choice = menu.show_menu("Choose Store Preference", options)

    if choice is not None:
        return stores[choice]
    return "both"


def show_capabilities():
    """Show system capabilities and requirements"""
    print("\n🔍 Checking System Capabilities...")
    print("=" * 50)

    checker = CapabilityChecker()
    methods = checker.get_available_methods()

    available_count = sum(1 for m in methods if m["available"])
    total_count = len(methods)

    print(f"\n📊 Available Methods: {available_count}/{total_count}")
    print("-" * 30)

    for method in methods:
        status_icon = "✅" if method["available"] else "❌"
        print(f"{status_icon} {method['name']}: {method['status']}")

    print(f"\n📁 Tools Directory: {get_user_config_dir() / 'tools'}")
    print("-" * 20)

    installer = ToolInstaller()

    apkeditor_path = installer.get_tool_path("apkeditor")
    if apkeditor_path and apkeditor_path.exists():
        print(f"✅ APKEditor: {apkeditor_path}")
    else:
        print("❌ APKEditor: Not installed")

    uber_signer_path = installer.get_tool_path("uber_signer")
    if uber_signer_path and uber_signer_path.exists():
        print(f"✅ Uber APK Signer: {uber_signer_path}")
    else:
        print("❌ Uber APK Signer: Not installed")

    adb_path = installer.get_tool_path("adb")

    if CapabilityChecker().check_adb():
        if adb_path and adb_path.exists():
            print(f"✅ ADB: {adb_path} (local)")
        else:
            print(f"✅ ADB: ADB (system-wide)")
    else:
        print("❌ ADB: Not installed")
    print("\n💡 Installation Tips:")
    print("-" * 20)

    if not checker.check_java():
        print("📋 Install Java: sudo apt install openjdk-11-jdk  # Ubuntu/Debian")
        print("                brew install openjdk@11          # macOS")

    print("📋 Run with --setup to install missing tools automatically")
    print("📋 Tools are installed to your user config directory")

    input("\nPress Enter to continue...")


def setup_tools():
    """Setup tools interactively"""
    installer = ToolInstaller()
    installer.setup_tools_interactive()


def main():
    parser = argparse.ArgumentParser(
        description="Iranian App Store Downloader with Enhanced Capabilities"
    )
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("-d", "--download", help="Download package directly")
    parser.add_argument(
        "-m", "--method", type=int, choices=[1, 2, 3, 4, 5], help="Merge method (1-5)"
    )
    parser.add_argument(
        "-a", "--arch", choices=["arm64", "arm32", "x86", "x86_64"], help="Architecture"
    )
    parser.add_argument(
        "-s", "--store", choices=["both", "myket", "bazaar"], help="Store preference"
    )
    parser.add_argument(
        "-c", "--check", action="store_true", help="Check system capabilities"
    )
    parser.add_argument(
        "--setup", action="store_true", help="Setup tools interactively"
    )
    parser.add_argument(
        "--no-interactive", action="store_true", help="Disable interactive menus"
    )
    parser.add_argument(
        "--config-dir", action="store_true", help="Show config directory path"
    )

    args = parser.parse_args()

    try:

        if args.config_dir:
            print(f"Config directory: {get_user_config_dir()}")
            return

        if args.setup:
            setup_tools()
            return

        if args.check:
            show_capabilities()
            return

        can_use_interactive = not args.no_interactive and hasattr(sys.stdin, "fileno")

        if can_use_interactive:
            try:

                import termios

                termios.tcgetattr(sys.stdin.fileno())
            except (ImportError, OSError):
                can_use_interactive = False
                print("⚠️  Interactive menus not available. Using fallback mode.")

        if args.arch:
            architecture = args.arch
        elif can_use_interactive:
            architecture = choose_architecture()
        else:
            print("\nAvailable architectures:")
            archs = list(ARCHITECTURES.keys())
            for i, arch in enumerate(archs):
                print(f"{i+1}. {arch} - {ARCHITECTURES[arch]['tag']}")

            while True:
                try:
                    choice = int(input("Choose architecture (1-4): ")) - 1
                    if 0 <= choice < len(archs):
                        architecture = archs[choice]
                        break
                    print("Please enter 1-4")
                except:
                    print("Please enter a valid number")

        if args.store:
            store_preference = args.store
        elif can_use_interactive:
            store_preference = choose_store()
        else:
            print("\nAvailable stores:")
            stores = list(STORES.keys())
            for i, store in enumerate(stores):
                print(f"{i+1}. {STORES[store]}")

            while True:
                try:
                    choice = int(input("Choose store (1-3): ")) - 1
                    if 0 <= choice < len(stores):
                        store_preference = stores[choice]
                        break
                    print("Please enter 1-3")
                except:
                    print("Please enter a valid number")

        app = Main(architecture, store_preference)

        print(f"\n🔧 System Status:")
        checker = CapabilityChecker()
        methods = checker.get_available_methods()
        available_count = sum(1 for m in methods if m["available"])
        print(f"   Available merge methods: {available_count}/{len(methods)}")
        print(f"   Config directory: {get_user_config_dir()}")

        if available_count < len(methods):
            print(f"   💡 Use --check to see requirements or --setup to install tools")

        if args.download:
            app.download(args.download, args.method)
        elif args.query:
            app.interactive_search(args.query)
        else:
            app.interactive_search()

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        if "--debug" in sys.argv:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
