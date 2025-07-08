
import re
import sys
import pandas as pd
from collections import defaultdict
from dataclasses import dataclass

from logai.algorithms.algo_interfaces import ParsingAlgo
from logai.config_interfaces import Config

import copy
import hashlib

from logai.algorithms.factory import factory
from logai.utils.log_normalizer import LogNormalizer, NormalizationConfig

class Partition:
    
    def __init__(self, stepNo, numOfLogs=0, lenOfLogs=0):
        self.logLL = []
        self.stepNo = stepNo
        self.valid = True
        self.numOfLogs = numOfLogs
        self.lenOfLogs = lenOfLogs

class Event:
    
    def __init__(self, eventStr):
        self.eventStr = eventStr
        self.eventId = hashlib.md5(" ".join(eventStr).encode("utf-8")).hexdigest()[0:8]
        self.eventCount = 0

@dataclass
class IPLoMParams(Config):
    
    rex: str = None
    logformat: str = None
    maxEventLen: int = 200
    step2Support: float = 0
    PST: float = 0
    CT: float = 0
    lowerBound: float = 0.25
    upperBound: float = 0.9
    keep_para: bool = True

@factory.register("parsing", "iplom", IPLoMParams)
class IPLoM(ParsingAlgo):
    
    def __init__(self, params: IPLoMParams):
        self.para = params
        self.partitionsL = []
        self.eventsL = []
        self.output = []
        self.keep_para = params.keep_para

        for logLen in range(self.para.maxEventLen + 1):
            self.partitionsL.append(Partition(stepNo=1, numOfLogs=0, lenOfLogs=logLen))

    def fit(self, loglines: pd.Series):
        
        pass

    def parse(self, loglines: pd.Series) -> pd.Series:
        
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
        
        self._Step1(loglines)
        self._Step2()
        self._Step3()
        self._Step4()
        self._getOutput()
        eventID_template = {
            event.eventId: " ".join(event.eventStr) for event in self.eventsL
        }

        self.output.sort(key=lambda x: int(x[0]))
        res = pd.Series(
            [eventID_template[logL[1]] for logL in self.output], index=loglines.index
        )
        return res

    def _Step1(self, loglines: pd.Series):
        self.df_log = pd.DataFrame(loglines)
        lineCount = 1
        for idx, line in self.df_log.iterrows():
            line = line[loglines.name]

            if line.strip() == "":
                continue

            if self.para.rex:
                for currentRex in self.para.rex:
                    line = re.sub(currentRex, "", line)

            wordSeq = list(filter(lambda x: x != "", re.split(r"[\s=:,]", line)))
            if not wordSeq:
                wordSeq = [" "]

            wordSeq.append(str(lineCount))
            lineCount += 1

            self.partitionsL[len(wordSeq) - 1].logLL.append(wordSeq)
            self.partitionsL[len(wordSeq) - 1].numOfLogs += 1

        for partition in self.partitionsL:
            if partition.numOfLogs == 0:
                partition.valid = False

            elif (
                self.para.PST != 0
                and 1.0 * partition.numOfLogs / lineCount < self.para.PST
            ):
                for logL in partition.logLL:
                    self.partitionsL[0].logLL.append(logL)
                    self.partitionsL[0].numOfLogs += 1
                partition.valid = False

    def _Step2(self):

        for partition in self.partitionsL:

            if not partition.valid:
                continue

            if partition.numOfLogs <= self.para.step2Support:
                continue

            if partition.stepNo == 2:
                break

            uniqueTokensCountLS = []
            for columnIdx in range(partition.lenOfLogs):
                uniqueTokensCountLS.append(set())

            for logL in partition.logLL:
                for columnIdx in range(partition.lenOfLogs):
                    uniqueTokensCountLS[columnIdx].add(logL[columnIdx])

            minColumnIdx = 0
            minColumnCount = len(uniqueTokensCountLS[0])

            for columnIdx in range(partition.lenOfLogs):
                if minColumnCount > len(uniqueTokensCountLS[columnIdx]):
                    minColumnCount = len(uniqueTokensCountLS[columnIdx])
                    minColumnIdx = columnIdx

            if minColumnCount == 1:
                continue

            logDLL = {}
            for logL in partition.logLL:
                if logL[minColumnIdx] not in logDLL:
                    logDLL[logL[minColumnIdx]] = []
                logDLL[logL[minColumnIdx]].append(logL)

            for key in logDLL:
                if (
                    self.para.PST != 0
                    and 1.0 * len(logDLL[key]) / partition.numOfLogs < self.para.PST
                ):
                    self.partitionsL[0].logLL += logDLL[key]
                    self.partitionsL[0].numOfLogs += len(logDLL[key])
                else:
                    newPartition = Partition(
                        stepNo=2,
                        numOfLogs=len(logDLL[key]),
                        lenOfLogs=partition.lenOfLogs,
                    )
                    newPartition.logLL = logDLL[key]
                    self.partitionsL.append(newPartition)

            partition.valid = False

    def _Step3(self):

        for partition in self.partitionsL:

            if not partition.valid:
                continue

            if partition.stepNo == 3:
                break

            p1, p2 = self.DetermineP1P2(partition)

            if p1 == -1 or p2 == -1:
                continue

            try:

                p1Set = set()
                p2Set = set()
                mapRelation1DS = {}
                mapRelation2DS = {}

                for logL in partition.logLL:
                    p1Set.add(logL[p1])
                    p2Set.add(logL[p2])

                    if logL[p1] == logL[p2]:
                        print("Warning: p1 may be equal to p2")

                    if logL[p1] not in mapRelation1DS:
                        mapRelation1DS[logL[p1]] = set()
                    mapRelation1DS[logL[p1]].add(logL[p2])

                    if logL[p2] not in mapRelation2DS:
                        mapRelation2DS[logL[p2]] = set()
                    mapRelation2DS[logL[p2]].add(logL[p1])

                oneToOneS = set()
                oneToMP1D = {}
                oneToMP2D = {}

                for p1Token in p1Set:
                    if len(mapRelation1DS[p1Token]) == 1:
                        if len(mapRelation2DS[list(mapRelation1DS[p1Token])[0]]) == 1:
                            oneToOneS.add(p1Token)

                    else:
                        isOneToM = True

                        for p2Token in mapRelation1DS[p1Token]:
                            if len(mapRelation2DS[p2Token]) != 1:
                                isOneToM = False
                                break
                        if isOneToM:
                            oneToMP1D[p1Token] = 0

                for deleteToken in oneToOneS:
                    p1Set.remove(deleteToken)
                    p2Set.remove(list(mapRelation1DS[deleteToken])[0])

                for deleteToken in oneToMP1D:
                    for deleteTokenP2 in mapRelation1DS[deleteToken]:
                        p2Set.remove(deleteTokenP2)
                    p1Set.remove(deleteToken)

                for p2Token in p2Set:
                    if len(mapRelation2DS[p2Token]) != 1:
                        isOneToM = True
                        for p1Token in mapRelation2DS[p2Token]:
                            if len(mapRelation1DS[p1Token]) != 1:
                                isOneToM = False
                                break
                        if isOneToM:
                            oneToMP2D[p2Token] = 0

                for deleteToken in oneToMP2D:
                    p2Set.remove(deleteToken)
                    for deleteTokenP1 in mapRelation2DS[deleteToken]:
                        p1Set.remove(deleteTokenP1)

                for logL in partition.logLL:
                    if logL[p1] in oneToMP1D:
                        oneToMP1D[logL[p1]] += 1

                    if logL[p2] in oneToMP2D:
                        oneToMP2D[logL[p2]] += 1

            except KeyError as er:
                print(er)
                print("error: " + str(p1) + "\t" + str(p2))

            newPartitionsD = {}
            if partition.stepNo == 2:
                newPartitionsD["dumpKeyforMMrelationInStep2__"] = Partition(
                    stepNo=3, numOfLogs=0, lenOfLogs=partition.lenOfLogs
                )

            for logL in partition.logLL:

                if logL[p1] in oneToOneS:
                    if logL[p1] not in newPartitionsD:
                        newPartitionsD[logL[p1]] = Partition(
                            stepNo=3, numOfLogs=0, lenOfLogs=partition.lenOfLogs
                        )
                    newPartitionsD[logL[p1]].logLL.append(logL)
                    newPartitionsD[logL[p1]].numOfLogs += 1

                elif logL[p1] in oneToMP1D:
                    split_rank = self.Get_Rank_Posistion(
                        len(mapRelation1DS[logL[p1]]), oneToMP1D[logL[p1]], True
                    )
                    if split_rank == 1:
                        if logL[p1] not in newPartitionsD:
                            newPartitionsD[logL[p1]] = Partition(
                                stepNo=3, numOfLogs=0, lenOfLogs=partition.lenOfLogs
                            )
                        newPartitionsD[logL[p1]].logLL.append(logL)
                        newPartitionsD[logL[p1]].numOfLogs += 1
                    else:
                        if logL[p2] not in newPartitionsD:
                            newPartitionsD[logL[p2]] = Partition(
                                stepNo=3, numOfLogs=0, lenOfLogs=partition.lenOfLogs
                            )
                        newPartitionsD[logL[p2]].logLL.append(logL)
                        newPartitionsD[logL[p2]].numOfLogs += 1

                elif logL[p2] in oneToMP2D:
                    split_rank = self.Get_Rank_Posistion(
                        len(mapRelation2DS[logL[p2]]), oneToMP2D[logL[p2]], False
                    )
                    if split_rank == 1:
                        if logL[p1] not in newPartitionsD:
                            newPartitionsD[logL[p1]] = Partition(
                                stepNo=3, numOfLogs=0, lenOfLogs=partition.lenOfLogs
                            )
                        newPartitionsD[logL[p1]].logLL.append(logL)
                        newPartitionsD[logL[p1]].numOfLogs += 1
                    else:
                        if logL[p2] not in newPartitionsD:
                            newPartitionsD[logL[p2]] = Partition(
                                stepNo=3, numOfLogs=0, lenOfLogs=partition.lenOfLogs
                            )
                        newPartitionsD[logL[p2]].logLL.append(logL)
                        newPartitionsD[logL[p2]].numOfLogs += 1

                else:
                    if partition.stepNo == 2:
                        newPartitionsD["dumpKeyforMMrelationInStep2__"].logLL.append(
                            logL
                        )
                        newPartitionsD["dumpKeyforMMrelationInStep2__"].numOfLogs += 1
                    else:
                        if len(p1Set) < len(p2Set):
                            if logL[p1] not in newPartitionsD:
                                newPartitionsD[logL[p1]] = Partition(
                                    stepNo=3, numOfLogs=0, lenOfLogs=partition.lenOfLogs
                                )
                            newPartitionsD[logL[p1]].logLL.append(logL)
                            newPartitionsD[logL[p1]].numOfLogs += 1
                        else:
                            if logL[p2] not in newPartitionsD:
                                newPartitionsD[logL[p2]] = Partition(
                                    stepNo=3, numOfLogs=0, lenOfLogs=partition.lenOfLogs
                                )
                            newPartitionsD[logL[p2]].logLL.append(logL)
                            newPartitionsD[logL[p2]].numOfLogs += 1

            if (
                "dumpKeyforMMrelationInStep2__" in newPartitionsD
                and newPartitionsD["dumpKeyforMMrelationInStep2__"].numOfLogs == 0
            ):
                newPartitionsD["dumpKeyforMMrelationInStep2__"].valid = False

            for key in newPartitionsD:
                if (
                    self.para.PST != 0
                    and 1.0 * newPartitionsD[key].numOfLogs / partition.numOfLogs
                    < self.para.PST
                ):
                    self.partitionsL[0].logLL += newPartitionsD[key].logLL
                    self.partitionsL[0].numOfLogs += newPartitionsD[key].numOfLogs
                else:
                    self.partitionsL.append(newPartitionsD[key])

            partition.valid = False

    def _Step4(self):
        self.partitionsL[0].valid = False
        if self.para.PST == 0 and self.partitionsL[0].numOfLogs != 0:
            event = Event(["Outlier"])
            event.eventCount = self.partitionsL[0].numOfLogs
            self.eventsL.append(event)

            for logL in self.partitionsL[0].logLL:
                logL.append(str(event.eventId))

        for partition in self.partitionsL:
            if not partition.valid:
                continue

            if partition.numOfLogs == 0:
                print(str(partition.stepNo) + "\t")

            uniqueTokensCountLS = []
            for columnIdx in range(partition.lenOfLogs):
                uniqueTokensCountLS.append(set())

            for logL in partition.logLL:
                for columnIdx in range(partition.lenOfLogs):
                    uniqueTokensCountLS[columnIdx].add(logL[columnIdx])

            e = copy.deepcopy(partition.logLL[0])[: partition.lenOfLogs]

            for columnIdx in range(partition.lenOfLogs):
                if len(uniqueTokensCountLS[columnIdx]) == 1:
                    continue
                else:
                    e[columnIdx] = "<*>"

            event = Event(e)
            event.eventCount = partition.numOfLogs

            self.eventsL.append(event)

            for logL in partition.logLL:
                logL.append(str(event.eventId))

    def _getOutput(self):
        if self.para.PST == 0 and self.partitionsL[0].numOfLogs != 0:
            for logL in self.partitionsL[0].logLL:
                self.output.append(logL[-2:] + logL[:-2])
        for partition in self.partitionsL:
            if not partition.valid:
                continue
            for logL in partition.logLL:
                self.output.append(logL[-2:] + logL[:-2])

    def Get_Rank_Posistion(self, cardOfS, Lines_that_match_S, one_m):
        try:
            distance = 1.0 * cardOfS / Lines_that_match_S
        except ZeroDivisionError as er1:
            print(er1)
            print(
                "cardOfS: "
                + str(cardOfS)
                + "\t"
                + "Lines_that_match_S: "
                + str(Lines_that_match_S)
            )

        if distance <= self.para.lowerBound:
            if one_m:
                split_rank = 2
            else:
                split_rank = 1
        elif distance >= self.para.upperBound:
            if one_m:
                split_rank = 1
            else:
                split_rank = 2
        else:
            if one_m:
                split_rank = 1
            else:
                split_rank = 2

        return split_rank

    def DetermineP1P2(self, partition):
        if partition.lenOfLogs > 2:
            count_1 = 0

            uniqueTokensCountLS = []
            for columnIdx in range(partition.lenOfLogs):
                uniqueTokensCountLS.append(set())

            for logL in partition.logLL:
                for columnIdx in range(partition.lenOfLogs):
                    uniqueTokensCountLS[columnIdx].add(logL[columnIdx])

            for columnIdx in range(partition.lenOfLogs):
                if len(uniqueTokensCountLS[columnIdx]) == 1:
                    count_1 += 1

            GC = 1.0 * count_1 / partition.lenOfLogs

            if GC < self.para.CT:
                return self.Get_Mapping_Position(partition, uniqueTokensCountLS)
            else:
                return (-1, -1)

        elif partition.lenOfLogs == 2:
            return (0, 1)
        else:
            return (-1, -1)

    def Get_Mapping_Position(self, partition, uniqueTokensCountLS):
        p1 = p2 = -1

        numOfUniqueTokensD = {}
        for columnIdx in range(partition.lenOfLogs):
            if len(uniqueTokensCountLS[columnIdx]) not in numOfUniqueTokensD:
                numOfUniqueTokensD[len(uniqueTokensCountLS[columnIdx])] = 0
            numOfUniqueTokensD[len(uniqueTokensCountLS[columnIdx])] += 1

        if partition.stepNo == 2:

            maxIdx = secondMaxIdx = -1
            maxCount = secondMaxCount = 0
            for key in numOfUniqueTokensD:
                if key == 1:
                    continue
                if numOfUniqueTokensD[key] > maxCount:
                    secondMaxIdx = maxIdx
                    secondMaxCount = maxCount
                    maxIdx = key
                    maxCount = numOfUniqueTokensD[key]
                elif (
                    numOfUniqueTokensD[key] > secondMaxCount
                    and numOfUniqueTokensD[key] != maxCount
                ):
                    secondMaxIdx = key
                    secondMaxCount = numOfUniqueTokensD[key]

            if maxCount > 1:
                for columnIdx in range(partition.lenOfLogs):
                    if len(uniqueTokensCountLS[columnIdx]) == maxIdx:
                        if p1 == -1:
                            p1 = columnIdx
                        else:
                            p2 = columnIdx
                            break

            else:
                for columnIdx in range(partition.lenOfLogs):
                    if len(uniqueTokensCountLS[columnIdx]) == maxIdx:
                        p1 = columnIdx
                        break

                for columnIdx in range(partition.lenOfLogs):
                    if len(uniqueTokensCountLS[columnIdx]) == secondMaxIdx:
                        p2 = columnIdx
                        break

            if p1 == -1 or p2 == -1:
                return (-1, -1)
            else:
                return (p1, p2)

        else:
            minIdx = secondMinIdx = -1
            minCount = secondMinCount = sys.maxsize
            for key in numOfUniqueTokensD:
                if numOfUniqueTokensD[key] < minCount:
                    secondMinIdx = minIdx
                    secondMinCount = minCount
                    minIdx = key
                    minCount = numOfUniqueTokensD[key]
                elif (
                    numOfUniqueTokensD[key] < secondMinCount
                    and numOfUniqueTokensD[key] != minCount
                ):
                    secondMinIdx = key
                    secondMinCount = numOfUniqueTokensD[key]

            for columnIdx in range(len(uniqueTokensCountLS)):
                if numOfUniqueTokensD[len(uniqueTokensCountLS[columnIdx])] == minCount:
                    if p1 == -1:
                        p1 = columnIdx
                        break

            for columnIdx in range(len(uniqueTokensCountLS)):
                if (
                    numOfUniqueTokensD[len(uniqueTokensCountLS[columnIdx])]
                    == secondMinCount
                ):
                    p2 = columnIdx
                    break

            return (p1, p2)

    def PrintPartitions(self):
        for idx in range(len(self.partitionsL)):
            print(
                "Partition {}:(from step {})    Valid:{}".format(
                    idx, self.partitionsL[idx].stepNo, self.partitionsL[idx].valid
                )
            )

            for log in self.partitionsL[idx].logLL:
                print(log)

    def PrintEventStats(self):
        for event in self.eventsL:
            if event.eventCount > 1:
                print(str(event.eventId) + "\t" + str(event.eventCount))
                print(event.eventStr)
