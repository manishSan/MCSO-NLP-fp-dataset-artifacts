# Running on multiple GPUs - CUDA multiporcessing
# from multiprocess import set_start_method
# set_start_method('spawn')

import datasets
import nltk
import numpy as np

def load_snli(split='train'):
    # we might later improve this method to load database from local file

    dataset_id = "snli"
    dataset = datasets.load_dataset(dataset_id, split=split)
    return dataset

def augment_snli(dataset, n_aug=10):
    import nltk
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('punkt')
    
    print(f"Augmenting {dataset.num_rows} rows of SNLI dataset")
    updated_dataset = dataset.map(augment_snli_row, batched=True, batch_size=64, num_proc=1)
    return updated_dataset

def augment_snli_row(batch):
    premises = batch['premise']
    hypotheses = batch['hypothesis']
    labels = batch['label']

    output = {'premise':[],
              'hypothesis':[],
              'label':[]
              }
    for p, h, l in zip(premises, hypotheses, labels):
        from nltk.corpus import wordnet as wn
        from nltk.stem.wordnet import WordNetLemmatizer
        from nltk.tokenize import word_tokenize
        from nltk.tag import pos_tag
        from collections import defaultdict

        tag_map = defaultdict(lambda : wn.NOUN)
        tag_map['J'] = wn.ADJ
        tag_map['V'] = wn.VERB
        tag_map['R'] = wn.ADV

       
        # lemmatize premise
        lemmatizer = WordNetLemmatizer()
        for token, tag in pos_tag(word_tokenize(p)):
            lemma = lemmatizer.lemmatize(token, tag_map[tag[0]])
            p = p.replace(token, lemma)

        np.random.seed(42)
        # lemmatize hypothesis
        for token, tag in pos_tag(word_tokenize(h)):
            lemma = lemmatizer.lemmatize(token, tag_map[tag[0]])

            # skip noun pos
            if tag_map[tag[0]] == wn.NOUN:
                continue

            # find synonyms for the word
            synonyms = wn.synonyms(lemma)
            # filter synonyms to remove empty arrays 
            synonyms = [s for s in synonyms if len(s) > 0]
            if len(synonyms) > 0:
                # uniformly choose a synonym
                np.random.shuffle(synonyms)
                synonym = synonyms[0][0]
                h = h.replace(token, synonym)
        
        # is label is not in {0, 1, 2} the replace it with 0
        if l not in [0, 1, 2]:
            l = 0

        output['premise'].append(p)
        output['hypothesis'].append(h)
        output['label'].append(l)

    return output

# define main for file entry
if __name__ == "__main__":
    split = 'validation'
    dataset = load_snli(split)
    aug_dataset = augment_snli(dataset)
    aug_dataset_dict = datasets.DatasetDict(
        {split: aug_dataset}
    )
    # aug_dataset = {split: aug_dataset}
    print("saving to disk")
    aug_dataset_dict.save_to_disk('snli_aug_{split}.hf'.format(split=split))
    aug_dataset.to_json('snli_aug_{split}.json'.format(split=split))

