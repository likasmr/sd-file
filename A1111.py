# ~ A1111.py | by ANXETY ~

from json_utils import read_json, update_json   # JSON (main)

from IPython.display import clear_output
from IPython.utils import capture
from pathlib import Path
import subprocess
import asyncio
import os

# Constants
UI = 'A1111'

HOME = Path.home()
WEBUI = HOME / UI
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

REPO_URL = "你的新下载地址"
BRANCH = read_json(SETTINGS_PATH, 'ENVIRONMENT.branch')
EXTS = read_json(SETTINGS_PATH, 'WEBUI.extension_dir')

os.chdir(HOME)

# ==================== WEB UI OPERATIONS ====================

async def _download_file(url, directory, filename):
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    process = await asyncio.create_subprocess_shell(
        f'curl -sLo {file_path} {url}',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    await process.communicate()

async def download_files(file_list):
    tasks = []
    for file_info in file_list:
        parts = file_info.split(',')
        url = parts[0].strip()
        directory = parts[1].strip() if len(parts) > 1 else WEBUI   # Default Save Path
        filename = parts[2].strip() if len(parts) > 2 else os.path.basename(url)
        tasks.append(_download_file(url, directory, filename))
    await asyncio.gather(*tasks)

async def download_configuration():
    ## FILES
    url_af = f'https://raw.githubusercontent.com/anxety-solo/sdAIgen/refs/heads/{BRANCH}/__configs__/'
    configs = [
        f'{url_af}/{UI}/config.json',
        f'{url_af}/{UI}/ui-config.json',
        f'{url_af}/styles.csv',
        f'{url_af}/user.css',
    ]
    await download_files(configs)

    ## REPOS
    extensions_list = [
        ## ANXETY Edits
        "https://github.com/anxety-solo/webui_timer timer",
        "https://github.com/anxety-solo/anxety-theme",
        
        ## OTHER | ON
        "https://github.com/gutris1/sd-image-info Image-Info",
        "https://github.com/gutris1/sd-encrypt-image Encrypt-Image",

        ## OTHER | OFF
        # "https://github.com/Bing-su/adetailer Adetailer",
        # "https://github.com/thomasasfk/sd-webui-aspect-ratio-helper Aspect-Ratio-Helper",
        # "https://github.com/richrobber2/canvas-zoom Canvas-Zoom",
        # "https://github.com/anxety-solo/sd-civitai-browser-plus Civitai-Browser-Plus",
        # "https://github.com/Zyin055/Config-Presets",
        # "https://github.com/Mikubill/sd-webui-controlnet ControlNet",
        # "https://github.com/zanllp/sd-webui-infinite-image-browsing Infinite-Image-Browsing",
        # "https://github.com/hako-mikan/sd-webui-regional-prompter Regional-Prompter",
        # "https://github.com/gutris1/sd-image-info Image-Info",
        # "https://github.com/gutris1/sd-hub SD-Hub",
        # "https://github.com/ilian6806/stable-diffusion-webui-state State",
        # "https://github.com/hako-mikan/sd-webui-supermerger Supermerger",
        # "https://github.com/DominikDoom/a1111-sd-webui-tagcomplete TagComplete",
        # "https://github.com/Tsukreya/Umi-AI-Wildcards",
        # "https://github.com/picobyte/stable-diffusion-webui-wd14-tagger wd14-tagger"
    ]
    os.makedirs(EXTS, exist_ok=True)
    os.chdir(EXTS)

    tasks = []
    for command in extensions_list:
        tasks.append(asyncio.create_subprocess_shell(
            f'git clone --depth 1 --recursive {command}',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ))
    
    await asyncio.gather(*tasks)

def unpack_webui():
    zip_path = f"{SCR_PATH}/{UI}.zip"
    get_ipython().system(f'aria2c --console-log-level=error -c -x 16 -s 16 -k 1M {REPO_URL} -d {SCR_PATH} -o {UI}.zip')
    get_ipython().system(f'unzip -q -o {zip_path} -d {WEBUI}')
    get_ipython().system(f'rm -rf {zip_path}')

# ==================== MAIN CODE ====================

if __name__ == "__main__":
    with capture.capture_output():
        unpack_webui()
        asyncio.run(download_configuration())
