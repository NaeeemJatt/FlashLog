
import pandas as pd

from logai.dataloader.data_model import LogRecordObject
from logai.utils import constants
from sklearn.model_selection import train_test_split

def split_train_dev_test_for_anomaly_detection(
        logrecord,
        training_type,
        test_data_frac_neg_class,
        test_data_frac_pos_class=None,
        shuffle=False,
):
    
    if training_type not in ["supervised", "unsupervised"]:
        raise ValueError("training_type must be either supervised or unsupervised")

    if training_type == "unsupervised":
        test_data_frac_pos_class = 1.0
    elif test_data_frac_pos_class is None:
        test_data_frac_pos_class = test_data_frac_neg_class

    if not shuffle:
        stratify = None
    else:
        stratify = logrecord.labels[constants.LABELS]

    train_ids, test_ids, train_labels, test_labels = train_test_split(
        logrecord.span_id[constants.SPAN_ID],
        logrecord.labels[constants.LABELS],
        test_size=0.2,
        shuffle=shuffle,
        stratify=stratify,
    )
    if not shuffle:
        stratify = None
    else:
        stratify = train_labels
    train_ids, dev_ids, train_labels, dev_labels = train_test_split(
        train_ids, train_labels, test_size=0.1, shuffle=shuffle, stratify=stratify
    )

    test_ids = list(set(test_ids))

    if training_type == "unsupervised":
        train_ids_labels = pd.DataFrame({"ids": train_ids, "labels": train_labels})
        train_ids_pos = train_ids_labels[train_ids_labels["labels"] == 1]["ids"]
        dev_ids_labels = pd.DataFrame({"ids": dev_ids, "labels": dev_labels})
        dev_ids_pos = dev_ids_labels[dev_ids_labels["labels"] == 1]["ids"]

        train_ids = train_ids_labels[train_ids_labels["labels"] == 0]["ids"]
        dev_ids = dev_ids_labels[dev_ids_labels["labels"] == 0]["ids"]

        test_ids.extend(train_ids_pos)
        test_ids.extend(dev_ids_pos)

        if len(dev_ids) == 0:
            train_ids, dev_ids = train_test_split(
                train_ids, test_size=0.1, shuffle=shuffle
            )

    else:
        train_ids = list(set(train_ids))
        dev_ids = list(set(dev_ids))

    indices_train = list(
        logrecord.span_id.loc[
            logrecord.span_id[constants.SPAN_ID].isin(train_ids)
        ].index
    )
    indices_dev = list(
        logrecord.span_id.loc[logrecord.span_id[constants.SPAN_ID].isin(dev_ids)].index
    )
    indices_test = list(
        logrecord.span_id.loc[logrecord.span_id[constants.SPAN_ID].isin(test_ids)].index
    )

    print(
        "indices_train/dev/test: ",
        len(indices_train),
        len(indices_dev),
        len(indices_test),
    )
    logrecord_train = logrecord.select_by_index(indices_train)
    logrecord_dev = logrecord.select_by_index(indices_dev)
    logrecord_test = logrecord.select_by_index(indices_test)

    return logrecord_train, logrecord_dev, logrecord_test
