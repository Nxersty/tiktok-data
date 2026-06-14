#!/usr/bin/env python3
import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


POSITIVE_WORDS = {
    "支持", "恢复", "好事", "理解", "辛苦", "及时", "希望", "理性", "说明了", "处理"
}
NEGATIVE_WORDS = {
    "离谱", "生气", "盲等", "太晚", "质疑", "追责", "曝光", "恐慌", "没有解释", "问责", "被困", "冷处理", "过去"
}

STANCE_KEYWORDS = {
    "support_response": {"理解", "处理", "恢复", "先别带节奏", "先等官方", "理性"},
    "criticize_response": {"太晚", "没有解释", "信息不透明", "追责", "交代", "为什么没人及时回应", "问责"},
    "call_for_amplification": {"转发", "曝光", "热搜", "监督", "继续关注"},
    "rumor_warning": {"辟谣", "误传", "夸大", "带节奏", "阴谋论", "等官方通报"}
}

PHASE_KEYWORDS = [
    ("现场曝光", {"滞留", "站台", "晚点", "现场", "聚集"}),
    ("官方说明", {"说明", "通报", "官方", "广播"}),
    ("恢复运行", {"恢复", "恢复运行", "逐步恢复"}),
    ("追责反思", {"追责", "问责", "交代", "改进", "监督"})
]

AMPLIFICATION_HINTS = {"转发", "曝光", "热搜", "监督", "扩散", "继续关注"}


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze structured public Douyin research samples.")
    parser.add_argument("--input", required=True, help="Path to input JSON dataset.")
    parser.add_argument("--markdown", required=True, help="Path to output Markdown report.")
    parser.add_argument("--json", required=True, help="Path to output JSON summary.")
    return parser.parse_args()


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text):
    text = text.strip()
    text = re.sub(r"\s+", "", text)
    return text


def sentiment_score(text):
    score = 0
    normalized = normalize_text(text)
    contrast = any(token in normalized for token in {"但是", "但", "不过", "可是"})
    for word in POSITIVE_WORDS:
        if word in normalized:
            score += 1
    for word in NEGATIVE_WORDS:
        if word in normalized:
            score -= 1
    if contrast and score > 0:
        score -= 1
    if any(token in normalized for token in {"追责", "问责", "曝光", "交代"}) and score >= 0:
        score -= 1
    if score > 0:
        return "positive"
    if score < 0:
        return "negative"
    return "neutral"


def detect_stances(text):
    normalized = normalize_text(text)
    labels = []
    for label, keywords in STANCE_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            labels.append(label)
    if not labels:
        labels.append("other")
    return labels


def detect_phase(video):
    joined = normalize_text(f"{video.get('title', '')}{video.get('summary', '')}")
    hits = []
    for phase, keywords in PHASE_KEYWORDS:
        if any(keyword in joined for keyword in keywords):
            hits.append(phase)
    return hits or ["一般讨论"]


def parse_dt(value):
    return datetime.fromisoformat(value)


def top_comment(video):
    comments = video.get("comments", [])
    if not comments:
        return None
    return max(comments, key=lambda item: item.get("like_count", 0))


def analyze(dataset):
    stats = {
        "video_count": 0,
        "comment_count": 0,
        "reply_count": 0
    }
    sentiment_counter = Counter()
    stance_counter = Counter()
    phase_counter = Counter()
    video_summaries = []
    active_users = defaultdict(lambda: {
        "comment_count": 0,
        "reply_count": 0,
        "videos": set(),
        "amplification_hits": 0,
        "sample_texts": []
    })
    timeline_entries = []

    for video in dataset.get("videos", []):
        stats["video_count"] += 1
        phases = detect_phase(video)
        for phase in phases:
            phase_counter[phase] += 1

        video_sentiments = Counter()
        video_stances = Counter()
        top = top_comment(video)

        timeline_entries.append({
            "time": video["publish_time"],
            "type": "video",
            "video_id": video["video_id"],
            "title": video["title"],
            "phase_tags": phases
        })

        for comment in video.get("comments", []):
            stats["comment_count"] += 1
            text = comment.get("text", "")
            senti = sentiment_score(text)
            sentiment_counter[senti] += 1
            video_sentiments[senti] += 1

            stances = detect_stances(text)
            for stance in stances:
                stance_counter[stance] += 1
                video_stances[stance] += 1

            user_state = active_users[comment["user_id"]]
            user_state["comment_count"] += 1
            user_state["videos"].add(video["video_id"])
            user_state["sample_texts"].append(text)
            if any(token in normalize_text(text) for token in AMPLIFICATION_HINTS):
                user_state["amplification_hits"] += 1

            timeline_entries.append({
                "time": comment["publish_time"],
                "type": "comment",
                "video_id": video["video_id"],
                "user_id": comment["user_id"],
                "text": text,
                "sentiment": senti,
                "stances": stances
            })

            for reply in comment.get("replies", []):
                stats["reply_count"] += 1
                reply_text = reply.get("text", "")
                senti = sentiment_score(reply_text)
                sentiment_counter[senti] += 1
                video_sentiments[senti] += 1

                reply_stances = detect_stances(reply_text)
                for stance in reply_stances:
                    stance_counter[stance] += 1
                    video_stances[stance] += 1

                reply_state = active_users[reply["user_id"]]
                reply_state["reply_count"] += 1
                reply_state["videos"].add(video["video_id"])
                reply_state["sample_texts"].append(reply_text)
                if any(token in normalize_text(reply_text) for token in AMPLIFICATION_HINTS):
                    reply_state["amplification_hits"] += 1

                timeline_entries.append({
                    "time": reply["publish_time"],
                    "type": "reply",
                    "video_id": video["video_id"],
                    "user_id": reply["user_id"],
                    "text": reply_text,
                    "sentiment": senti,
                    "stances": reply_stances
                })

        video_summaries.append({
            "video_id": video["video_id"],
            "title": video["title"],
            "publish_time": video["publish_time"],
            "phase_tags": phases,
            "top_comment": top["text"] if top else None,
            "top_comment_likes": top["like_count"] if top else 0,
            "sentiment_breakdown": dict(video_sentiments),
            "stance_breakdown": dict(video_stances)
        })

    timeline_entries.sort(key=lambda item: parse_dt(item["time"]))
    high_activity = []
    for user_id, state in active_users.items():
        score = len(state["videos"]) * 2 + state["comment_count"] + state["reply_count"] + state["amplification_hits"] * 2
        if len(state["videos"]) >= 2 or state["amplification_hits"] >= 1:
            high_activity.append({
                "user_id": user_id,
                "activity_score": score,
                "comment_count": state["comment_count"],
                "reply_count": state["reply_count"],
                "video_count": len(state["videos"]),
                "amplification_hits": state["amplification_hits"],
                "sample_texts": state["sample_texts"][:3]
            })
    high_activity.sort(key=lambda item: item["activity_score"], reverse=True)

    dominant_sentiment = sentiment_counter.most_common(1)[0][0] if sentiment_counter else "neutral"
    dominant_stances = stance_counter.most_common(4)

    return {
        "dataset_name": dataset.get("dataset_name"),
        "topic_id": dataset.get("topic_id"),
        "topic_name": dataset.get("topic_name"),
        "stats": stats,
        "dominant_sentiment": dominant_sentiment,
        "sentiment_breakdown": dict(sentiment_counter),
        "stance_breakdown": dict(stance_counter),
        "phase_breakdown": dict(phase_counter),
        "dominant_stances": dominant_stances,
        "video_summaries": video_summaries,
        "high_activity_users": high_activity[:10],
        "timeline_entries": timeline_entries[:20]
    }


def percent(part, total):
    if total == 0:
        return "0.0%"
    return f"{(part / total) * 100:.1f}%"


def build_markdown(summary):
    total_texts = summary["stats"]["comment_count"] + summary["stats"]["reply_count"]
    negative = summary["sentiment_breakdown"].get("negative", 0)
    positive = summary["sentiment_breakdown"].get("positive", 0)
    neutral = summary["sentiment_breakdown"].get("neutral", 0)

    lines = []
    lines.append(f"# {summary['topic_name']} 分析报告")
    lines.append("")
    lines.append("## 一、样本概况")
    lines.append("")
    lines.append(f"- 数据集：`{summary['dataset_name']}`")
    lines.append(f"- 视频数：{summary['stats']['video_count']}")
    lines.append(f"- 评论数：{summary['stats']['comment_count']}")
    lines.append(f"- 回复数：{summary['stats']['reply_count']}")
    lines.append("")
    lines.append("## 二、核心结论")
    lines.append("")
    lines.append(f"1. 样本整体以`{summary['dominant_sentiment']}`情绪为主，其中负向占比 {percent(negative, total_texts)}，正向占比 {percent(positive, total_texts)}，中性占比 {percent(neutral, total_texts)}。")
    if summary["dominant_stances"]:
        top_stance_labels = "、".join([f"{label}({count})" for label, count in summary["dominant_stances"]])
        lines.append(f"2. 讨论最集中的立场包括：{top_stance_labels}。")
    lines.append(f"3. 事件阶段标签显示，讨论已覆盖：{'、'.join(summary['phase_breakdown'].keys())}。")
    if summary["high_activity_users"]:
        top_user = summary["high_activity_users"][0]
        lines.append(f"4. 用户 `{top_user['user_id']}` 表现出最强高活跃线索，跨 {top_user['video_count']} 个视频发声，放大相关命中 {top_user['amplification_hits']} 次。")
    lines.append("")
    lines.append("## 三、事件脉络")
    lines.append("")
    for item in summary["timeline_entries"][:8]:
        if item["type"] == "video":
            lines.append(f"- {item['time']}：视频 `{item['video_id']}` 发布，主题为《{item['title']}》，阶段标签：{'、'.join(item['phase_tags'])}。")
        else:
            stance_text = "、".join(item.get("stances", []))
            lines.append(f"- {item['time']}：{item['type']} 出现，情绪 `{item['sentiment']}`，立场 `{stance_text}`，内容：{item['text']}")
    lines.append("")
    lines.append("## 四、视频级观察")
    lines.append("")
    for video in summary["video_summaries"]:
        lines.append(f"- `{video['video_id']}`《{video['title']}》：阶段 `{'、'.join(video['phase_tags'])}`；最高赞评论 {video['top_comment_likes']} 赞；情绪分布 {video['sentiment_breakdown']}；立场分布 {video['stance_breakdown']}。")
    lines.append("")
    lines.append("## 五、高活跃传播线索")
    lines.append("")
    if summary["high_activity_users"]:
        for user in summary["high_activity_users"][:5]:
            sample = " | ".join(user["sample_texts"][:2])
            lines.append(f"- 用户 `{user['user_id']}`：活跃分 {user['activity_score']}，跨视频数 {user['video_count']}，放大命中 {user['amplification_hits']}，示例：{sample}")
    else:
        lines.append("- 当前样本中未识别出明显高活跃传播线索。")
    lines.append("")
    lines.append("## 六、应用价值")
    lines.append("")
    lines.append("1. 可用于判断事件是否从现场信息传播转向问责型舆情。")
    lines.append("2. 可用于观察负面情绪是否在短时间内集中累积。")
    lines.append("3. 可用于识别需要重点复核的高活跃传播账号线索。")
    lines.append("")
    lines.append("## 七、当前局限")
    lines.append("")
    lines.append("1. 当前为规则法基线，情感和立场识别仍需更多真实样本校准。")
    lines.append("2. 当前样例数据为脱敏合成样本，主要用于演示链路，不直接代表真实全网结论。")
    return "\n".join(lines) + "\n"


def write_outputs(markdown_path, json_path, summary):
    markdown = build_markdown(summary)
    Path(markdown_path).write_text(markdown, encoding="utf-8")
    Path(json_path).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    args = parse_args()
    dataset = load_dataset(args.input)
    summary = analyze(dataset)
    write_outputs(args.markdown, args.json, summary)


if __name__ == "__main__":
    main()
