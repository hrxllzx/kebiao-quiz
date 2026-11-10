# -*- coding: utf-8 -*-
"""解析 docx -> 题库 JSON（题目模板分段 + 答案填充）"""
import json
import re
import sys
import docx

DOCX = r"D:\hrx\lzx\1110课标练习1（课程性质和课程理念）-题目及答案.docx"


def load_lines(path):
    d = docx.Document(path)
    out = []
    for p in d.paragraphs:
        t = p.text.replace("\u00a0", " ").strip(" \t")
        if t:
            out.append(t)
    return out


def split_blanks(q):
    """按连续全角/半角空白切分为 segs，len(segs) = 空格数 + 1"""
    segs = re.split(r"[\u3000 ]{2,}", q)
    return [s.strip() for s in segs]


def fill_from_answer(segs, ans):
    """贪心对齐：segs 之间的空档即为答案"""
    fills = []
    pos = 0
    n = len(segs) - 1
    for i in range(n):
        p = segs[i]
        if p:
            idx = ans.find(p, pos)
            if idx < 0:
                return None
            pos = idx + len(p)
        nxt = segs[i + 1]
        if nxt:
            j = ans.find(nxt, pos) if nxt else -1
            if j < 0:
                return None
            fills.append(ans[pos:j].strip())
            pos = j
        else:
            fills.append(ans[pos:].strip())
            pos = len(ans)
    return fills


def parse_lines(lines):
    sets = []
    cur = None
    mode = None
    qs, ans = [], []
    num_re = re.compile(r"^(\d+)[\.．、][ \t]*(.*)$")
    head_re = re.compile(r"^练习\s*(\d+)\s*[（(]?\s*(.*?)\s*[)）]?$")

    def flush():
        if cur is None:
            return
        for i, q in enumerate(qs):
            if i >= len(ans):
                break
            cur["items"].append({"no": i + 1, "q": q, "a": ans[i]})

    for ln in lines:
        if ln.startswith("数学课标练习") or ln.startswith("（填空题"):
            continue
        m = head_re.match(ln)
        if m and ("练习" in ln) and len(ln) < 40:
            flush()
            title = ln
            cur = {"title": title, "no": m.group(1), "items": []}
            sets.append(cur)
            qs, ans, mode = [], [], None
            continue
        if ln in ("题目", "参考答案"):
            flush()
            qs, ans = ([], []) if ln == "题目" else (qs, [])
            mode = "q" if ln == "题目" else "a"
            continue
        m = num_re.match(ln)
        if m and cur is not None:
            (qs if mode == "q" else ans).append(m.group(2).strip(" \t"))
    flush()
    return sets


def main():
    lines = load_lines(DOCX)
    sets = parse_lines(lines)
    total_q = 0
    bad = []
    for s in sets:
        for it in s["items"]:
            segs = split_blanks(it["q"])
            nblank = len(segs) - 1
            if nblank == 0:
                bad.append((s["no"], it["no"], "no-blank"))
                it["segs"] = [it["q"]]
                it["fills"] = []
                continue
            fills = fill_from_answer(segs, it["a"])
            if fills is None or len(fills) != nblank or any(not f for f in fills):
                bad.append((s["no"], it["no"], "align-fail", it["q"], it["a"]))
                it["segs"] = segs
                it["fills"] = [""] * nblank
            else:
                it["segs"] = segs
                it["fills"] = fills
            total_q += 1
            it["nblank"] = nblank

    # 自检：把 fills 填回 segs，必须与原答案一致（忽略句末标点差异）
    def norm(x):
        return re.sub(r"[\s，。、；：\"'“”‘’（）()《》]", "", x)

    mism = []
    for s in sets:
        for it in s["items"]:
            if not it.get("fills"):
                continue
            rebuilt = it["segs"][0] + "".join(
                f + it["segs"][i + 1] for i, f in enumerate(it["fills"])
            )
            if norm(rebuilt) != norm(it["a"]):
                mism.append((s["no"], it["no"], rebuilt, it["a"]))

    data = {"source": "义务教育数学课程标准（2022年版）", "sets": sets}
    with open("quiz_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"练习组: {len(sets)}  题目: {total_q}")
    for s in sets:
        print(f"  {s['title']}  ->  {len(s['items'])} 题")
    print("\n对齐失败:", len(bad))
    for b in bad:
        print("  ", b)
    print("重建不一致:", len(mism))
    for m in mism:
        print("  ", m)


if __name__ == "__main__":
    main()
