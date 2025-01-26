# ~ launch.py | by ANXETY ~

from json_utils import read_json, save_json, update_json
from TunnelHub import Tunnel

from IPython.display import clear_output
from IPython import get_ipython
from datetime import timedelta
from pathlib import Path
import subprocess
import requests
import logging
import shlex
import time
import json
import yaml
import os
import re


CD = os.chdir
ipySys = get_ipython().system

# Constants
HOME = Path.home()
VENV = HOME / 'venv'
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

ENV_NAME = read_json(SETTINGS_PATH, 'ENVIRONMENT.env_name')
UI = read_json(SETTINGS_PATH, 'WEBUI.current')
WEBUI = read_json(SETTINGS_PATH, 'WEBUI.webui_path')

# USER VENV
py = Path(VENV) / 'bin/python3'


def load_settings(path):
    """Load settings from a JSON file."""
    try:
        return {
            **read_json(path, 'ENVIRONMENT'),
            **read_json(path, 'WIDGETS'),
            **read_json(path, 'WEBUI')
        }
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading settings: {e}")
        return {}

def is_package_installed(package_name):
    """Check if a package is installed globally using npm."""
    try:
        subprocess.run(["npm", "ls", "-g", package_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def get_public_ip(version='ipv4'):
    """Retrieve the public IP address."""
    try:
        url = f'https://api64.ipify.org?format=json&{version}=true'
        response = requests.get(url)
        return response.json().get('ip', 'N/A')
    except Exception as e:
        print(f"Error getting public {version} address:", e)
        return None

def update_config_paths(config_path, paths_to_check):
    """Update configuration paths in the specified JSON config file."""
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            config_data = json.load(file)
        for key, expected_value in paths_to_check.items():
            if key in config_data and config_data[key] != expected_value:
                sed_command = f"sed -i 's|\"{key}\": \".*\"|\"{key}\": \"{expected_value}\"|' {config_path}"
                ipySys(sed_command)
                
def trash_checkpoints():
    dirs = ["A1111", "ReForge", "ComfyUI", "Forge"]
    paths = [Path(HOME) / name for name in dirs]

    for path in paths:
        cmd = f"find {path} -type d -name .ipynb_checkpoints -exec rm -rf {{}} +"
        subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
## === Tunnel Functions ===
def _zrok_enable(token):
    zrok_env_path = Path(HOME) / '.zrok/environment.json'

    current_token = None
    if zrok_env_path.exists():
        with open(zrok_env_path, 'r') as f:
            current_token = json.load(f).get('zrok_token')

    if current_token != token:
        ipySys('zrok disable &> /dev/null')
    ipySys(f'zrok enable {token} &> /dev/null')

def _ngrok_auth(token):
    yml_path = Path(ROOT) / '.config/ngrok/ngrok.yml'

    current_token = None
    if yml_path.exists():
        with open(yml_path, 'r') as f:
            current_token = yaml.safe_load(f).get('agent', {}).get('authtoken')

    if current_token != token:
        ipySys(f'ngrok config add-authtoken {token}')
        
def setup_tunnels(tunnel_port, public_ipv4):
    """Setup tunneling commands based on available packages and configurations."""
    tunnels = [
        {
            "command": f"cl tunnel --url localhost:{tunnel_port}",
            "name": "Cloudflared",
            "pattern": re.compile(r"[\w-]+\.trycloudflare\.com")
        },
        {
            "command": f"ssh -o StrictHostKeyChecking=no -p 80 -R0:localhost:{tunnel_port} a.pinggy.io",
            "name": "Pinggy",
            "pattern": re.compile(r"[\w-]+\.a\.free\.pinggy\.link")
        }
    ]

    if is_package_installed('localtunnel'):
        tunnels.append({
            "command": f"lt --port {tunnel_port}",
            "name": "Localtunnel",
            "pattern": re.compile(r"[\w-]+\.loca\.lt"),
            "note": f"Password : \033[32m{public_ipv4}\033[0m rerun cell if 404 error."
        })

    if zrok_token:
        _zrok_enable(zrok_token)
        tunnels.append({
            "command": f"zrok share public http://localhost:{tunnel_port}/ --headless",
            "name": "Zrok",
            "pattern": re.compile(r"[\w-]+\.share\.zrok\.io")
        })
        
    if ngrok_token:
        _ngrok_auth(ngrok_token)
        tunnels.append({
            "command": f"ngrok http http://localhost:{tunnel_port} --log stdout",
            "name": "Ngrok",
            "pattern": re.compile(r"https://[\w-]+\.ngrok-free\.app")
        })

    return tunnels

def start_styles_script():
    """启动styles.py脚本并在后台运行"""
    subprocess.Popen(['python3', '/root/A1111/styles.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

## === Main ===
# Load settings
settings = load_settings(SETTINGS_PATH)
locals().update(settings)

print('Please Wait...')

# Get public IP address
public_ipv4 = read_json(SETTINGS_PATH, "ENVIRONMENT.public_ip", None)
if not public_ipv4:
    public_ipv4 = get_public_ip(version='ipv4')
    update_json(SETTINGS_PATH, "ENVIRONMENT.public_ip", public_ipv4)

tunnel_port = 8188 if UI == 'ComfyUI' else 7860
TunnelingService = Tunnel(tunnel_port)
TunnelingService.logger.setLevel(logging.DEBUG)

# environ
if f'{VENV}/bin' not in os.environ['PATH']:
    os.environ['PATH'] = f'{VENV}/bin:' + os.environ['PATH']
os.environ["PYTHONWARNINGS"] = "ignore"

# Setup tunnels
tunnels = setup_tunnels(tunnel_port, public_ipv4)
for tunnel_info in tunnels:
    TunnelingService.add_tunnel(**tunnel_info)

clear_output()

# Update configuration paths
paths_to_check = {
    "tagger_hf_cache_dir": f"{WEBUI}/models/interrogators/",
    "ad_extra_models_dir": adetailer_dir,
    "sd_checkpoint_hash": "",
    "sd_model_checkpoint": "",
    "sd_vae": "None"
}
update_config_paths(f'{WEBUI}/config.json', paths_to_check)
## Remove '.ipynb_checkpoints' dirs in UI
trash_checkpoints()

# Launching the tunnel
launcher = 'main.py' if UI == 'ComfyUI' else 'launch.py'
password = 'vo9fdxgc0zkvghqwzrlz6rk2o00h5sc7'

# Setup pinggy timer
ipySys(f'echo -n {int(time.time())+(3600+20)} > {WEBUI}/static/timer-pinggy.txt')

with TunnelingService:
    CD(WEBUI)
    commandline_arguments += f' --port={tunnel_port}'
    
    # Default args append
    if UI != 'ComfyUI':
        commandline_arguments += ' --enable-insecure-extension-access --disable-console-progressbars --theme dark'
        # NSFW filter for Kaggle
        if ENV_NAME == "Kaggle":
            commandline_arguments += f' --encrypt-pass={password} --api'
    
    ## Launch
    try:
        if UI == 'ComfyUI':
            if check_custom_nodes_deps:
                ipySys(f'{py} install-deps.py')
            print("Installing dependencies for ComfyUI from requirements.txt...")
            subprocess.run(['pip', 'install', '-r', 'requirements.txt'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            clear_output(wait=True)

        print(f"🔧 WebUI: \033[34m{UI} \033[0m")
        ipySys(f'{py} {launcher} {commandline_arguments}')
    except KeyboardInterrupt:
        pass

# Print session duration
timer = float(open(f'{WEBUI}/static/timer.txt', 'r').read())
time_since_start = str(timedelta(seconds=time.time() - timer)).split('.')[0]
print(f"\n⌚️ You have been conducting this session for - \033[33m{time_since_start}\033[0m")
