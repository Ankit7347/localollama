import requests
import json
import time
import os
import re

# Configuration
API_URL = "http://localhost:11434/api/generate"
MODEL = "gemma:2b"
INPUT_FILE = "subjects.json"
OUTPUT_FILE = "ai_definitions.json"
DELAY = 1  # seconds between requests

# Load syllabus JSON
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    syllabus_data = json.load(f)

# Ensure we use a list of subjects
subjects = syllabus_data if isinstance(syllabus_data, list) else [syllabus_data]

# Normalize subject structure
for subject in subjects:
    for chapter in subject.get("chapters", []):
        normalized_topics = []
        for t in chapter.get("topics", []):
            if isinstance(t, str):
                normalized_topics.append({"topic": t})
            elif isinstance(t, dict):
                normalized_topics.append(t)
        chapter["topics"] = normalized_topics


def clean_response_text(text, topic=None):
    if not text:
        return ""

    raw = text.strip()
    out = re.sub(r"```(?:json)?", "", raw).strip()

    # Remove common leading prompt/chat fragments.
    out = re.sub(r"^\s*(sure[,\s]*)?(here(?:'s| is)?\s+the\s+definition\s+of\s+[^\.]+\.)", "", out, flags=re.IGNORECASE).strip()
    out = re.sub(r"^\s*Definition[:\-]?\s*", "", out, flags=re.IGNORECASE).strip()

    # Remove explicit subject/chapter metadata.
    out = re.sub(r"Subject\s*:\s*[^,;\.]+[;,\.]?", "", out, flags=re.IGNORECASE).strip()

    # If format is Chapter: X: definition, capture after second colon.
    m = re.search(r"Chapter\s*:\s*[^:]+:\s*(.*)$", out, flags=re.IGNORECASE)
    if m:
        out = m.group(1).strip()

    out = out.replace("\n", " ").replace("\r", " ")
    out = re.sub(r"\s+", " ", out).strip()

    # Remove repeated labels/phrases (e.g., "Subject: ... Chapter: ...")
    out = re.sub(r"(Subject\s*:\s*[^,;\.]+[;,\.]?)+", "", out, flags=re.IGNORECASE).strip()
    out = re.sub(r"(Chapter\s*:\s*[^:]+[;,\.]?)+", "", out, flags=re.IGNORECASE).strip()

    out = out.strip(' .')

    # Fallback if empty: pick sentence with topic or first sentence from raw text.
    if not out:
        sentences = re.split(r"(?<=[.!?])\s+", raw)
        found = ""
        if topic:
            for s in sentences:
                if topic.lower() in s.lower():
                    found = s.strip()
                    break
        if not found and sentences:
            found = sentences[0].strip()
        out = found

    out = re.sub(r"\s+", " ", out).strip()

    # Strip trailing period.
    if out.endswith('.'):
        out = out[:-1].strip()
    return out


def generate_definition(subject, chapter, topic, grade="6 to B.Tech"):
    prompt = (
        f"Provide a concise, formal definition of the topic '{topic}' for learners from class {grade}. "
        f"Subject: {subject}. Chapter: {chapter}. "
        "Write exactly one paragraph (1-2 sentences) in plain text."
        " Do not provide examples, bullet points, code, or any extras."
    )

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(API_URL, json=payload, timeout=300)
    response.raise_for_status()
    result = response.json()
    definition_text = result.get("response", "")
    return clean_response_text(definition_text, topic)


def save_output(data):
    temp_file = OUTPUT_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp_file, OUTPUT_FILE)


# Build output structure with definitions only
output = []

for subject in subjects:
    subj_out = {
        "subject": subject.get("subject", ""),
        "year": subject.get("year", ""),
        "chapters": []
    }

    for chapter in subject.get("chapters", []):
        chap_out = {
            "chapter": chapter.get("chapter", ""),
            "topics": []
        }

        for t in chapter.get("topics", []):
            topic_name = t.get("topic") if isinstance(t, dict) else None
            if not topic_name:
                continue

            print(f"[GENERATING] {subj_out['subject']} > {chap_out['chapter']} > {topic_name}")
            try:
                definition = generate_definition(subj_out["subject"], chap_out["chapter"], topic_name)
            except Exception as e:
                print(f"[ERROR] {topic_name}: {e}")
                definition = ""
            definition = clean_response_text(definition, topic_name)

            chap_out["topics"].append({
                "topic": topic_name,
                "definition": definition
            })

            time.sleep(DELAY)

        subj_out["chapters"].append(chap_out)
    output.append(subj_out)

save_output(output)
print(f"Definitions written to {OUTPUT_FILE}")
