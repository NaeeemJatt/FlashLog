
import pandas as pd

from logai.utils import constants
from logai.utils.functions import get_parameter_list

def test_get_parameter_list():
    data = {
        constants.LOGLINE_NAME:
            ["This is a dataset structure logline",
             "This is a dataset structure logline"
             ],
        constants.PARSED_LOGLINE_NAME:
            [
                "This is a * logline",
                "This is a * logline"
            ]
    }
    df = pd.DataFrame.from_dict(data)

    para_list = df.apply(get_parameter_list, axis=1)
    assert len(para_list) == 2, "parameter list length should be 2"
    assert para_list[0][0] == 'dataset structure', "parameter list should contain the right terms"
