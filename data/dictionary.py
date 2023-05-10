from nltk.corpus import words

DICTIONARY_WORDS = set(words.words())
CUSTOM_WORDS = set()
ALL_WORDS = DICTIONARY_WORDS | CUSTOM_WORDS

def is_word_legal(word):
    return word in ALL_WORDS