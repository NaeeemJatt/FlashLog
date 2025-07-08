
from enum import Enum

DIGITS_SUB = "[DIGITS]"
TIMESTAMP = "[TIMESTAMP]"

class Field(str, Enum):
    TIMESTAMP = "timestamp"
    BODY = "body"
    ATTRIBUTES = "attributes"
    RESOURCE = "resource"
    SPAN_ID = "span_id"
    LABELS = "labels"

LOGLINE_NAME = "logline"
NEXT_LOGLINE_NAME = "next_logline"
PARSED_LOGLINE_NAME = "parsed_logline"
PARAMETER_LIST_NAME = "parameter_list"
LOG_EVENTS = "log_events"
LOG_TIMESTAMPS = "timestamp"
SPAN_ID = "span_id"
EVENT_INDEX = "event_index"
LABELS = "labels"

LOG_COUNTS = "counts"

MIN_TS_LENGTH = 10
COUNTER_AD_ALGO = []
