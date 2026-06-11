import re
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox


CHOSEONG_LIST = [
    "ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ",
    "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ",
    "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ",
    "ㅋ", "ㅌ", "ㅍ", "ㅎ",
]

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MISSED_FILE = BASE_DIR / "missed_quiz.txt"
UNKNOWN_TOPIC_FILE = BASE_DIR / "unknown_topics.txt"


def get_choseong(text: str) -> str:
    result: list[str] = []

    for char in text:
        code = ord(char)

        if 0xAC00 <= code <= 0xD7A3:
            syllable_index = code - 0xAC00
            choseong_index = syllable_index // 588
            result.append(CHOSEONG_LIST[choseong_index])

    return "".join(result)


def safe_file_name(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


def read_words(file_path: Path) -> list[str]:
    if not file_path.exists():
        return []

    return [
        line.strip()
        for line in file_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_all_words_with_topic() -> list[tuple[str, str]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    result: list[tuple[str, str]] = []

    for file_path in DATA_DIR.glob("*.txt"):
        topic = file_path.stem
        words = read_words(file_path)

        for word in words:
            result.append((topic, word))

    return result


def save_unknown_topic(topic: str) -> None:
    existing = set()

    if UNKNOWN_TOPIC_FILE.exists():
        existing = {
            line.strip()
            for line in UNKNOWN_TOPIC_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

    if topic not in existing:
        with UNKNOWN_TOPIC_FILE.open("a", encoding="utf-8") as file:
            file.write(topic + "\n")


def save_missed_quiz(choseong: str, topic: str | None, reason: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    topic_text = topic if topic else "전체검색"

    with MISSED_FILE.open("a", encoding="utf-8") as file:
        file.write(f"{now} | 주제={topic_text} | 초성={choseong} | 사유={reason}\n")


def append_answer(topic: str, answer: str) -> tuple[bool, str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    topic_file = DATA_DIR / f"{safe_file_name(topic)}.txt"
    existing = set(read_words(topic_file))

    if answer in existing:
        return False, f"이미 등록됨: data/{topic}.txt -> {answer}"

    with topic_file.open("a", encoding="utf-8") as file:
        file.write(answer + "\n")

    return True, f"등록 완료: data/{topic}.txt -> {answer}"


def filter_candidates(
    candidates: list[tuple[str, str]],
    choseong: str,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    exact_matches: list[tuple[str, str]] = []
    partial_matches: list[tuple[str, str]] = []

    for found_topic, word in candidates:
        word_choseong = get_choseong(word)

        if word_choseong == choseong:
            exact_matches.append((found_topic, word))
        elif choseong in word_choseong:
            partial_matches.append((found_topic, word))

    return list(dict.fromkeys(exact_matches)), list(dict.fromkeys(partial_matches))


def find_answers(choseong: str, topic: str | None) -> tuple[list[tuple[str, str, str]], str]:
    if topic:
        topic_file = DATA_DIR / f"{safe_file_name(topic)}.txt"

        if topic_file.exists():
            topic_source_candidates = [(topic, word) for word in read_words(topic_file)]
            topic_exact, topic_partial = filter_candidates(topic_source_candidates, choseong)

            if topic_exact or topic_partial:
                return (
                    [(found_topic, word, "완전일치") for found_topic, word in topic_exact]
                    + [(found_topic, word, "포함일치") for found_topic, word in topic_partial],
                    "주제 DB에서 찾음",
                )

            all_exact, all_partial = filter_candidates(load_all_words_with_topic(), choseong)

            if all_exact or all_partial:
                return (
                    [(found_topic, word, "완전일치") for found_topic, word in all_exact]
                    + [(found_topic, word, "포함일치") for found_topic, word in all_partial],
                    "주제 DB에는 없고 전체 DB에서 찾음",
                )

            save_missed_quiz(choseong, topic, "주제 파일은 있으나 후보 없음")
            return [], "주제 파일은 있으나 후보 없음"

        save_unknown_topic(topic)
        all_exact, all_partial = filter_candidates(load_all_words_with_topic(), choseong)

        if all_exact or all_partial:
            return (
                [(found_topic, word, "완전일치") for found_topic, word in all_exact]
                + [(found_topic, word, "포함일치") for found_topic, word in all_partial],
                "처음 보는 주제라 전체 DB에서 찾음",
            )

        save_missed_quiz(choseong, topic, "처음 보는 주제이고 전체 DB에도 후보 없음")
        return [], "처음 보는 주제이고 전체 DB에도 후보 없음"

    all_exact, all_partial = filter_candidates(load_all_words_with_topic(), choseong)

    if all_exact or all_partial:
        return (
            [(found_topic, word, "완전일치") for found_topic, word in all_exact]
            + [(found_topic, word, "포함일치") for found_topic, word in all_partial],
            "전체 DB에서 찾음",
        )

    save_missed_quiz(choseong, None, "전체 DB에도 후보 없음")
    return [], "전체 DB에도 후보 없음"


def parse_input(text: str) -> tuple[str, str | None] | None:
    text = text.strip()

    if not text:
        return None

    parts = text.split(maxsplit=1)

    choseong = parts[0].strip()
    topic = parts[1].strip() if len(parts) == 2 else None

    if not all(char in CHOSEONG_LIST for char in choseong):
        return None

    return choseong, topic


class QuizHelperApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("초성 퀴즈 도우미")
        self.root.geometry("520x520")
        self.root.attributes("-topmost", True)

        self.results: list[tuple[str, str, str]] = []

        self.input_var = tk.StringVar()
        self.status_var = tk.StringVar(value="예: ㅍㄹㅌ 가전제품 또는 ㅍㄹㅌ")
        self.add_topic_var = tk.StringVar()
        self.add_answer_var = tk.StringVar()

        self.build_ui()
        self.bind_events()

    def build_ui(self) -> None:
        frame = tk.Frame(self.root, padx=12, pady=12)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="문제 입력").pack(anchor="w")
        self.input_entry = tk.Entry(frame, textvariable=self.input_var, font=("Malgun Gothic", 14))
        self.input_entry.pack(fill="x", pady=(4, 8))

        button_row = tk.Frame(frame)
        button_row.pack(fill="x", pady=(0, 8))

        tk.Button(button_row, text="검색", command=self.search).pack(side="left")
        tk.Button(button_row, text="지우기", command=self.clear_input).pack(side="left", padx=(6, 0))
        tk.Button(button_row, text="창 숨기기", command=self.hide_window).pack(side="right")

        tk.Label(frame, textvariable=self.status_var, anchor="w", justify="left").pack(fill="x", pady=(0, 8))

        tk.Label(frame, text="후보").pack(anchor="w")
        self.result_listbox = tk.Listbox(frame, height=12, font=("Malgun Gothic", 12))
        self.result_listbox.pack(fill="both", expand=True, pady=(4, 8))

        result_button_row = tk.Frame(frame)
        result_button_row.pack(fill="x", pady=(0, 12))
        tk.Button(result_button_row, text="선택 답 복사", command=self.copy_selected_answer).pack(side="left")

        add_frame = tk.LabelFrame(frame, text="정답 추가", padx=8, pady=8)
        add_frame.pack(fill="x")

        tk.Label(add_frame, text="주제").grid(row=0, column=0, sticky="w")
        self.add_topic_entry = tk.Entry(add_frame, textvariable=self.add_topic_var)
        self.add_topic_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        tk.Label(add_frame, text="정답").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.add_answer_entry = tk.Entry(add_frame, textvariable=self.add_answer_var)
        self.add_answer_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        add_frame.columnconfigure(1, weight=1)
        tk.Button(add_frame, text="추가", command=self.add_answer).grid(row=2, column=1, sticky="e", pady=(8, 0))

    def bind_events(self) -> None:
        self.input_entry.bind("<Return>", self.handle_input_enter)
        self.result_listbox.bind("<Double-Button-1>", lambda _event: self.copy_selected_answer())
        self.result_listbox.bind("<Return>", lambda _event: self.copy_selected_answer())
        self.add_answer_entry.bind("<Return>", lambda _event: self.add_answer())

    def handle_input_enter(self, _event: tk.Event) -> None:
        self.search()

        if self.results:
            self.result_listbox.selection_clear(0, tk.END)
            self.result_listbox.selection_set(0)
            self.result_listbox.activate(0)
            self.result_listbox.focus_set()

    def search(self) -> None:
        parsed = parse_input(self.input_var.get())

        if not parsed:
            self.results = []
            self.refresh_results()
            self.status_var.set("형식 오류. 예: ㅍㄹㅌ 또는 ㅍㄹㅌ 가전제품")
            return

        choseong, topic = parsed
        answers, status = find_answers(choseong, topic)
        self.results = answers
        self.refresh_results()

        if topic:
            self.add_topic_var.set(topic)

        if answers:
            self.status_var.set(f"{status} | 후보를 클릭하거나 Enter로 복사")
        else:
            self.status_var.set(f"{status} | 아래에서 직접 정답 추가 가능")
            self.add_answer_var.set("")
            self.add_answer_entry.focus_set()

    def refresh_results(self) -> None:
        self.result_listbox.delete(0, tk.END)

        for found_topic, answer, match_type in self.results:
            self.result_listbox.insert(
                tk.END,
                f"[{match_type}] [{found_topic}] {answer} ({get_choseong(answer)})",
            )

    def copy_selected_answer(self) -> None:
        if not self.results:
            return

        selection = self.result_listbox.curselection()
        index = selection[0] if selection else 0
        topic, answer, _match_type = self.results[index]

        self.root.clipboard_clear()
        self.root.clipboard_append(answer)
        self.root.update()

        self.add_topic_var.set(topic)
        self.add_answer_var.set(answer)
        self.status_var.set(f"복사됨: [{topic}] {answer}")

    def add_answer(self) -> None:
        topic = self.add_topic_var.get().strip()
        answer = self.add_answer_var.get().strip()

        if not topic or not answer:
            messagebox.showerror("입력 오류", "주제와 정답을 모두 입력하세요.")
            return

        _, message = append_answer(topic, answer)
        self.status_var.set(message)
        messagebox.showinfo("정답 추가", message)

    def clear_input(self) -> None:
        self.input_var.set("")
        self.status_var.set("예: ㅍㄹㅌ 가전제품 또는 ㅍㄹㅌ")
        self.results = []
        self.refresh_results()
        self.input_entry.focus_set()

    def hide_window(self) -> None:
        self.root.iconify()

    def run(self) -> None:
        self.input_entry.focus_set()
        self.root.mainloop()


def run_cli() -> None:
    print("초성 퀴즈 수동 도우미")
    print("입력 예시 1: ㅍㄹㅌ 가전제품")
    print("입력 예시 2: ㅍㄹㅌ")
    print("정답 추가: add 가전제품 프린터")
    print("GUI 실행: python main.py")
    print("종료: q")
    print()

    while True:
        text = input("> ").strip()

        if text.lower() in ["q", "quit", "exit"]:
            break

        if text.startswith("add "):
            parts = text.split(maxsplit=2)

            if len(parts) != 3:
                print("형식: add 주제 정답")
                continue

            _, topic, answer = parts
            _, message = append_answer(topic, answer)
            print(message)
            print()
            continue

        parsed = parse_input(text)

        if not parsed:
            print("형식 오류. 예: ㅍㄹㅌ 또는 ㅍㄹㅌ 가전제품")
            print()
            continue

        choseong, topic = parsed
        answers, status = find_answers(choseong, topic)

        print(f"상태: {status}")

        if answers:
            print("추천 답:")
            for index, (found_topic, answer, match_type) in enumerate(answers, start=1):
                print(f"{index}. [{match_type}] [{found_topic}] {answer} ({get_choseong(answer)})")
        else:
            print("추천 답 없음")
            if topic:
                print("정답을 알면 아래 형식으로 추가:")
                print(f"add {topic} 정답")
            else:
                print("주제를 알면 아래 형식으로 추가:")
                print("add 주제 정답")

        print()


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1].lower() == "cli":
        run_cli()
        return

    QuizHelperApp().run()


if __name__ == "__main__":
    main()
