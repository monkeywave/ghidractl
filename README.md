# ghidractl

A Python library and CLI tool to effortlessly install, manage, and automate Ghidra environments.

Install, update, and manage multiple [Ghidra](https://ghidra-sre.org/) versions from the command line — or use it as an importable library in your Python tools.

## Features

- Install/update/uninstall multiple Ghidra versions side-by-side
- Auto-detect and manage Java/JDK dependencies (Adoptium Temurin)
- Cross-platform: macOS (ARM64 + x86-64), Linux, Windows
- Rich terminal UI with progress bars and tables
- Importable Python API for toolchain integration
- Extension and settings management

## Installation

```bash
pip install ghidractl
```

## CLI Usage

```bash
# Install the latest Ghidra
ghidractl install

# Install a specific version
ghidractl install 11.3

# List installed versions
ghidractl list

# List all available versions
ghidractl list --all

# Set active version
ghidractl use 11.3

# Launch Ghidra GUI
ghidractl run

# Update to latest
ghidractl update

# Uninstall a version
ghidractl uninstall 11.2.1

# Print install path
ghidractl locate
```

### Java Management

```bash
# Check Java status
ghidractl java check

# Install JDK via Adoptium
ghidractl java install

# Install a specific JDK version
ghidractl java install --version 17

# Manual install instructions
ghidractl java guide
```

### Extensions

```bash
# List extensions
ghidractl ext list

# Install from ZIP
ghidractl ext install ./my-extension.zip

# Remove an extension
ghidractl ext uninstall MyExtension
```

### Settings

```bash
# Backup Ghidra settings
ghidractl settings backup

# Restore from backup
ghidractl settings restore ghidra_settings_backup.zip
```

### Configuration

```bash
# Show config
ghidractl config show

# Set GitHub token (for higher API rate limits)
ghidractl config set github_token ghp_your_token_here
```

## Library API

```python
import ghidractl

# Install Ghidra
path = ghidractl.install("latest")

# List available versions
versions = ghidractl.list_versions()

# List installed versions
installed = ghidractl.installed()

# Set active version
ghidractl.use("11.3")

# Get install path
path = ghidractl.get_path()

# Launch Ghidra
ghidractl.run()

# Java management
java = ghidractl.java.check()
ghidractl.java.install(version=21)
```

## Requirements

- Python 3.10+
- Java/JDK (auto-installable via `ghidractl java install`)

