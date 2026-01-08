import os
import sys
import shutil
from pathlib import Path
import subprocess

# Ensure using current Python environment
sys.executable = sys.executable

def build_exe():
    # Project root directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Clean up previous build files
    dist_dir = os.path.join(project_dir, 'dist')
    build_dir = os.path.join(project_dir, 'build')
    spec_file = os.path.join(project_dir, 'lightragcoder.spec')
    
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    if os.path.exists(spec_file):
        os.remove(spec_file)
    
    print("Cleanup completed, starting EXE build...")
    
    # PyInstaller build parameters
    pyinstaller_cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        '--onefile',  # Generate single EXE file
        '--name', 'LightRAGCoder',  # Output file name
        '--hidden-import', 'asyncio',  # Ensure asyncio is included
        '--hidden-import', 'queue',  # Ensure queue module is included
        '--hidden-import', 'mcp',  # Ensure mcp is included
        '--hidden-import', 'mcp.server',  # Ensure mcp.server is included
        '--hidden-import', 'mcp.server.lowlevel',  # Ensure mcp.server.lowlevel is included
        '--hidden-import', 'mcp.server.lowlevel.server',  # Ensure mcp.server.lowlevel.server is included
        '--collect-submodules', 'importlib.metadata',  # Ensure importlib.metadata module is included
        '--collect-submodules', 'lightrag_hku',  # Ensure lightrag_hku module is included
        '--collect-submodules', 'tree_sitter',  # Ensure tree_sitter module is included
        '--collect-submodules', 'anthropic',  # Ensure anthropic module is included
        '--collect-submodules', 'openai',  # Ensure openai module is included
        '--collect-submodules', 'google_genai',  # Ensure google_genai module is included
        '--collect-submodules', 'transformers',  # Ensure transformers module is included
        '--collect-submodules', 'torch',  # Ensure torch module is included
        '--collect-submodules', 'numpy',  # Ensure numpy module is included
        '--collect-submodules', 'tokenizers',  # Ensure tokenizers module is included
        '--collect-submodules', 'sentence_transformers',  # Ensure sentence_transformers module is included
        '--collect-submodules', 'faiss',  # Ensure faiss module is included
        '--console',  # Show console window for debugging
        '--clean',  # Clean temporary files
        os.path.join(project_dir, 'lightragcoder.py')  # Main script
    ]
    
    # Execute PyInstaller build command
    try:
        subprocess.run(pyinstaller_cmd, check=True, shell=False)
        print(f"\nBuild successful! Executable file located at: {dist_dir}")
        
        # Copy necessary resource files to dist directory
        print("Copying necessary resource files...")
        
        # Check if .env.example needs to be copied
        env_example_src = os.path.join(project_dir, '.env.example')
        env_example_dst = os.path.join(dist_dir, '.env.example')
        if os.path.exists(env_example_src):
            shutil.copy2(env_example_src, env_example_dst)
            print(f"Copied .env.example to {dist_dir}")
        
        # Prompt user build completion
        print("\n======== Build Completed ========")
        print(f"Executable: {os.path.join(dist_dir, 'lightragcoder.exe')}")
        print("\nUsage:")
        print("1. Copy lightragcoder.exe from dist directory to target machine")
        print("2. Ensure target machine has code directories to analyze")
        print("3. Run in command line: lightragcoder.exe --help for assistance")
        print("\nNotes:")
        print("- No need to install Python on target machine")
        print("- Program will generate symbol database files in working directory")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)
    
if __name__ == '__main__':
    # Check if PyInstaller is installed, install if not
    try:
        import PyInstaller
        print(f"PyInstaller version {PyInstaller.__version__} already installed")
    except ImportError:
        print("PyInstaller not found, installing...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
            print("PyInstaller installation successful")
        except subprocess.CalledProcessError:
            print("PyInstaller installation failed, please install manually and run this script again")
            sys.exit(1)
    
    # Execute build
    build_exe()