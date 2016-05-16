import abc
import csv
import os


class InstType:
    Stock = 'STK'
    Future = 'FUT'
    Option = 'OPT'
    FutureOption = 'FOT'
    Index = 'IDX'
    CASH = 'CASH'
    ETF = 'ETF'
    Combo = 'CBO'


class CallPut:
    Call = "C"
    Put = "P"


class Instrument:
    __slots__ = (
        'inst_id',
        'name',
        'type',
        'symbol',
        'exch_id',
        'ccy_id',
        'alt_symbol',
        'alt_exch_id',

        'sector',
        'group',

        ## option / derivatives
        'und_inst_id',
        'expiry_date',
        'factor',
        'strike',
        'put_call',
        'margin'

    )

    def __init__(self, inst_id, name, type, symbol, exch_id, ccy_id, alt_symbol=None, alt_exch_id=None,
                 sector=None, group=None,
                 put_call=None, expiry_date=None, und_inst_id=None, factor=1, strike=0.0, margin=0.0):
        self.inst_id = int(inst_id)
        self.name = name
        self.type = type
        self.symbol = symbol
        self.exch_id = exch_id
        self.ccy_id = ccy_id
        self.alt_symbol = alt_symbol if alt_symbol else {}
        self.alt_exch_id = alt_exch_id if alt_exch_id else {}

        self.sector = sector
        self.group = group
        self.put_call = put_call
        self.expiry_date = expiry_date
        self.und_inst_id = und_inst_id

        self.factor = float(factor) if factor else 1
        self.strike = float(strike) if strike else 0.0
        self.margin = float(margin) if margin else 0.0

    def __str__(self):
        return "Instrument(inst_id = %s, name = %s, type = %s, symbol = %s, exch_id = %s, ccy_id = %s)" \
               % (self.inst_id, self.name, self.type, self.symbol, self.exch_id, self.ccy_id)

    def id(self):
        return self.symbol + "@" + self.exch_id


class Exchange:
    __slots__ = (
        'exch_id',
        'name'
    )

    def __init__(self, exch_id, name):
        self.exch_id = exch_id
        self.name = name

    def __str__(self):
        return "Exchange(exch_id = %s, name = %s)" \
               % (self.exch_id, self.name)


class Currency:
    __slots__ = (
        'ccy_id',
        'name'
    )

    def __init__(self, ccy_id, name):
        self.ccy_id = ccy_id
        self.name = name

    def __str__(self):
        return "Currency(ccy_id = %s, name = %s)" \
               % (self.ccy_id, self.name)


class RefDataManager(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def start(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_inst(self, inst):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_ccy(self, ccy):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_exch(self, exch):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_inst(self, inst_id):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_inst_by_symbol(self, symbol, exch_id):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_ccy(self, ccy_id):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_exch(self, exch_id):
        raise NotImplementedError()


class InMemoryRefDataManager(RefDataManager):
    def __init__(self):
        self.inst_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instrument.csv'))
        self.ccy_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ccy.csv'))
        self.exch_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'exch.csv'))

        self.__inst_dict = {}
        self.__inst_symbol_dict = {}
        self.__ccy_dict = {}
        self.__exch_dict = {}

        self.start()

    def start(self):
        with open(self.inst_file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                alt_symbol = {}
                if row['alt_symbol']:
                    for item in row['alt_symbol'].split(";"):
                        kv = item.split("=")
                        alt_symbol[kv[0]] = kv[1]

                alt_exch_id = {}
                if row['alt_exch_id']:
                    print row['alt_exch_id']
                    for item in row['alt_exch_id'].split(";"):
                        kv = item.split("=")
                        alt_exch_id[kv[0]] = kv[1]

                inst = Instrument(inst_id=row['inst_id'], name=row['name'], type=row['type'], symbol=row['symbol'],
                                  exch_id=row['exch_id'], ccy_id=row['ccy_id'], alt_symbol=alt_symbol,
                                  alt_exch_id=alt_exch_id, sector=row['sector'], group=row['group'],
                                  put_call=row['put_call'], expiry_date=row['expiry_date'],
                                  und_inst_id=row['und_inst_id'],
                                  factor=row['factor'], strike=row['strike'], margin=row['margin'])
                self.add_inst(inst)

        with open(self.ccy_file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ccy = Currency(ccy_id=row['ccy_id'], name=row['name'])
                self.add_ccy(ccy)

        with open(self.exch_file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                exch = Exchange(exch_id=row['exch_id'], name=row['name'])
                self.add_exch(exch)

    def stop(self):
        # TODO save to csv
        pass

    def add_inst(self, inst):
        if inst.inst_id in self.__inst_dict:
            raise RuntimeError("duplicate inst, inst_id=%s" % inst.inst_id)

        if inst.id() in self.__inst_symbol_dict:
            raise RuntimeError("duplicate inst, id=%s" % inst.id())

        self.__inst_dict[inst.inst_id] = inst
        self.__inst_symbol_dict[inst.id()] = inst

    def add_ccy(self, ccy):
        if ccy.ccy_id in self.__ccy_dict:
            raise RuntimeError("duplicate ccy, ccy_id %s" % ccy.ccy_id)

        self.__ccy_dict[ccy.ccy_id] = ccy

    def add_exch(self, exch):
        if exch.exch_id in self.__exch_dict:
            raise RuntimeError("duplicate exch, exch_id %s" % exch.exch_id)

        self.__exch_dict[exch.exch_id] = exch

    def get_inst(self, inst_id):
        return self.__inst_dict.get(inst_id, None)

    def get_inst_by_symbol(self, symbol, exch_id):
        return self.__inst_symbol_dict.get('%s@%s' % (symbol, exch_id), None)

    def get_ccy(self, ccy_id):
        return self.__ccy_dict.get(ccy_id, None)

    def get_exch(self, exch_id):
        return self.__exch_dict.get(exch_id, None)


if __name__ == "__main__":
    mgr = InMemoryRefDataManager();
    print mgr.get_inst_by_symbol('EURUSD', 'IDEALPRO')
    print mgr.get_inst(2)


