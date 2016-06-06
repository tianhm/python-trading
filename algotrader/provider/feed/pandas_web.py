import logging
from datetime import date

import pandas as pd
import pandas.io.data as web

from algotrader.event import EventBus
from algotrader.event import EventLogger
from algotrader.event.order import *
from algotrader.provider import *
from algotrader.trading.ref_data import inmemory_ref_data_mgr
from algotrader.utils import logger


class PandasWebDataFeed(Feed):
    __metaclass__ = abc.ABCMeta

    def __init__(self, system, ref_data_mgr=None, data_event_bus=None):
        self.system = system
        self.__ref_data_mgr = ref_data_mgr if ref_data_mgr else inmemory_ref_data_mgr
        self.__data_event_bus = data_event_bus if data_event_bus else EventBus.data_subject

        feed_mgr.register(self)

    def start(self):
        pass

    def stop(self):
        pass

    def subscribe_all_mktdata(self, sub_keys):
        self.__load_data([sub_keys])

    def subscribe_mktdata(self, sub_key):
        self.__load_data([sub_key])


    @abc.abstractmethod
    def process_row(self, row):
        raise NotImplementedError


    def __load_data(self, sub_keys):

        self.dfs = []
        for sub_key in sub_keys:
            if not isinstance(sub_key, HistDataSubscriptionKey):
                raise RuntimeError("only HistDataSubscriptionKey is supported!")
            if sub_key.data_type == Bar and sub_key.bar_type == BarType.Time and sub_key.bar_size == BarSize.D1:
                inst = self.__ref_data_mgr.get_inst(inst_id=sub_key.inst_id)
                symbol = inst.get_symbol(self.ID)

                df = web.DataReader("F", self.system, sub_key.from_date, sub_key.to_date)
                df['Symbol'] = symbol
                df['BarSize'] = int(BarSize.D1)

                self.dfs.append(df)

        self.df = pd.concat(self.dfs).sort_index(0, ascending=True)

        for index, row in self.df.iterrows():
            ## TODO support bar filtering // from date, to date
            bar = self.process_row(index, row)
            self.__data_event_bus.on_next(bar)

    def unsubscribe_mktdata(self, sub_key):
        pass


class YahooDataFeed(PandasWebDataFeed):
    ID = "Yahoo"
    URL = 'http://real-chart.finance.yahoo.com/table.csv?s=%s&d=%s&e=%s&f=%s&g=d&a=%s&b=%s&c=%s&ignore=.csv'

    def __init__(self, ref_data_mgr=None, data_event_bus=None):
        super(YahooDataFeed, self).__init__(system='yahoo', ref_data_mgr=ref_data_mgr, data_event_bus=data_event_bus)

    def id(self):
        return YahooDataFeed.ID


    def process_row(self, index, row):
        return Bar(instrument=row['Symbol'],
                   timestamp=index,
                   open=row['Open'],
                   high=row['High'],
                   low=row['Low'],
                   close=row['Close'],
                   vol=row['Volume'],
                   adj_close=row['Adj Close'],
                   size=row['BarSize'])

class GoogleDataFeed(PandasWebDataFeed):
    ID = "Google"

    def __init__(self, ref_data_mgr=None, data_event_bus=None):
        super(GoogleDataFeed, self).__init__(system='google', ref_data_mgr=ref_data_mgr, data_event_bus=data_event_bus)

    def id(self):
        return GoogleDataFeed.ID


    def process_row(self, index, row):
        return Bar(instrument=row['Symbol'],
                   timestamp=index,
                   open=row['Open'],
                   high=row['High'],
                   low=row['Low'],
                   close=row['Close'],
                   vol=row['Volume'],
                   size=row['BarSize'])

if __name__ == "__main__":
    feed = YahooDataFeed()

    today = date.today()
    sub_key = HistDataSubscriptionKey(inst_id=3, provider_id=YahooDataFeed.ID, data_type=Bar, bar_size=BarSize.D1,
                                      from_date=datetime.datetime(2010, 1, 1), to_date=today)

    logger.setLevel(logging.DEBUG)
    eventLogger = EventLogger()

    feed.subscribe_mktdata(sub_key)