import json
import random
from openai import OpenAI
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
from tqdm import tqdm

def modify_sentence(sentence):
    # TODO: Implement sentence modification logic here
    # This could involve calling an external NLP service, like an AI model, to paraphrase sentences.
    return sentence

def introduce_noise(sentence_list):
    # TODO: Implement logic to introduce noise sentences here
    return sentence_list

import requests

# GPT_MODEL = "gpt-4-1106-preview"
GPT_MODEL = "gpt-3.5-turbo-16k-0613"
seed = 42
API_KEY = "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"
client = OpenAI(api_key=API_KEY)
def call_chatgpt(prompt, context, max_tokens=1000):
    """
    Makes an API call to a ChatGPT-like model.

    :param prompt: The input text prompt to send to the model.
    :param max_tokens: The maximum number of tokens to generate in the response.
    :return: The model's response as a string.
    """
    messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": context},
        ]
    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages,
        seed=seed,
        max_tokens=max_tokens,
        temperature=0.9,
        # response_json=True,
        # response_format='{ "type": "json_object" }'
    )
    if 'error' in response: 
        print(response['error'])
        return None 
    else: 
        print("ChatGPT request successful with status code")
        return response.choices[0].message.content.strip()

def create_adversarial_context(context, percentage=50):
    # use call_GPT to generate adversarial context
    prompt = "Create an adversarial context for the following passage without changing the meaning."\
            "You can use techniques like, Paraphrasing, Negation, Noise Injection, Distraction (introducing words like Why, what, who, because etc. in between),"\
            "Word Swapping(adding synonyms and antonyms) and Contradictions. "\
            "Keep the length of output roughly similar to input, but make sure the meaning of the passage doesn't change - "
                # "Always return a valid JSON in response"
    
    prompt = prompt + context[1]
    
    adversarial_prompt = call_chatgpt("You are a AI research assistance, working on evaluating Language Models.", prompt)
    return (context[0], adversarial_prompt)

def create_adversarial_contexts(contexts, percentage=20):
    adversarial_contexts = []
    print('Contexts to update - ', len(contexts))

    with ProcessPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_adversarial_context, context, percentage) for context in contexts]
        for future in as_completed(futures):
            ad_context = future.result()
            if not ad_context is None:
                adversarial_contexts.append(ad_context)

    # for context in contexts:
    #     ad_context = create_adversarial_context(context[1], percentage)
    #     if not ad_context is None:
    #         adversarial_contexts.append((context[0], ad_context))
    return adversarial_contexts

# this batching is not supported by OpenAI with chat completion API
def create_adversarial_contexts_parallel(contexts, percentage=20):
    print('Contexts to update - ', len(contexts))

    # create an array of messages to send to the chatbot
    prompts = []
    for context in tqdm(contexts):
        s = "You are a AI research assistance, working on evaluating Language Models."
        p = "Create an adversarial context for the following passage without changing the meaning."\
            "You can use techniques like, Paraphrasing, Negation, Noise Injection, Distraction (introducing words like Why, what, who, because etc. in between),"\
            "Word Swapping(adding synonyms and antonyms) and Contradictions. "\
            "Keep the length of output roughly similar to input, but make sure the meaning of the passage doesn't change - "
        p = p + context[1]

        message = [
            {"role": "system", "content": s},
            {"role": "user", "content": p},
        ]
        prompts.append(message)

    # make call_chatgpt_parallel with 10 messages at once
    concurrency = 10
    max_token = 500
    adversarial_contexts = []
    for i in tqdm(range(0, len(prompts), concurrency)):
        batch = prompts[i:i+10]

        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=batch,
            seed=seed,
            max_tokens=max_token,
            temperature=0.9,
            # response_json=True,
            # response_format='{ "type": "json_object" }'
        )
        if 'error' in response: 
            print(response['error'])
            return None 
        else: 
            print("ChatGPT request successful with status code: {}".format(response['id']))
            # the response is sequential
            # we'll find context index from the id of the response
            for index, choice in enumerate(response.choices):
                curr_context = contexts[i+index]
                adversarial_contexts.append((curr_context[0], choice))
            
    return adversarial_contexts

def process_paragraph(paragraph, article):
    test_set = []
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

def convert_json(in_json):
    test_set = []
    for article in in_json['data']:
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

def process_ad_context(ad_context, squad_data):
    adv_context = []
    for article in squad_data['data']:
        for paragraph in article['paragraphs']:
            if hash(paragraph['context']) == ad_context[0]:
                paragraph['context'] = ad_context[1]
                context_counter += 1

                # we might need to save_only_changed_contexts, save them to adv context file
                data = process_paragraph(paragraph, article)
                adv_context.extend(data)
    return adv_context

def create_adversarial_dataset(original_file_path, adversarial_file_path, percent_context_to_change=20, save_only_changed_contexts=False):
    with open(original_file_path, 'r') as file:
        squad_data = json.load(file)
    
    # crete a hash of context as ID, this will be used to identify the context later
    # context is a tuple of (hash(context), context)
    contexts = [(hash(paragraph['context']), paragraph['context']) for article in squad_data['data'] for paragraph in article['paragraphs']]

    #  Shuffle the contexts
    random.shuffle(contexts)

    # extract the first percent_context_to_change% of contexts to change
    num_contexts_to_change = len(contexts) * percent_context_to_change // 100
    adversarial_contexts = create_adversarial_contexts(contexts[:num_contexts_to_change])

    # adversarial_contexts = create_adversarial_contexts_parallel(contexts[:num_contexts_to_change])
    context_counter = 0

    # The paragraph should be sequential, so the order of following loops 
    # should just be O(n)
    adversarial_data = []

    for ad_context in adversarial_contexts:
        for article in squad_data['data']:
            for paragraph in article['paragraphs']:
                if hash(paragraph['context']) == ad_context[0]:
                    paragraph['context'] = ad_context[1]
                    context_counter += 1

                    # we might need to save_only_changed_contexts, save them to adv context file
                    if save_only_changed_contexts:
                        data = process_paragraph(paragraph, article)
                        adversarial_data.extend(data)

                    break
        if context_counter == num_contexts_to_change:
            break
    
    
    if save_only_changed_contexts:
        with open(adversarial_file_path, 'w') as file:
            json.dump(adversarial_data, file)
        return

    # convert data to the format required by the model

    squad_data = convert_json(squad_data)

    with open(adversarial_file_path, 'w') as file:
        json.dump(squad_data, file)

# define the main entry point of the script
if __name__ == "__main__":
    # Prompt for a question
    orig_file_path = './Squad/train-v1.1.json'
    out_file_path = './Squad/train-v1.1-adversarial-50-diff-2.json'
    percent_context_to_change = 50
    create_adversarial_dataset(original_file_path=orig_file_path, 
                               adversarial_file_path=out_file_path,
                               percent_context_to_change=percent_context_to_change,
                               save_only_changed_contexts=True)
