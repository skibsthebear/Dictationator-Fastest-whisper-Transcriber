#!/usr/bin/env python3
"""
Setup script for Dictationer - Voice Recording System.

This script handles:
1. Virtual environment creation
2. Dependency installation
3. GPU support guidance
4. Installation verification
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_colored(message, color=Colors.RESET):
    """Print colored message to terminal."""
    print(f"{color}{message}{Colors.RESET}")


def print_header(message):
    """Print a formatted header."""
    print()
    print_colored("=" * 60, Colors.CYAN)
    print_colored(message, Colors.CYAN + Colors.BOLD)
    print_colored("=" * 60, Colors.CYAN)
    print()


def get_python_command():
    """Get the appropriate Python command for the OS."""
    if platform.system() in ['Linux', 'Darwin']:  # Darwin is macOS
        return 'python3'
    return 'python'


def get_pip_command():
    """Get the appropriate pip command for the OS."""
    if platform.system() in ['Linux', 'Darwin']:
        return 'pip3'
    return 'pip'


def check_python_version():
    """Check if Python version is 3.8 or higher."""
    if sys.version_info < (3, 8):
        print_colored("❌ Error: Python 3.8 or higher is required.", Colors.RED)
        print_colored(f"   Current version: {sys.version}", Colors.RED)
        sys.exit(1)
    print_colored(f"✓ Python version: {sys.version.split()[0]}", Colors.GREEN)


def create_venv():
    """Create virtual environment if it doesn't exist."""
    venv_path = Path.cwd() / 'venv'
    python_cmd = get_python_command()
    
    if venv_path.exists():
        print_colored("✓ Virtual environment 'venv' already exists", Colors.GREEN)
        return True
    
    print_colored("Creating virtual environment 'venv'...", Colors.YELLOW)
    try:
        subprocess.run([python_cmd, '-m', 'venv', 'venv'], check=True)
        print_colored("✓ Virtual environment created successfully", Colors.GREEN)
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Failed to create virtual environment: {e}", Colors.RED)
        return False


def get_venv_executable(executable):
    """Get the path to an executable in the virtual environment."""
    if platform.system() == 'Windows':
        return Path.cwd() / 'venv' / 'Scripts' / f'{executable}.exe'
    else:
        return Path.cwd() / 'venv' / 'bin' / executable


def show_gpu_instructions():
    """Show GPU support instructions and get user confirmation."""
    print_header("🎮 GPU Support Information")
    
    print_colored("IMPORTANT: GPU Acceleration Setup", Colors.YELLOW + Colors.BOLD)
    print()
    print("For significantly faster transcription with GPU support:")
    print()
    print_colored("1. Install CUDA Toolkit:", Colors.CYAN)
    print("   - Download from: https://developer.nvidia.com/cuda-downloads")
    print("   - Check your CUDA version after installation: nvidia-smi")
    print()
    print_colored("2. Install PyTorch with CUDA support:", Colors.CYAN)
    print("   After this setup completes, activate the venv and run:")
    print()
    print_colored("   # For CUDA 12.1 (latest GPUs):", Colors.GREEN)
    print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
    print()
    print_colored("   # For CUDA 11.8 (older GPUs):", Colors.GREEN)
    print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    print()
    print_colored("   # For CPU only (no GPU):", Colors.GREEN)
    print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu")
    print()
    print_colored("⚠️  Without proper PyTorch + CUDA installation, GPU will not be detected!", Colors.YELLOW)
    print()
    
    # Get user acknowledgment
    while True:
        response = input(f"{Colors.CYAN}Do you understand the GPU requirements? Type 'yes' to continue: {Colors.RESET}").strip().lower()
        if response == 'yes':
            break
        print_colored("Please type 'yes' to acknowledge the GPU setup requirements.", Colors.YELLOW)
    
    print()
    print_colored("📦 This setup will prepare Dictationer for CPU-only mode.", Colors.BLUE)
    print_colored("   GPU will automatically activate if you install PyTorch with CUDA support.", Colors.BLUE)
    print()
    
    input(f"{Colors.CYAN}Press Enter to continue with the setup...{Colors.RESET}")


def install_dependencies():
    """Install dependencies from requirements.txt."""
    print_header("📦 Installing Dependencies")
    
    pip_path = get_venv_executable('pip')
    requirements_file = Path.cwd() / 'requirements.txt'
    
    if not requirements_file.exists():
        print_colored("❌ Error: requirements.txt not found!", Colors.RED)
        return False
    
    print_colored("Installing packages from requirements.txt...", Colors.YELLOW)
    print()
    
    try:
        # Skip pip upgrade - it's not essential and can cause issues on Windows
        # Just install requirements directly
        print_colored("Installing requirements...", Colors.CYAN)
        subprocess.run([str(pip_path), 'install', '-r', 'requirements.txt'], check=True)
        
        print()
        print_colored("✓ All dependencies installed successfully", Colors.GREEN)
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Failed to install dependencies: {e}", Colors.RED)
        return False


def verify_installation():
    """Verify that all required packages are installed."""
    print_header("🔍 Verifying Installation")
    
    python_path = get_venv_executable('python')
    
    # Read requirements from requirements.txt
    requirements = []
    with open('requirements.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (before any version specifiers)
                package = line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0]
                requirements.append(package)
    
    # Map of package names to import names (if different)
    import_map = {
        'pyaudio': 'pyaudio',
        'keyboard': 'keyboard',
        'faster-whisper': 'faster_whisper',
        'watchdog': 'watchdog',
        'pyperclip': 'pyperclip',
        'PySide6': 'PySide6',
        'python-dotenv': 'dotenv',
        'transformers': 'transformers'
    }
    
    all_good = True
    results = []
    
    for package in requirements:
        import_name = import_map.get(package, package)
        try:
            # Test import in the venv Python
            result = subprocess.run(
                [str(python_path), '-c', f'import {import_name}'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                results.append((package, True, "✓ Installed"))
            else:
                results.append((package, False, f"✗ Import failed: {result.stderr.strip()}"))
                all_good = False
        except Exception as e:
            results.append((package, False, f"✗ Error: {str(e)}"))
            all_good = False
    
    # Display results
    print_colored("Package Status:", Colors.BOLD)
    print("-" * 40)
    for package, success, message in results:
        color = Colors.GREEN if success else Colors.RED
        print_colored(f"{package:<20} {message}", color)
    print("-" * 40)
    
    # Check for PyTorch (optional but recommended)
    print()
    print_colored("Checking optional PyTorch installation...", Colors.CYAN)
    try:
        result = subprocess.run(
            [str(python_path), '-c', 
             'import torch; print(f"PyTorch {torch.__version__} - CUDA: {torch.cuda.is_available()}")'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_colored(f"✓ {result.stdout.strip()}", Colors.GREEN)
        else:
            print_colored("✗ PyTorch not installed (GPU acceleration unavailable)", Colors.YELLOW)
            print_colored("  Install PyTorch for GPU support - see instructions above", Colors.YELLOW)
    except Exception:
        print_colored("✗ PyTorch not installed (GPU acceleration unavailable)", Colors.YELLOW)
    
    return all_good


def main():
    """Main setup function."""
    print_colored("""
    🎤 Dictationer Setup Script
    Advanced Voice Recording & Transcription System
    """, Colors.CYAN + Colors.BOLD)
    
    # Check Python version
    check_python_version()
    
    # Create virtual environment
    if not create_venv():
        sys.exit(1)
    
    # Show GPU instructions and get confirmation
    show_gpu_instructions()
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Verify installation
    if verify_installation():
        print_header("✅ Setup Complete!")
        print_colored("Dictationer has been successfully set up!", Colors.GREEN + Colors.BOLD)
        print()
        print("To get started:")
        print()
        
        print_colored("Launch the program with:", Colors.CYAN)
        if platform.system() == 'Windows':
            print("   start.bat")
        else:
            print("   ./start.sh")
        
        print()
        print_colored("For GPU support, remember to install PyTorch with CUDA!", Colors.YELLOW)
    else:
        print_header("⚠️  Setup Completed with Warnings")
        print_colored("Some packages may not have installed correctly.", Colors.YELLOW)
        print_colored("Please check the errors above and try again.", Colors.YELLOW)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_colored("Setup cancelled by user.", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_colored(f"Unexpected error: {e}", Colors.RED)
        sys.exit(1)