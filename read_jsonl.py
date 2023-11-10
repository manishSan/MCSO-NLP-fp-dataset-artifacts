# file to read jsonl files
# these files are new line seperated JSON
# we'll load file into a list of dictionaries by splitting with new line 
# and then parse each line
import json
from difflib import SequenceMatcher
import re

def load_jsonl(filename):
    """
    load jsonl file into a list of dictionaries
    """
    data = []
    with open(filename) as f:
        for line in f:
            data.append(json.loads(line))
    return data

def parse_json(json_string: str):
    """
    parse json string into a dictionary
    """
    return json.loads(json_string)

# Function to normalize strings
def normalize_string(s):
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()

# Function to calculate sequence match score
def sequence_match_score(a, b):
    return SequenceMatcher(None, a, b).ratio()

def find_incorrect_predictions(data):
    """
    find incorrect predictions in the data
    """
    incorrect_predictions = []
    correct_pred_threshold = 0.95
    for record in data:
        gold_answers = record['answers']['text']
        pred_answer = normalize_string(record['predicted_answer'])

        # Dictionary to hold match scores
        match_scores = {}

        # Compare the normalized predicted answer to each gold answer
        for i, gold in enumerate(gold_answers):
            normalized_gold = normalize_string(gold)
            # Calculate sequence match score
            score = sequence_match_score(pred_answer, normalized_gold)
            match_scores[gold] = score
        
        # find if any of the gold answers have a match score above threshold
        if not any(score > correct_pred_threshold for score in match_scores.values()):
            # add this record to incorrect prediction
            record['pred_to_answer_match_score'] = match_scores
            incorrect_predictions.append(record)

    return incorrect_predictions




def iterate_jsonl(filename: str):
    jsonl = load_jsonl(filename)

    return find_incorrect_predictions(jsonl)

# define a main entry point
if __name__ == "__main__":
    # load the data
    folder = './../fp_model_runs/eval_output_qa_nov_4_7-10/'
    input_filename = 'eval_predictions.jsonl'
    pred_data = iterate_jsonl(folder + input_filename)
    # print the first 10 records
    # write this pred_data to a file named 'incorrect_prediction_analysis.jsonl' in the same folder
    out_filename = "incorrect_prediction_analysis.jsonl"
    with open(folder + out_filename, 'w') as f:
        for record in pred_data:
            f.write(json.dumps(record))
            f.write('\n')

    for i in range(10):
        print(pred_data[i])