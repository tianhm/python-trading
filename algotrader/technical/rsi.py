import numpy as np
from typing import Dict

from algotrader.technical import Indicator


def gain_loss(prev_value, next_value):
    change = next_value - prev_value
    if change < 0:
        gain = 0
        loss = abs(change)
    else:
        gain = change
        loss = 0
    return gain, loss


# [begin, end)
def avg_gain_loss(series, input_key, begin, end):
    range_len = end - begin
    if range_len < 2:
        return 0, 0

    gain = 0
    loss = 0
    for i in range(begin + 1, end):
        curr_gain, curr_loss = gain_loss(series[i - 1, input_key], series[i, input_key])
        gain += curr_gain
        loss += curr_loss
    return gain / float(range_len - 1), loss / float(range_len - 1)


def rsi(values, input_key, length):
    assert (length > 1)
    if len(values) > length:

        avg_gain, avg_loss = avg_gain_loss(values, input_key, 0, length)
        for i in range(length, len(values)):
            gain, loss = gain_loss(values[i - 1, input_key], values[i, input_key])
            avg_gain = (avg_gain * (length - 1) + gain) / float(length)
            avg_loss = (avg_loss * (length - 1) + loss) / float(length)

        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - 100 / (1 + rs)
    else:
        return np.nan


class RSI(Indicator):
    __slots__ = (
        'length',
        '__prev_gain',
        '__prev_loss'
    )

    def __init__(self, time_series=None, inputs=None, input_keys=None, desc="Relative Strength Indicator", length=14):
        super(RSI, self).__init__(time_series=time_series, inputs=inputs, input_keys=input_keys, desc=desc,
                                  length=length)
        self.length = self.get_int_config("length", 14)
        self.__prev_gain = None
        self.__prev_loss = None
        #super(RSI, self)._update_from_inputs()

    def _process_update(self, source: str, timestamp: int, data: Dict[str, float]):
        result = {}
        if self.first_input.size() > self.length:
            if self.__prev_gain is None:
                avg_gain, avg_loss = avg_gain_loss(self.first_input, self.first_input_keys[0], 0, self.first_input.size())
            else:
                prev_value = self.first_input.ago(1, self.first_input_keys[0])
                curr_value = self.first_input.now(self.first_input_keys[0])
                curr_gain, curr_loss = gain_loss(prev_value, curr_value)
                avg_gain = (self.__prev_gain * (self.length - 1) + curr_gain) / float(self.length)
                avg_loss = (self.__prev_loss * (self.length - 1) + curr_loss) / float(self.length)

            if avg_loss == 0:
                rsi_value = 100
            else:
                rs = avg_gain / avg_loss
                rsi_value = 100 - 100 / (1 + rs)
                self.__prev_gain = avg_gain
                self.__prev_loss = avg_loss

            result[Indicator.VALUE] = rsi_value
        else:
            result[Indicator.VALUE] = np.nan

        self.add(timestamp=timestamp, data=result)

# if __name__ == "__main__":
#     import datetime
#     from algotrader.trading.data_series import DataSeries
#
#     close = DataSeries("close")
#     rsi = RSI(close, input_key='close', length=14)
#     print(rsi.name)
#     t = datetime.datetime.now()
#
#     values = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
#               45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00]
#
#     for idx, value in enumerate(values):
#         close.add(timestamp=t, data={'close': value})
#         t = t + datetime.timedelta(0, 3)
#
#         print(idx, rsi.now())
