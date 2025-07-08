
import pandas as pd

from logai.algorithms.parsing_algo.ael import AELParams, AEL
from logai.algorithms.parsing_algo.iplom import IPLoMParams, IPLoM

from tests.logai.test_utils.fixtures import logrecord_body

class TestAEL:
    def setup(self):
        self.params = AELParams()

    def test_fit_parse(self, logrecord_body):
        parser = AEL(self.params)
        assert isinstance(parser, AEL)
        parser.fit(logrecord_body['logline'])
        parsed_loglines = parser.parse(logrecord_body['logline'])

        assert isinstance(parsed_loglines, pd.Series), 'parse returns pandas.Series'
