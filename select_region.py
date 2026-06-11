import ctypes
import json
import time
from pathlib import Path

import pyautogui


try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "region.json"


def main() -> None:
    print("카톡 대화창 캡처 영역 설정")
    print()
    print("문제 말풍선 하나만 잡지 말고,")
    print("카톡 채팅 내용이 보이는 중간 영역 전체를 잡으세요.")
    print("상단 방 제목, 하단 입력창은 제외하는 게 좋습니다.")
    print()

    print("1) 마우스를 캡처할 영역의 '왼쪽 위'에 올려놓고 Enter")
    input("준비되면 Enter...")
    left_top = pyautogui.position()
    print(f"왼쪽 위 좌표: x={left_top.x}, y={left_top.y}")

    time.sleep(0.5)

    print()
    print("2) 마우스를 캡처할 영역의 '오른쪽 아래'에 올려놓고 Enter")
    input("준비되면 Enter...")
    right_bottom = pyautogui.position()
    print(f"오른쪽 아래 좌표: x={right_bottom.x}, y={right_bottom.y}")

    left = min(left_top.x, right_bottom.x)
    top = min(left_top.y, right_bottom.y)
    width = abs(right_bottom.x - left_top.x)
    height = abs(right_bottom.y - left_top.y)

    if width <= 0 or height <= 0:
        print("영역 설정 실패. 오른쪽 아래 좌표가 왼쪽 위보다 커야 합니다.")
        return

    region = {
        "left": left,
        "top": top,
        "width": width,
        "height": height,
    }

    CONFIG_FILE.write_text(
        json.dumps(region, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"영역 저장 완료: {CONFIG_FILE}")
    print(region)


if __name__ == "__main__":
    main()