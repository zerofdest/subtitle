#!/usr/bin/env python3
"""將 yt-dlp 的 *.live_chat.json (JSONL) 批次轉為聊天文本；有正文的 SC 標記金額。"""

import argparse
import json
import re
from pathlib import Path

DEFAULT_DIRECTORY = Path(r"H:\yt-dlp\output\NA")


def one_line(value: str) -> str:
    """保證一條聊天只占輸出文件的一行。"""
    return re.sub(r"[\r\n\u2028\u2029]+", " ", value).strip()


def get_message(renderer: dict) -> str:
    message = renderer.get("message", {})
    if not isinstance(message, dict):
        return ""

    runs = message.get("runs")
    if isinstance(runs, list):
        # 一條彈幕可能被拆成多個 runs；只取 text，不提取 emoji。
        parts = [run["text"] for run in runs
                 if isinstance(run, dict) and isinstance(run.get("text"), str)]
        if parts:
            return one_line("".join(parts))

    simple_text = message.get("simpleText", "")
    return one_line(simple_text) if isinstance(simple_text, str) else ""


def extract_chat_lines(record: dict):
    replay = record.get("replayChatItemAction", {})
    if not isinstance(replay, dict):
        return

    for action in replay.get("actions", []):
        if not isinstance(action, dict):
            continue
        add_action = action.get("addChatItemAction", {})
        if not isinstance(add_action, dict):
            continue
        item = add_action.get("item", {})
        if not isinstance(item, dict):
            continue

        # 普通聊天：使用者名稱：內容
        # 有文字的 Super Chat：使用者名稱【SC 金額】：內容
        # 無文字的 SC（以及純表情消息）不輸出。
        for renderer_type, renderer in item.items():
            if not isinstance(renderer, dict):
                continue
            author = renderer.get("authorName", {})
            if not isinstance(author, dict):
                continue
            name = author.get("simpleText", "")
            if not isinstance(name, str):
                continue
            name = one_line(name)
            message = get_message(renderer)
            if not name or not message:
                continue

            if renderer_type == "liveChatPaidMessageRenderer":
                amount_data = renderer.get("purchaseAmountText", {})
                amount = (amount_data.get("simpleText", "")
                          if isinstance(amount_data, dict) else "")
                amount = one_line(amount) if isinstance(amount, str) else ""
                label = f"【SC {amount}】" if amount else "【SC】"
                yield f"{name}{label}：{message}"
            else:
                yield f"{name}：{message}"


def convert_file(input_file: Path) -> tuple[int, int]:
    output_file = input_file.with_suffix(".txt")  # xxx.live_chat.json -> xxx.live_chat.txt
    saved = 0
    invalid = 0

    # 流式逐行解析，適用於較大的直播聊天文件。
    with input_file.open("r", encoding="utf-8-sig") as src, \
         output_file.open("w", encoding="utf-8", newline="\n") as dst:
        for lineno, line in enumerate(src, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                invalid += 1
                if invalid <= 3:
                    print(f"  [警告] 第 {lineno} 行 JSON 無效：{exc.msg}")
                continue
            if not isinstance(record, dict):
                continue
            for chat_line in extract_chat_lines(record):
                dst.write(chat_line + "\n")
                saved += 1

    print(f"[完成] {input_file.name} -> {output_file.name}（{saved} 條，損壞行 {invalid} 條）")
    return saved, invalid


def main():
    parser = argparse.ArgumentParser(description="批次提取 yt-dlp 直播聊天使用者名稱及文字")
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY,
                        help=f"待處理目錄，默認：{DEFAULT_DIRECTORY}")
    args = parser.parse_args()

    folder = args.directory
    if not folder.is_dir():
        parser.error(f"目錄不存在：{folder}")

    files = sorted(folder.glob("*.live_chat.json"))
    if not files:
        print(f"沒有找到 .live_chat.json 文件：{folder}")
        return

    total_messages = 0
    total_invalid = 0
    for file in files:
        try:
            count, invalid = convert_file(file)
        except OSError as exc:
            print(f"[失敗] {file.name}：{exc}")
            continue
        total_messages += count
        total_invalid += invalid
    print(f"處理結束：共 {len(files)} 個文件，輸出 {total_messages} 條消息，損壞行 {total_invalid} 條。")


if __name__ == "__main__":
    main()
