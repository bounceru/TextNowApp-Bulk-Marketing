"""
TextNow Max Creator - Windows EXE Builder

This script builds a Windows executable (.exe) file for the TextNow Max Creator application.
It uses PyInstaller to create a standalone executable that can be run on any Windows machine.
"""

import os
import sys
import shutil
import subprocess

def clear_build_directories():
    """Clear any existing build directories"""
    print("Clearing build directories...")
    
    for directory in ['build', 'dist']:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            print(f"Removed {directory}/")

def copy_assets():
    """Copy assets to include in the executable"""
    print("Copying assets...")
    
    # Create assets directory in the current directory if it doesn't exist
    if not os.path.exists('assets'):
        os.makedirs('assets')
    
    # Check for assets in attached_assets directory
    for asset in ['progress_logo.png', 'progress_background.jpg']:
        source_path = os.path.join('attached_assets', asset)
        if os.path.exists(source_path):
            dest_path = os.path.join('assets', asset)
            shutil.copy(source_path, dest_path)
            print(f"Copied {source_path} to {dest_path}")

def build_executable():
    """Build the Windows executable"""
    print("Building TextNow Max Creator executable...")
    
    # Create necessary directories if they don't exist
    required_dirs = ['assets', 'static', 'templates', 'voicemail']
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"Creating missing directory: {directory}")
            os.makedirs(directory, exist_ok=True)
    
    # Check for database file
    if not os.path.exists('ghost_accounts.db'):
        print("Creating empty database file")
        with open('ghost_accounts.db', 'w') as f:
            pass  # Create empty file
    
    # Check for ghost names file
    if not os.path.exists('ghost_names_usernames.csv'):
        print("Creating sample names file")
        with open('ghost_names_usernames.csv', 'w') as f:
            f.write("firstname,lastname,username\n")
            f.write("John,Doe,johndoe123\n")
            f.write("Jane,Smith,janesmith456\n")
    
    # Use the correct path separator based on platform
    # Windows uses ';', other platforms use ':'
    separator = ';' if sys.platform.startswith('win') else ':'
    
    # Build the command with only existing directories
    add_data_commands = []
    
    # Add directories only if they exist
    for directory in required_dirs:
        if os.path.exists(directory):
            add_data_commands.append(f'--add-data={directory}{separator}{directory}')
    
    # Add files only if they exist
    for file in ['ghost_accounts.db', 'ghost_names_usernames.csv']:
        if os.path.exists(file):
            add_data_commands.append(f'--add-data={file}{separator}.')
    
    # PyInstaller command with all necessary options
    pyinstaller_command = [
        'pyinstaller',
        f'--name=TextNowMaxCreator',
        '--onefile',  # Create a single executable file
        '--windowed',  # Don't show console window
        f'--icon=assets/progress_logo.png' if os.path.exists('assets/progress_logo.png') else '',  # Application icon
    ]
    
    # Add all data commands to the command
    pyinstaller_command.extend(add_data_commands)
    
    # Add remaining options
    pyinstaller_command.extend([
        '--clean',  # Clean PyInstaller cache
        # Main script to execute
        'fixed_clickable_original.py'
    ])
    
    # Remove empty strings from command
    pyinstaller_command = [cmd for cmd in pyinstaller_command if cmd]
    
    # Run PyInstaller
    try:
        subprocess.run(pyinstaller_command, check=True)
        print("Build successful!")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        sys.exit(1)

def create_portable_version():
    """Create a portable ZIP version"""
    print("Creating portable ZIP version...")
    
    # Files to include in the portable version
    files_to_include = [
        'dist/TextNowMaxCreator.exe',
        'README.md',
        'FEATURES.md',
        'INSTALLATION.md',
        'USAGE_GUIDE.md'
    ]
    
    # Create portable directory
    portable_dir = 'TextNowMaxCreator_Portable'
    if os.path.exists(portable_dir):
        shutil.rmtree(portable_dir)
    os.makedirs(portable_dir)
    
    # Copy files
    for file in files_to_include:
        if os.path.exists(file):
            print(f"Copying {file} to portable directory...")
            shutil.copy(file, portable_dir)
    
    # Create empty folders
    for folder in ['data', 'logs', 'config']:
        os.makedirs(os.path.join(portable_dir, folder), exist_ok=True)
    
    # Create the ZIP file
    shutil.make_archive('TextNowMaxCreator_Portable', 'zip', '.', portable_dir)
    print(f"Created TextNowMaxCreator_Portable.zip")

def create_installer():
    """Create an installer using NSIS"""
    print("NOTE: NSIS installer creation not implemented in this script.")
    print("To create an installer, use the NSIS script provided separately.")
    print("Manual installer creation steps:")
    print("1. Download and install NSIS: https://nsis.sourceforge.io/Download")
    print("2. Open TextNowMaxCreator_Installer.nsi with NSIS")
    print("3. Compile the installer")

def main():
    """Main function"""
    print("=" * 60)
    print("TextNow Max Creator - Windows EXE Builder")
    print("=" * 60)
    
    # Clear build directories
    clear_build_directories()
    
    # Copy assets
    copy_assets()
    
    # Build executable
    build_executable()
    
    # Create portable version
    create_portable_version()
    
    # Create installer
    create_installer()
    
    print("\nBuild process completed!")
    print("Executable location: dist/TextNowMaxCreator.exe")
    print("Portable ZIP: TextNowMaxCreator_Portable.zip")
    print("=" * 60)

if __name__ == "__main__":
    main()