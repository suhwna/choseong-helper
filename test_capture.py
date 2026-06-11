import ctypes
import json
from pathlib import Path

import mss
from PIL import Image


try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "region.json"
OUTPUT_FILE = BASE_DIR / "capture_test.png"


def main() -> None:
    if not CONFIG_FILE.exists():
        print(f"region.json 파일이 없습니다: {CONFIG_FILE}")
        print("먼저 python select_region.py 를 실행하세요.")
        return

    raw_text = CONFIG_FILE.read_text(encoding="utf-8").strip()

    if not raw_text:
        print("region.json 파일이 비어있습니다.")
        print("region.json 삭제 후 python select_region.py 를 다시 실행하세요.")
        return

    region_json = json.loads(raw_text)

    monitor = {
        "left": int(region_json["left"]),
        "top": int(region_json["top"]),
        "width": int(region_json["width"]),
        "height": int(region_json["height"]),
    }

    print("읽은 region.json:")
    print(monitor)

    with mss.MSS() as screen_capture:
        print()
        print("MSS 모니터 목록:")
        for index, item in enumerate(screen_capture.monitors):
            print(index, item)

        screenshot = screen_capture.grab(monitor)
        image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        image.save(OUTPUT_FILE)

    print()
    print(f"저장 완료: {OUTPUT_FILE}")
    print("이미지를 열어서 카톡 대화창 영역이 제대로 찍혔는지 확인하세요.")


if __name__ == "__main__":
    main()