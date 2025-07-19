import requests
from pathlib import Path

BASE_URL = "https://raw.communitydragon.org/latest/"
FILE_LIST_URL = BASE_URL + "cdragon/files.exported.txt"
DOWNLOAD_ROOT = Path("images")

def matches_target(line):
    return (line.startswith("game/assets/characters/tft13")) or (line.startswith("game/assets/maps/tft/icons/"))

def download_file(relative_path):
    url = BASE_URL + relative_path
    local_path = DOWNLOAD_ROOT / relative_path
    local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded: {relative_path}")
        else:
            print(f"Failed ({response.status_code}): {relative_path}")
    except Exception as e:
        print(f"Error downloading {relative_path}: {e}")

def main():
    print("Fetching file list")
    response = requests.get(FILE_LIST_URL)
    if response.status_code != 200:
        print("Failed to fetch files.exported.txt")
        return

    lines = response.text.splitlines()
    targets = [line for line in lines if matches_target(line)]

    for path in targets:
        download_file(path)

    print("\nAll downloads completed.")

if __name__ == "__main__":
    main()
