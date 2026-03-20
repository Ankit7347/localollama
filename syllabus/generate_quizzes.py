import argparse
import requests
import json
import time
import os
import glob

# Configuration
API_URL = "http://localhost:11434/api/generate"
MODEL = "gemma:2b"
DELAY = 1  # seconds between requests

def parse_llm_json(text):
    """Parses the LLM output into JSON. It only removes the outer ```json markers to prevent parse errors, keeping all inner markdown intact."""
    if not text:
        return []

    raw = text.strip()
    # Remove markdown code block markers if the model included them
    if raw.startswith("```json"):
        raw = raw[7:]
    elif raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    
    raw = raw.strip()
    
    try:
        data = json.loads(raw)
        return data
    except json.JSONDecodeError as e:
        print(f"[JSON ERROR] Failed to parse response: {e}")
        return []

def generate_quizzes(subject, chapter, topic, definition):
    prompt = f"""
You are an expert educational content creator. Based on the following definition of the topic '{topic}' in the chapter '{chapter}' for the subject '{subject}', generate exactly 5 quiz questions.
- 2 questions MUST have multiple correct answers (set type to "multiple_correct").
- 3 questions MUST have a single correct answer (set type to "single_correct").

Definition:
{definition}

Output the result STRICTLY as a valid JSON array of objects with the following structure. You are allowed to use Markdown formatting (like **bold** or *italics*) inside the question and option strings. Do not output any conversational text outside the JSON:
[
  {{
    "question": "Question text",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "answer": "Correct Option", // For single_correct this is a string. For multiple_correct this is a list of strings: ["Correct Option 1", "Correct Option 2"]
    "type": "single_correct" // or "multiple_correct"
  }}
]
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "temperature": 0.3, # lower temperature for rigid JSON structure output
        "top_p": 0.9,
    }

    response = requests.post(API_URL, json=payload, timeout=300)
    response.raise_for_status()
    result = response.json()
    quiz_text = result.get("response", "")
    return parse_llm_json(quiz_text)

def export_to_markdown(subjects, md_filename):
    """Renders the subjects and quizzes into a readable Markdown file."""
    with open(md_filename, "w", encoding="utf-8") as f:
        for subject in subjects:
            f.write(f"# {subject.get('subject', 'Unknown Subject')} (Year {subject.get('year', '')})\n\n")
            for chapter in subject.get("chapters", []):
                f.write(f"## {chapter.get('chapter', 'Unknown Chapter')}\n\n")
                for topic in chapter.get("topics", []):
                    f.write(f"### {topic.get('topic', 'Unknown Topic')}\n\n")
                    f.write(f"**Definition:**\n{topic.get('definition', '')}\n\n")
                    
                    quizzes = topic.get("quizzes", [])
                    if quizzes:
                        f.write("**Quizzes:**\n\n")
                        for i, quiz in enumerate(quizzes, 1):
                            f.write(f"**Q{i}: {quiz.get('question', '')}**\n\n")
                            answers = quiz.get("answer", [])
                            # Normalize single_correct string answers into a list for easy checking
                            if isinstance(answers, str):
                                answers = [answers]
                            for option in quiz.get("options", []):
                                mark = "x" if option in answers else " "
                                f.write(f"- [{mark}] {option}\n")
                            f.write("\n")
                    f.write("---\n\n")

def main():
    parser = argparse.ArgumentParser(description='Generate AI quizzes for topics.')
    parser.add_argument('--input-pattern', type=str, default='data/output/official_syllabus_*-topic.json', help='Input JSON files pattern')
    args = parser.parse_args()

    file_list = glob.glob(args.input_pattern)
    if not file_list:
        print(f"No files found matching '{args.input_pattern}'")
        return

    for filepath in file_list:
        print(f"\n--- Processing File: {filepath} ---")
        with open(filepath, "r", encoding="utf-8") as f:
            subjects = json.load(f)

        if not isinstance(subjects, list):
            subjects = [subjects]

        for subject in subjects:
            subject_name = subject.get("subject", "")
            for chapter in subject.get("chapters", []):
                chapter_name = chapter.get("chapter", "")
                for t in chapter.get("topics", []):
                    topic_name = t.get("topic", "")
                    definition = t.get("definition", "")
                    
                    # Skip if we already have quizzes generated
                    if "quizzes" in t and t["quizzes"]:
                        continue
                    
                    print(f"[GENERATING QUIZZES] {subject_name} > {chapter_name} > {topic_name}")
                    try:
                        quizzes = generate_quizzes(subject_name, chapter_name, topic_name, definition)
                        t["quizzes"] = quizzes
                    except Exception as e:
                        print(f"[ERROR] {topic_name}: {e}")
                        t["quizzes"] = []
                    
                    # Save incrementally back to the SAME file
                    with open(filepath, "w", encoding="utf-8") as out_f:
                        json.dump(subjects, out_f, ensure_ascii=False, indent=2)
                    
                    time.sleep(DELAY)

        print(f"Quizzes updated directly in {filepath}")
        
        # Automatically generate a markdown file next to the JSON file
        md_filepath = filepath.replace('.json', '.md')
        export_to_markdown(subjects, md_filepath)
        print(f"Markdown rendered to {md_filepath}")

if __name__ == "__main__":
    main()