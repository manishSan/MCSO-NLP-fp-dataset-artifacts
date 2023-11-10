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

def reformat_json(original_file_path, out_file_path):
    reformatted = convert_json(original_file_path)
    
    with open(out_file_path, 'w') as file:
        json.dump(reformatted, file)


# define the main entry point of the script
if __name__ == "__main__":
    # Prompt for a question
    orig_file_path = './Squad/dev-v1.1-adversarial.json'
    out_file_path = './Squad/dev-v1.1-adversarial-reformatted.json'
    reformat_json(original_file_path=orig_file_path, 
                               out_file_path=out_file_path)