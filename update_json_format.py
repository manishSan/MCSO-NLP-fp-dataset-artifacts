# This file load the Squad/dev-v1.1-advertised.json file and convert it to the format used by the model
# The format is:
# [{id: string, 
#  title: string,
#  context: string,
#  question: string,
#  answers: 
#      text: [ string, string, string ]
# }]

import json
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

def convert_json(original_file_path):
    with open(original_file_path, 'r') as file:
        squad_data = json.load(file)

    test_set = []
    for article in squad_data['data']:
        t_set = {}
        for paragraph in article['paragraphs']:
            for qa in paragraph['qas']:
                t_set = {}
                t_set['id'] = qa['id']
                t_set['title'] = article['title']
                t_set['context'] = paragraph['context']
                t_set['question'] = qa['question']
                text = []
                ans_start = []
                for ans in qa['answers']:
                    text.append(ans['text'])
                    ans_start.append(ans['answer_start'])
                    
                t_set['answers'] = {
                    'text': text,
                    'answer_start': ans_start
                }
                test_set.append(t_set)

    return test_set

def extract_all_paragraphs(squad_data):
    paragraphs = []
    for article in squad_data['data']:
        para = article['paragraphs']
        paragraphs.extend(para)
    return paragraphs

def reformat_json(original_file_path, out_file_path):
    reformatted = convert_json(original_file_path)
    
    with open(out_file_path, 'w') as file:
        json.dump(reformatted, file)

def process_ad_context(ad_context, paragraphs):
    ad_context_str  = ad_context[1]
    paragraph = find_min_cosine_distance(ad_context_str, paragraphs)
    result_set = []
    for qa in paragraph['qas']:
        t_set = {}

        t_set['id'] = qa['id']
        t_set['context'] = ad_context_str
        t_set['question'] = qa['question']
        text = []
        ans_start = []
        for ans in qa['answers']:
            text.append(ans['text'])
            ans_start.append(ans['answer_start'])
            
        t_set['answers'] = {
            'text': text,
            'answer_start': ans_start
        }
        result_set.append(t_set)
    return result_set

def reformat_json_train(original_file_path, adversarial_file_path, out_file_path):
    with open(original_file_path, 'r') as file:
        squad_data = json.load(file)

    with open(adversarial_file_path, 'r') as file:
        adversarial_contexts = json.load(file)

    paragraphs = extract_all_paragraphs(squad_data)

    test_set = []
    # The paragraph should be sequential, so the order of following loops 
    # should just be O(n)
    with ProcessPoolExecutor() as executor:
        test_set = list(tqdm(executor.map(process_ad_context, adversarial_contexts, paragraphs), total=len(adversarial_contexts)))

    # for ad_context in tqdm(adversarial_contexts):
    #     with ProcessPoolExecutor() as executor:
                        
    with open(out_file_path, 'w') as file:
        json.dump(test_set, file)
    return


def find_min_distance(context, list_of_paragraphs):
    distances = []

    for paragraph in list_of_paragraphs:
        inner_context = paragraph['context']
        distances.append(levenshtein_distance(context, inner_context))

    index = np.argmin(distances)

    return list_of_paragraphs[index]

def cosine_distance(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return 1 - (dot_product / (norm_vec1 * norm_vec2))

def find_min_cosine_distance(context, list_of_paragraphs):
    distances = []

    for paragraph in list_of_paragraphs:
        inner_context = paragraph['context']
        vectorizer = CountVectorizer().fit_transform([context, inner_context])
        vectors = vectorizer.toarray()
        dist = cosine_distance(vectors[0], vectors[1])
        distances.append(dist)

    index = np.argmin(distances)

    return list_of_paragraphs[index]

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]
# define the main entry point of the script
if __name__ == "__main__":
    # Prompt for a question
    # orig_file_path = './Squad/dev-v1.1.json'
    # out_file_path = './Squad/dev-v1.1-reformatted.json'
    # reformat_json(original_file_path=orig_file_path, out_file_path=out_file_path)

    orig_file_path = './Squad/train-v1.1.json'
    adv_file_path = './Squad/train-v1.1-adversarial-50-diff.json'
    out_file_path = '.Squad/train-v1.1-adversarial-50-diff-reformatted.json'
    reformat_json_train(original_file_path=orig_file_path, 
                        adversarial_file_path=adv_file_path, 
                        out_file_path=out_file_path)