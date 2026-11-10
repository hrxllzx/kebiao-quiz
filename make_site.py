# -*- coding: utf-8 -*-
"""把 quiz_data.json 注入 index_template.html -> index.html（单文件、离线可用）"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    data = json.load(open(os.path.join(HERE, "quiz_data.json"), encoding="utf-8"))
    tpl = open(os.path.join(HERE, "index_template.html"), encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")  # 防止提前闭合 script
    assert "__DATA_JSON__" in tpl
    out = tpl.replace("__DATA_JSON__", payload)
    path = os.path.join(HERE, "index.html")
    open(path, "w", encoding="utf-8", newline="\n").write(out)
    n = sum(len(s["items"]) for s in data["sets"])
    print(f"index.html 已生成: {len(out)} 字节, {n} 题, {len(data['sets'])} 组")


if __name__ == "__main__":
    main()
