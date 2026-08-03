import sqlite3
import json
from collections import defaultdict

def build_jopad_dictionary(db_path, json_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # We use defaultdict to easily build our structure without throwing KeyError
    lexicon = defaultdict(lambda: {"definition": [], "synonyms": set()})
    
    print("1. Extracting definitions from 'dictionary' table...")
    cursor.execute("SELECT word, definition FROM dictionary WHERE definition IS NOT NULL")
    for word, definition in cursor.fetchall():
        lexicon[word]["definition"].append(definition)

    print("2. Extracting synonyms from 'thesaurus' table...")
    cursor.execute("SELECT word, synonyms FROM thesaurus WHERE synonyms IS NOT NULL")
    for word, syn_str in cursor.fetchall():
        # The database stores synonyms as a comma-separated string, so we split them
        syns = [s.strip() for s in syn_str.split(',') if s.strip()]
        lexicon[word]["synonyms"].update(syns)

    print("3. Grouping rhymes from 'word_variants' table...")
    rhyme_groups = defaultdict(list)
    word_to_syllable = {}
    
    # We grab variant 0 (the most common pronunciation) and its last_syllable
    cursor.execute("SELECT word, last_syllable FROM word_variants WHERE last_syllable IS NOT NULL AND variant_number = 0")
    for word, last_syllable in cursor.fetchall():
        rhyme_groups[last_syllable].append(word)
        word_to_syllable[word] = last_syllable

    print("4. Assembling the final JSON structure...")
    final_json = {}
    
    for word, data in lexicon.items():
        # Some words have multiple definitions (e.g., as a noun and a verb). 
        # This joins them into a single string.
        combined_def = ". \n".join(data["definition"])
        
        # Convert the set of synonyms back to a standard list
        synonyms_list = list(data["synonyms"])
        
        # Find rhymes based on the shared last_syllable
        rhymes_list = []
        if word in word_to_syllable:
            syllable = word_to_syllable[word]
            # Grab words with the same syllable, making sure not to include the word itself
            all_rhymes = [r for r in rhyme_groups[syllable] if r != word]
            
            # Limiting to 5 rhymes to match your desired output and keep file size manageable
            rhymes_list = all_rhymes[:70] 

        # We only add the word to our JSON if it actually has a definition
        if combined_def:
            final_json[word] = {
                "definition": combined_def,
                "synonyms": synonyms_list,
                "rhymes": rhymes_list
            }

    print("5. Writing data to JSON file...")
    with open(json_path, 'w', encoding='utf-8') as f:
        # indent=2 formats it exactly like your example
        json.dump(final_json, f, indent=2, ensure_ascii=False)
        
    print(f"Done! Extracted {len(final_json)} words into {json_path}")
    conn.close()

if __name__ == "__main__":
    # Ensure your database is in the same directory, or provide the full path
    build_jopad_dictionary("poet_assistant.db", "jopad_dictionary_artiste.json")
