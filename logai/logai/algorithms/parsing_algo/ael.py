
import re
import hashlib
import pandas as pd
from collections import defaultdict
from functools import reduce
from dataclasses import dataclass

from logai.algorithms.algo_interfaces import ParsingAlgo
from logai.config_interfaces import Config
from logai.algorithms.factory import factory

class Event:
    
    def __init__(self, logidx, Eventstr=""):
        self.id = hashlib.md5(Eventstr.encode("utf-8")).hexdigest()[0:8]
        self.logs = [logidx]
        self.Eventstr = Eventstr
        self.EventToken = Eventstr.split()
        self.merged = False

    def refresh_id(self):
        
        self.id = hashlib.md5(self.Eventstr.encode("utf-8")).hexdigest()[0:8]

@dataclass
class AELParams(Config):
    
    rex: str = None
    minEventCount: int = 2
    merge_percent: int = 1
    keep_para: bool = True

@factory.register("parsing", "ael", AELParams)
class AEL(ParsingAlgo):
    def __init__(self, params: AELParams):
        self.rex = params.rex
        self.minEventCount = params.minEventCount
        self.merge_percent = params.merge_percent
        self.df_log = None
        self.logname = None
        self.merged_events = []
        self.bins = defaultdict(dict)
        self.keep_para = params.keep_para

    def fit(self, loglines: pd.DataFrame):
        
        pass

    def parse(self, loglines: pd.Series) -> pd.Series:

        from logai.utils.log_normalizer import LogNormalizer, NormalizationConfig
        
        normalizer_config = NormalizationConfig(
            normalize_ips=True,
            normalize_ports=True,
            normalize_timestamps=True,
            normalize_uuids=True,
            normalize_hashes=True,
            normalize_file_paths=True,
            normalize_hex_values=True,
            enable_caching=True
        )
        normalizer = LogNormalizer(normalizer_config)
        
        normalized_loglines = normalizer.normalize_batch(loglines.tolist())
        loglines = pd.Series(normalized_loglines, index=loglines.index)
        
        self.logname = "logname"
        self.load_data(loglines)
        self.tokenize()
        self.categorize()
        self.reconcile()

        templateL = [0] * self.df_log.shape[0]

        for event in self.merged_events:
            for logidx in event.logs:
                templateL[logidx] = event.Eventstr

        return pd.Series(templateL, index=loglines.index)

    def tokenize(self):
        
        for idx, log in self.df_log["Content_"].items():
            para_count = 0

            tokens = log.split()
            for token in tokens:
                if token == "<*>":
                    para_count += 1

            if "Logs" not in self.bins[(len(tokens), para_count)]:
                self.bins[(len(tokens), para_count)]["Logs"] = [idx]
            else:
                self.bins[(len(tokens), para_count)]["Logs"].append(idx)

    def categorize(self):
        
        for key in self.bins:
            abin = self.bins[key]
            abin["Events"] = []

            for logidx in abin["Logs"]:
                log = self.df_log["Content_"].loc[logidx]
                matched = False
                for event in abin["Events"]:
                    if log == event.Eventstr:
                        matched = True
                        event.logs.append(logidx)
                        break
                if not matched:
                    abin["Events"].append(Event(logidx, log))

    def reconcile(self):
        
        for key in self.bins:
            abin = self.bins[key]
            if len(abin["Events"]) > self.minEventCount:
                tobeMerged = []
                for e1 in abin["Events"]:
                    if e1.merged:
                        continue
                    e1.merged = True
                    tobeMerged.append([e1])

                    for e2 in abin["Events"]:
                        if e2.merged:
                            continue
                        if self.has_diff(e1.EventToken, e2.EventToken):
                            tobeMerged[-1].append(e2)
                            e2.merged = True
                for Es in tobeMerged:
                    merged_event = reduce(self.merge_event, Es)
                    merged_event.refresh_id()
                    self.merged_events.append(merged_event)
            else:
                for e in abin["Events"]:
                    self.merged_events.append(e)

    def merge_event(self, e1, e2):
        
        for pos in range(len(e1.EventToken)):
            if e1.EventToken[pos] != e2.EventToken[pos]:
                e1.EventToken[pos] = "<*>"

        e1.logs.extend(e2.logs)
        e1.Eventstr = " ".join(e1.EventToken)

        return e1

    def has_diff(self, tokens1: list, tokens2: list):
        
        diff = 0
        for idx in range(len(tokens1)):
            if tokens1[idx] != tokens2[idx]:
                diff += 1
        return True if 0 < diff * 1.0 / len(tokens1) <= self.merge_percent else False

    def load_data(self, loglines: pd.Series):
        
        def preprocess(log):
            if self.rex:
                for currentRex in self.rex:
                    log = re.sub(currentRex, "<*>", log)
            return log

        self.df_log = pd.DataFrame(loglines)
        self.df_log["Content_"] = self.df_log[loglines.name].map(preprocess)
