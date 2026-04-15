import json
import os
import requests
import time

# Configuration
TEMPLATE_FILE = "bestbook-template.json"
OUTPUT_FILE = "best-books-updated.json"
API_URL = "http://localhost:11434/api/generate"
MODEL = "gemma:2b"
DELAY = 1  # seconds between requests
ADDITIONAL_TAG = "NCERT"


def load_template(template_path):
    """Load the bestbook template JSON file."""
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_book_info(subject_name, sub_exam_name):
    """
    Use API to generate 2 book titles, authors, and descriptions for a subject.
    
    Replacements applied per book:
    1. Title - Generated from API
    2. Author - Generated from API
    3. Description - Generated from API
    """
    prompt = (
        f"Generate TWO different recommended books for the subject '{subject_name}' at '{sub_exam_name}' level. "
        f"Provide ONLY a JSON array with exactly two objects, each with these three fields (no markdown, no extra text): "
        f"[{{\"title\": \"book title 1\", \"author\": \"author name 1\", \"description\": \"one sentence description 1\"}}, "
        f"{{\"title\": \"book title 2\", \"author\": \"author name 2\", \"description\": \"one sentence description 2\"}}]. "
    )
    
    try:
        response = requests.post(
            API_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        # Extract and parse the response
        raw_response = result.get("response", "").strip()
        
        # Try to extract JSON from response
        if "[" in raw_response and "]" in raw_response:
            json_start = raw_response.find("[")
            json_end = raw_response.rfind("]") + 1
            json_str = raw_response[json_start:json_end]
            books_list = json.loads(json_str)
            
            # Ensure we have at least 2 books
            if isinstance(books_list, list) and len(books_list) >= 2:
                return [
                    {
                        "title": books_list[0].get("title", "Recommended Book 1"),
                        "author": books_list[0].get("author", "Author Name"),
                        "description": books_list[0].get("description", "Best reference material.")
                    },
                    {
                        "title": books_list[1].get("title", "Recommended Book 2"),
                        "author": books_list[1].get("author", "Author Name"),
                        "description": books_list[1].get("description", "Alternative reference material.")
                    }
                ]
        
        return None
    
    except Exception as e:
        print(f"  ⚠ API Error: {str(e)}")
        return None


def update_books_with_api(books_data, output_path):
    """
    Update all subjects in books data using API.
    Saves file after each subject is processed.
    Skips subjects already marked as done: true
    
    For each subject (2 books):
    - Replacement 1: Title (from API)
    - Replacement 2: Author (from API)
    - Replacement 3: Description (from API)
    - Append: Add tags (Exam, Class, Subject, NCERT) - at least 3 tags
    - Mark: Set "done": true
    """
    updated_data = books_data
    total_subjects = len(updated_data)
    replacements_count = 0
    append_count = 0
    skipped_count = 0
    
    for idx, entry in enumerate(updated_data, 1):
        subject_name = entry.get("subjectName", {}).get("en", "Unknown")
        sub_exam_name = entry.get("subExamName", {}).get("en", "Unknown")
        exam_name = entry.get("examName", {}).get("en", "Unknown")
        is_done = entry.get("done", False)
        
        # Skip if already processed
        if is_done:
            print(f"[{idx}/{total_subjects}] ⏭️  SKIPPED (already done): {subject_name}")
            skipped_count += 1
            continue
        
        print(f"\n[{idx}/{total_subjects}] Processing: {subject_name}")
        
        # Generate book info from API (2 books)
        print(f"  → Calling API for 2 book recommendations...")
        books_info = generate_book_info(subject_name, sub_exam_name)
        
        if books_info:
            # Create tags that match exam, class, and subject
            common_tags = [exam_name, sub_exam_name, subject_name, ADDITIONAL_TAG]
            
            # Clear existing books and add 2 new ones
            entry["books"] = []
            
            for book_idx, book_info in enumerate(books_info, 1):
                book = {
                    "title": book_info["title"],
                    "author": book_info["author"],
                    "description": book_info["description"],
                    "tags": common_tags.copy()
                }
                entry["books"].append(book)
                print(f"  ✓ [REPLACEMENT {(book_idx-1)*3 + 1}] Book {book_idx} Title: {book_info['title'][:50]}...")
                print(f"  ✓ [REPLACEMENT {(book_idx-1)*3 + 2}] Book {book_idx} Author: {book_info['author']}")
                print(f"  ✓ [REPLACEMENT {(book_idx-1)*3 + 3}] Book {book_idx} Description updated")
                replacements_count += 3
            
            # Add tags to both books
            for book_idx, book in enumerate(entry["books"], 1):
                if "tags" in book and isinstance(book["tags"], list):
                    print(f"  ✓ [APPEND] Book {book_idx} Tags: {', '.join(book['tags'])} (count: {len(book['tags'])})")
                    append_count += 1
        
        # Mark as done
        entry["done"] = True
        print(f"  ✓ [DONE] Marked as completed")
        
        # Save file after each subject is processed
        print(f"  💾 Saving file...")
        save_updated_books(updated_data, output_path)
        
        # Add delay between API calls
        if idx < total_subjects:
            time.sleep(DELAY)
    
    print(f"\n{'='*60}")
    print(f"✓ Total Subjects: {total_subjects}")
    print(f"✓ Skipped (already done): {skipped_count}")
    print(f"✓ Newly Processed: {total_subjects - skipped_count}")
    print(f"✓ Total Replacements Applied: {replacements_count}")
    print(f"✓ Total Appends Applied: {append_count}")
    print(f"{'='*60}\n")
    
    return updated_data


def save_updated_books(books_data, output_path):
    """Save updated books data to output JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(books_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Updated books saved to: {output_path}")


def main():
    """Main execution function."""
    try:
        print("=" * 60)
        print("BEST BOOKS TEMPLATE PROCESSOR - API EDITION")
        print("=" * 60)
        print(f"API URL: {API_URL}")
        print(f"Model: {MODEL}")
        print(f"Output: {OUTPUT_FILE}")
        print("=" * 60 + "\n")
        
        # Step 1: Load template or output file (resume support)
        print("[STEP 1] Loading template...")
        if os.path.exists(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 100:
            print(f"✓ Found existing output file: {OUTPUT_FILE} (resuming from checkpoint)")
            books_data = load_template(OUTPUT_FILE)
        else:
            books_data = load_template(TEMPLATE_FILE)
        print(f"✓ Loaded {len(books_data)} subject entries\n")
        
        # Step 2: Apply replacements and append using API
        print("[STEP 2] Processing subjects...")
        print("✓ Subjects marked as 'done': true will be skipped")
        print("✓ File will be saved after each subject is processed\n")
        updated_data = update_books_with_api(books_data, OUTPUT_FILE)
        
        print("\n" + "=" * 60)
        print("PROCESS COMPLETED SUCCESSFULLY!")
        print(f"Final output saved to: {OUTPUT_FILE}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
