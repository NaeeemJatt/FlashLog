
import pandas as pd

from logai.algorithms.parsing_algo.iplom import IPLoMParams, IPLoM

from tests.logai.test_utils.fixtures import logrecord_body

class TestIPLoM:
    def setup(self):
        self.params = IPLoMParams()

    def test_fit_parse(self, logrecord_body):
        parser = IPLoM(self.params)
        parser.fit(logrecord_body['logline'])
        parsed_loglines = parser.parse(logrecord_body['logline'])
        assert isinstance(parser, IPLoM)
        assert isinstance(parsed_loglines, pd.Series), 'parse returns pandas.Series'
