
import re

import pandas as pd

def generate_logformat_regex(log_format):
    
    headers = []
    splitters = re.split(r"(<[^<>]+>)", log_format)
    regex = ""
    for k in range(len(splitters)):
        if k % 2 == 0:
            splitter = re.sub(" +", "\\\s+", splitters[k])
            regex += splitter
        else:
            header = splitters[k].strip("<").strip(">")
            regex += "(?P<%s>.*?)" % header
            headers.append(header)
    regex = re.compile("^" + regex + "$")
    return headers, regex

def log_to_dataframe(log_file, regex, headers):
    
    log_messages = []
    linecount = 0
    cnt = 0
    with open(log_file, "r", encoding="utf8", errors="ignore") as fin:
        for line in fin.readlines():
            cnt += 1
            try:
                match = regex.search(line.strip())
                message = [match.group(header) for header in headers]
                log_messages.append(message)
                linecount += 1
            except Exception as e:
                pass
    print("Total size after encoding is", linecount, cnt)
    logdf = pd.DataFrame(log_messages, columns=headers, dtype=str)
    return logdf

def load_data(filename, log_format):
    
    headers, regex = generate_logformat_regex(log_format)
    df_log = log_to_dataframe(filename, regex, headers)
    return df_log
