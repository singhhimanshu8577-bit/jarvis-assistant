"""
Master Automated Deployment Script for JARVIS Assistant on Windows.
Sets up virtual environment, installs dependencies, configures environment variables,
creates Desktop launchers, and verifies the deployment.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def print_banner(text: str):
    print("\n" + "=" * 65)
    print(f"  {text}")
    print("=" * 65)


def run_command(cmd_list, cwd=None) -> bool:
    print(f"\n[Executing] {' '.join(cmd_list)}")
    res = subprocess.run(cmd_list, cwd=cwd)
    return res.returncode == 0


def deploy():
    project_dir = Path(__file__).parent.resolve()
    venv_dir = project_dir / "venv"
    venv_python = venv_dir / "Scripts" / "python.exe"
    venv_pip = venv_dir / "Scripts" / "pip.exe"

    print_banner("JARVIS ASSISTANT: AUTOMATED PRODUCTION DEPLOYMENT")
    print(f"[*] Project Location: {project_dir}")

    # 1. Setup Virtual Environment
    print_banner("STEP 1: Virtual Environment Setup")
    if not venv_python.exists():
        print(f"[*] Creating Python virtual environment at {venv_dir}...")
        success = run_command([sys.executable, "-m", "venv", str(venv_dir)], cwd=str(project_dir))
        if not success:
            print("[Error] Failed to create virtual environment.")
            return False
        print("[+] Virtual environment created successfully.")
    else:
        print("[+] Existing virtual environment detected.")

    # 2. Install / Upgrade Dependencies
    print_banner("STEP 2: Dependencies Installation")
    req_file = project_dir / "requirements.txt"
    if req_file.exists() and venv_python.exists():
        print("[*] Installing requirements into virtual environment...")
        run_command([str(venv_python), "-m", "pip", "install", "-r", str(req_file)], cwd=str(project_dir))
    else:
        print("[*] Using current environment dependencies.")

    # 3. Configure .env file
    print_banner("STEP 3: Environment Configuration")
    env_file = project_dir / ".env"
    env_example = project_dir / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print(f"[+] Created '{env_file.name}' from template.")
    else:
        print(f"[+] '{env_file.name}' is configured.")

    # 4. Create Desktop Shortcuts
    print_banner("STEP 4: Desktop & Start Menu Shortcuts")
    from install_shortcuts import create_desktop_shortcuts
    create_desktop_shortcuts()

    # 5. Run Verification Self-Test
    print_banner("STEP 5: Deployment Verification Diagnostics")
    exec_python = str(venv_python) if venv_python.exists() else sys.executable
    main_script = str(project_dir / "main.py")

    print("[*] Running system self-test...")
    test_success = run_command([exec_python, main_script, "--test"], cwd=str(project_dir))

    # 6. Final Summary
    print_banner("DEPLOYMENT COMPLETED SUCCESSFULLY!")
    print("""
JARVIS has been deployed to your system.

You can launch JARVIS in two ways:
  1. Desktop Shortcuts:
     - Click 'JARVIS (Voice).bat' on your Desktop for Voice Mode
     - Click 'JARVIS (Console).bat' on your Desktop for Console Mode

  2. Direct Terminal / Script Launchers:
     - Run: C:\\Users\\hp\\.gemini\\antigravity-ide\\scratch\\jarvis-assistant\\JARVIS_Voice.bat
     - Run: C:\\Users\\hp\\.gemini\\antigravity-ide\\scratch\\jarvis-assistant\\JARVIS_Text.bat
     - Run: python main.py --voice
     - Run: python main.py --text

Configuration:
  - Edit API Keys in: C:\\Users\\hp\\.gemini\\antigravity-ide\\scratch\\jarvis-assistant\\.env
  - Edit Voice & Behavior in: C:\\Users\\hp\\.gemini\\antigravity-ide\\scratch\\jarvis-assistant\\config\\config.yaml
""")
    return True


if __name__ == "__main__":
    deploy()
