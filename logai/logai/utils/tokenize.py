
import itertools
import re
import string

from logai.utils import constants

def replace_delimeters(logline, delimeter_regex):
    
    return logline.replace(delimeter_regex, " ")

def tokenize(logline, config):
    
    logline = " ".join(
        ["".join(g).strip() for k, g in itertools.groupby(logline, str.isalpha)]
    )
    logline = " ".join(
        [x for x in logline.split(" ") if len(x) > 0 and x not in string.punctuation]
    )
    return logline

def _tokenize_camel_case(logline):
    return re.sub(
        "([A-Z][a-z]+)", r" \1", re.sub("([A-Z]+)", r" \1", str(logline))
    ).strip()

def _tokenize_replace_digits(logline):
    tokens = []
    digits = []
    for t in logline.split():

        if t.isdigit():
            tokens.append(constants.DIGITS_SUB)
            digits.append(t)
        else:
            tokens.append(t)

    return " ".join(tokens)
