# Iranian App Store Downloader

🚀 A powerful command-line tool for downloading Android apps from Iranian app stores (Myket and CafeBazaar) with advanced APK merging capabilities.

## ✨ Features

- **Multi-Store Support**: Download from both Myket and CafeBazaar
- **Architecture Selection**: Support for ARM64, ARM32, x86, and x86_64
- **Advanced APK Merging**: 5 different merge methods for split APKs
- **Interactive Interface**: Beautiful terminal UI with arrow key navigation
- **Automatic Tool Installation**: Downloads and sets up required tools automatically
- **Progress Tracking**: Real-time download progress with speed indicators
- **Cross-Platform**: Works on Linux, macOS, and Windows

## 🛠️ Installation

### Prerequisites

- **Python 3.7+**
- **Java JDK 11+** (for APK processing tools)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/SafaSafari/Iran_Market.git
cd Iran_Market

# Install dependencies
pip install requests

# Run the tool
python main.py
```

On first run, the tool will automatically offer to download and install required tools.

## 🎯 Usage

### Interactive Mode (Recommended)

```bash
# Search and download interactively
python main.py

# Search for a specific app
python main.py "instagram"
```

### Command Line Mode

```bash
# Direct download
python main.py -d com.instagram.android

# Specify architecture and store
python main.py -a arm64 -s myket "telegram"

# Use specific merge method
python main.py -d com.whatsapp -m 3
```

### Command Line Options

```bash
Options:
  -d, --download PACKAGE    Download package directly
  -m, --method {1,2,3,4,5}  Merge method (1-5)
  -a, --arch {arm64,arm32,x86,x86_64}  Architecture
  -s, --store {both,myket,bazaar}  Store preference
  -c, --check               Check system capabilities
  --setup                   Setup tools interactively
  --no-interactive          Disable interactive menus
  --config-dir              Show config directory path
```

## 📱 Supported Architectures

| Architecture | Target Devices | ABI Support |
|--------------|----------------|-------------|
| **arm64** | Modern phones | arm64-v8a, armeabi-v7a, armeabi |
| **arm32** | Chinese/old phones | armeabi-v7a, armeabi |
| **x86** | Emulator (32-bit) | x86 |
| **x86_64** | Emulator (64-bit) | x86_64, x86 |

## 🔧 APK Merge Methods

The tool supports 5 different methods to handle split APKs:

| Method | Description | Requirements | Best For |
|--------|-------------|--------------|----------|
| **1. XAPK Bundle** | Creates XAPK file | None | General use, app installers |
| **2. APKS Bundle** | Creates APKS file | None | SAI, Split APKs Installer |
| **3. APKEditor Merge** | Merges using APKEditor | Java + APKEditor.jar | Single APK output |
| **4. ADB Install** | Direct device install | ADB + connected device | Immediate installation |
| **5. Full Merge + Sign** | Complete merge & resign | Java + Uber APK Signer | Production-ready APK |

## 🏗️ System Requirements

### Required Tools (Auto-installable)

- **APKEditor**: For merging split APKs
- **Uber APK Signer**: For signing merged APKs
- **ADB Platform Tools**: For direct device installation

### Manual Installation

If automatic installation fails, install tools manually:

#### Java (Required)
```bash
# Ubuntu/Debian
sudo apt install openjdk-11-jdk

# macOS
brew install openjdk@11

# Windows
# Download from Oracle or use package managers
```

#### Android SDK Tools (Optional)
```bash
# For ADB and signing tools
# Download Android SDK or platform-tools
```

## 📁 Project Structure

```
Iran_Market/
├── main.py                 # Main application
├── README.md              # This file
└── ~/.config/IranianAppDownloader/  # Config directory
    ├── config.json        # User configuration
    └── tools/             # Auto-downloaded tools
        ├── APKEditor.jar
        ├── uber-apk-signer.jar
        └── platform-tools/
```

## 🔍 Examples

### Search and Download

```bash
# Interactive search
python main.py "بازی"

# Download specific package
python main.py -d ir.tgbs.android

# Download from specific store
python main.py -s bazaar -d com.instagram.android
```

### Architecture-Specific Downloads

```bash
# For modern phones (recommended)
python main.py -a arm64 "telegram"

# For older devices
python main.py -a arm32 "whatsapp"

# For emulator testing
python main.py -a x86_64 "instagram"
```

### Advanced Usage

```bash
# Check system capabilities
python main.py --check

# Setup tools interactively
python main.py --setup

# Non-interactive mode (for scripts)
python main.py --no-interactive -d com.package.name
```

## 🛡️ Security & Privacy

- **Token Management**: Securely stores API tokens locally
- **No Data Collection**: No user data is transmitted to external servers
- **Local Processing**: All APK merging happens locally
- **Open Source**: Full source code available for inspection

## 🔧 Troubleshooting

### Common Issues

**Java not found:**
```bash
# Verify Java installation
java -version

# Install if missing (Ubuntu/Debian)
sudo apt install openjdk-11-jdk
```

**ADB device not found:**
```bash
# Enable USB debugging on your device
# Check connection
adb devices
```

**Download fails:**
```bash
# Try different store
python main.py -s myket -d package.name

# Check internet connection
# Some packages may be region-restricted
```

### Debug Mode

```bash
# Enable debug output
python main.py --debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone for development
git clone https://github.com/SafaSafari/Iran_Market.git
cd Iran_Market

# Install development dependencies
pip install requests

# Run tests
python main.py --check
```

## ⚖️ Legal Notice

This tool is for educational and personal use only. Users are responsible for complying with:

- App store terms of service
- Copyright laws in their jurisdiction
- Software licensing agreements

**Disclaimer**: This project is not affiliated with Myket, CafeBazaar, or any app developers.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **APKEditor** by REAndroid
- **Uber APK Signer** by Patrick Favre-Bulle
- **Android Platform Tools** by Google
- Iranian app store APIs (Myket & CafeBazaar)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/SafaSafari/Iran_Market/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SafaSafari/Iran_Market/discussions)

---

**⭐ Star this project if you find it useful!**

---

## 📊 Quick Reference

### Architecture Matrix
| Device Type | Recommended | Alternative |
|-------------|-------------|-------------|
| Modern Android (2019+) | `arm64` | `arm32` |
| Older Android | `arm32` | - |
| Android Emulator | `x86_64` | `x86` |

### Store Comparison
| Feature | Myket | CafeBazaar |
|---------|-------|------------|
| App Coverage | Moderate | High |
| Update Frequency | Good | Excellent |
| API Stability | Stable | Very Stable |
| Split APK Support | Yes | Yes |

Made with ❤️ by SafaSafari and Claude =))