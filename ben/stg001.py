"""
Project: Inv_7578
Date:   2019-03-31
Author: Ben
Contact: Ben910128@Gmail.com
Site: http://www.semitrade.org

# todo1: Strategy 001
Long only, if the close is lower than last 5 bars buy, once in trade if the close is higher than last 5 bars sell.
1. try changing the 5 days variable
2. doing different exit rules

"""

import os

import pandas as pd
import backtrader as bt
import backtrader.feeds as feed
from backtrader import TimeFrame
from backtrader.analyzers import (SQN,  Transactions, AnnualReturn, DrawDown, PyFolio,
                                  Returns, SharpeRatio,TradeAnalyzer,TimeReturn)


# global parameters
CASH = 100000
COMMISSION = 5/10000



# part 1: define backtrader data feed using PandasDataFeed
class newPandasData(feed.PandasData):
    '''
    The ``dataname`` parameter inherited from ``feed.DataBase`` is the pandas
    DataFrame
    '''
    params = (
              # Possible values for datetime (must always be present)
              #  None : datetime is the "index" in the Pandas Dataframe
              #  -1 : autodetect position or case-wise equal name
              #  >= 0 : numeric index to the colum in the pandas dataframe
              #  string : column name (as index) in the pandas dataframe
              ('datetime', None),

              # Possible values below:
              #  None : column not present
              #  -1 : autodetect position or case-wise equal name
              #  >= 0 : numeric index to the colum in the pandas dataframe
              #  string : column name (as index) in the pandas dataframe
              ('open', 0),
              ('high', 2),
              ('low', 3),
              ('close', 1),
              ('volume', 4),
              ('openinterest', None),
              )


def flatten_ana(analyzers, col_lab=None):
    ta_dict = {}
    out_dict = {}
    for k,v in analyzers.items():
        if isinstance(v, bt.utils.autodict.AutoOrderedDict):
            for kk, vv in v.items():
                if isinstance(vv, bt.utils.autodict.AutoOrderedDict):
                    for kkk, vvv in vv.items():
                        if isinstance(vvv, bt.utils.autodict.AutoOrderedDict):
                            for k4, v4 in vvv.items():
                                if isinstance(v4, bt.utils.autodict.AutoOrderedDict):
                                    for k5, v5 in v4.items():
                                        ta_dict["{}_{}_{}_{}_{}".format(k,kk,kkk,k4,k5)]=v5
                                else:
                                    ta_dict["{}_{}_{}_{}".format(k,kk,kkk,k4)]=v4
                        else:
                            ta_dict["{}_{}_{}".format(k,kk,kkk)]=vvv
                else:
                    ta_dict["{}_{}".format(k,kk)]=vv
        else:
            ta_dict[k]=v
    if col_lab is not None:
        for k,v in ta_dict.items():
            out_dict["{}_{}".format(col_lab, k)] = v
    else:
        out_dict = ta_dict
    return out_dict

def get_data(code):
    """
    证券代码	交易日期	日开盘价	日最高价	日最低价	日收盘价	日个股交易股数
    日个股交易金额	日个股流通市值	日个股总市值	考虑现金红利再投资的日个股回报率	不考虑现金红利的日个股回报率	考虑现金红利再投资的收盘价的可比价格
    不考虑现金红利的收盘价的可比价格	市场类型	最新股本变动日期	交易状态
    没有单位	没有单位	元/股	元/股	元/股	元/股	股	元	千元	千元	没有单位	没有单位	元/股	元/股	没有单位	没有单位	没有单位
    """
    data_path = '/Users/ben/Work/local_database/stock/{}.csv'.format(code)

    if not os.path.exists(data_path):
        data1 = pd.read_csv('/Users/ben/Work/local_database/CSMAR/0-股票市场交易/TRD_Dalyr.txt', sep="\t",
                           dtype={'Stkcd':str},
                           usecols=['Stkcd', 'Trddt', 'Opnprc','Loprc','Hiprc','Clsprc','Dnshrtrd'], encoding='utf-16-le', skiprows=[1,2])
        data2 = pd.read_csv('/Users/ben/Work/local_database/CSMAR/0-股票市场交易/TRD_Dalyr_19.txt', sep="\t",
                           dtype={'Stkcd':str},
                           usecols=['Stkcd', 'Trddt', 'Opnprc','Loprc','Hiprc','Clsprc','Dnshrtrd'], encoding='utf-16-le')
        data = data1.append(data2)
        data.columns = ['code', 'date','open','high','low','close','volume']
        data_tmp = data[['code','date', 'open', 'close','high','low','volume']]
        data_tmp.index = data_tmp.date
        df2 = data_tmp[data_tmp.code == code]
        df3 = df2.drop(['code', 'date'], axis=1)
        df3.to_csv(data_path)
    else:
        pass


# part 2: develop strategy
class stg001(bt.Strategy):
    params = (
        ('long_window_size', 5),
        ('exit_window_size', 5),
        ('stop_loss_percent', 0.02),
        ('take_profit_percent', 0.1),
        ('print_log', False),
        ('name', 'stg001')
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.p.print_log or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Strategy desc
        self.name = self.p.name
        self.desc = "Long only, Buy if the close is lower than last {}-bars, " \
                    "Sell once in trade if the close is higher than last {}-bars.\n" \
                    "Stop loss if decrease {:.0f}%, Take profit if increase {:.0f}% ".format(
            self.p.long_window_size,
            self.p.exit_window_size,
            self.p.stop_loss_percent*100,
            self.p.take_profit_percent*100)
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)
            self.price_executed = order.executed.price
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            if len(self.dataclose) > self.p.long_window_size and (
                    min(self.dataclose.get(size=self.p.long_window_size)) == self.dataclose[0]):
                # current close less than previous close
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()
        else:
            # Already in the market ... we might sell # Stop Loss at Specific Percent Order
            if (len(self.dataclose) > self.p.exit_window_size and (max(self.dataclose.get(size=self.p.exit_window_size)) == self.dataclose[0])
                ) or self.dataclose[0] <= (self.price_executed * (1-self.p.stop_loss_percent)
                ) or self.dataclose[0] >= (self.price_executed * (1+self.p.take_profit_percent)):

                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


class MonthlyReturn(TimeReturn):
    params = (
        ('timeframe', TimeFrame.Months),
    )


def cerebro_run(stg, code, df_feed_in, start_date, long_sz, exit_sz, take_size, slp, tpp, logging=True):
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Analyzer
    cerebro.addanalyzer(SQN, _name="sqn")
    cerebro.addanalyzer(SharpeRatio, legacyannual=True, _name="sr")
    cerebro.addanalyzer(TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(AnnualReturn, _name="ar")
    cerebro.addanalyzer(Returns, _name="rs")
    cerebro.addanalyzer(MonthlyReturn, _name="mr")
    cerebro.addanalyzer(DrawDown, _name="dw")
    cerebro.addanalyzer(PyFolio, _name="pf")
    cerebro.addanalyzer(Transactions, _name="trans")

    # Add a strategy
    cerebro.addstrategy(stg,
                        long_window_size=long_sz,
                        exit_window_size=exit_sz,
                        stop_loss_percent=slp,
                        take_profit_percent=tpp)

    # Add the Data Feed to Cerebro
    data = newPandasData(dataname=df_feed_in)
    cerebro.adddata(data)
    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=COMMISSION)
    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=take_size)

    # Set our desired cash start
    cerebro.broker.setcash(CASH)
    # Print out the starting conditions
    broker_start_value = cerebro.broker.getvalue()
    # Run over everything
    stgs = cerebro.run()
    # Print out the final result
    #cerebro.plot(dpi=2000)

    ta_dict = flatten_ana(stgs[0].analyzers.ta.get_analysis(), col_lab='ta')
    sqn_dict = flatten_ana(stgs[0].analyzers.sqn.get_analysis(), 'sqn')
    sr_dict = flatten_ana(stgs[0].analyzers.sr.get_analysis(), 'sr')
    ar_dict = flatten_ana(stgs[0].analyzers.ar.get_analysis(), 'ar')
    dw_dict = flatten_ana(stgs[0].analyzers.dw.get_analysis(), 'dw')
    rs_dict = flatten_ana(stgs[0].analyzers.rs.get_analysis(), 'rs')
    tr_dict = flatten_ana(stgs[0].analyzers.mr.get_analysis(), 'mr')
    trans_dict = flatten_ana(stgs[0].analyzers.trans.get_analysis(), 'trans')
    # pf_dict = flatten_ana(stgs[0].analyzers.pf.get_analysis(), 'pf')

    ana = [ta_dict, sqn_dict,sr_dict,ar_dict,dw_dict,rs_dict,tr_dict,trans_dict]

    df_ana = pd.DataFrame()
    for i in range(len(ana)):
        if i == 0:
            df_ana = pd.DataFrame.from_dict({'Value':ana[i]})
        else:
            df_ana_tmp = pd.DataFrame.from_dict({'Value':ana[i]})
            df_ana = df_ana.append(df_ana_tmp)

    broker_final_value = cerebro.broker.getvalue()


    # Return Backtest result
    out_indicator = ['stg',
                     'stock_code',
                     'start_date',
                    'long_window_size',
                    'exit_window_size',
                    'size_per_trans',
                    'stop_loss_percent',
                    'take_profit_percent',
                    'return_total',
                    'boker_final',
                    'boker_start',
                    'sharp_ratio',
                    'pnl_net',
                    'pnl_gross',
                    'sqn',
                    'monthly_return',
                    'max_drawdown',
                    'max_drawdown_money',
                    'max_drawdown_length',
                    'trans_total',
                    'trans_total_win',
                    'trans_total_lost',
                    'trans_win_rate',
                    'trans_detail',]
    out_rzlt = [stg.params.name,
                code,
                start_date,
                long_sz,
                exit_sz,
                take_size,
                slp,
                tpp,
                rs_dict['rs_rtot'],
                broker_final_value,
                broker_start_value,
                sr_dict['sr_sharperatio'],
                ta_dict['ta_pnl_net_total'],
                ta_dict['ta_pnl_gross_total'],
                sqn_dict['sqn_sqn'],
                tr_dict,
                dw_dict['dw_max_drawdown'],
                dw_dict['dw_max_moneydown'],
                dw_dict['dw_max_len'],
                ta_dict['ta_total_closed'],
                ta_dict['ta_won_total'],
                ta_dict['ta_lost_total'],
                ta_dict['ta_won_total']/ta_dict['ta_total_closed'],
                trans_dict]

    out = dict(zip(out_indicator, out_rzlt))
    for k in ar_dict:
        out[k] = ar_dict[k]

    for k in tr_dict:
        out[k] = tr_dict[k]

    """SQN
        1.6 - 1.9 Below average
        2.0 - 2.4 Average
        2.5 - 2.9 Good
        3.0 - 5.0 Excellent
        5.1 - 6.9 Superb
        7.0 - Holy Grail?
    """

    if logging and out['trans_win_rate']>0.6 and out['sqn']>=1:

        # if the strategy beyond Excellent then output the details
        print("Summary of {}: \n{}".format(stgs[0].name, stgs[0].desc))
        print("------------------------------------------")
        print("Return:          {:,.2f}%({:,.0f}/{:,.0f})".format(rs_dict['rs_rtot']*100,broker_final_value,broker_start_value))
        print("Sharp Ratio:     {:,.2f}".format(sr_dict['sr_sharperatio']))
        print("PnL Net:         {:,.0f}(Gross:{:,.0f})".format(ta_dict['ta_pnl_net_total'],ta_dict['ta_pnl_gross_total']))
        print("SQN:             {:.2f}".format(sqn_dict['sqn_sqn']))
        print("Max Drawdown:    {:.2f}%".format(dw_dict['dw_max_drawdown']))
        print("Max Drawdown:    {:,.0f}￥/{}(Days)".format(dw_dict['dw_max_moneydown'],dw_dict['dw_max_len']))
        print("Trans(Win/Loss): {}({}+/{}-)".format(ta_dict['ta_total_closed'],ta_dict['ta_won_total'],ta_dict['ta_lost_total']))
        print("Annual Return:")
        for k in ar_dict:
            print("  {} : {:.2f}%".format(k.upper(), ar_dict[k]*100))

        print("Monthly Return:")
        for k in tr_dict:
            if tr_dict[k] !=0:
                print("  {} : {:.2f}%".format(k.upper()[0:10], tr_dict[k]*100))

        # print("Monthly Transactions:")
        # trans = pd.DataFrame([l.split(" ")[0] for l in list(trans_dict.keys())])
        # trans['month'] = trans[0].map(lambda x: x[:13])
        # trans_out = trans.groupby('month').count() / 2
        # for i in range(len(trans_out)):
        #     print("  {} : {}".format(trans_out.index[i].upper(), trans_out.iloc[i][0]))

    return out



if __name__ == '__main__':


    # todo: create performance detail tracking report.
    h5 = pd.read_hdf('/Users/ben/Work/local_database/CSMAR/0-股票市场交易/TRD_Dalyr.h5')


    code='300285'
    data_path = '/Users/ben/Work/local_database/stock/{}.csv'.format(code)

    df = h5[(h5.code == code)].sort_index()
    df = df.drop(['code','date'], axis=1)
    df.to_csv(data_path)

    df = pd.read_csv(data_path, header=0, index_col=0, parse_dates=True, usecols=[0, 1, 2, 3, 4, 5])
    df = df.sort_index()

    start_date = '2015-12-31'
    df_feed = df[df.index >= start_date]


    for lwz in range(1,12):
        for ewz in range(1, 12):
            print("{}/{}".format(lwz, ewz))
            out = cerebro_run(stg001, code, df_feed, start_date, lwz, ewz, 4000, 0.08, 0.08, logging=True)




    for slp in range(3,10):
        for tpp in range(5, 15):
            print("\nslp:{}%/tpp{}%".format(slp, tpp))
            out = cerebro_run(stg001, code, df_feed, start_date, 3, 2, 4000, slp/100, tpp/100, logging=True)





    # h5 = pd.read_hdf('/Users/ben/Work/local_database/CSMAR/0-股票市场交易/TRD_Dalyr.h5')
    #
    # code_list = h5[(h5.close >= 20) & (h5.close <= 50)].code.unique().tolist()
    # e_df = pd.read_csv("draft", sep = "\n", header=None)
    # e_df['ind'] = e_df[0].map(lambda x: 1 if 'code' in x else 0)
    # e_df2 = e_df[e_df.ind == 1]
    # codes = e_df2[0].map(lambda x: x[6:12])
    # code_e = codes.values.tolist()
    #
    #
    # for code in list(set(code_list)-set(code_e)):
    #
    #     data_path = '/Users/ben/Work/local_database/stock/{}.csv'.format(code)
    #
    #
    #     df2 = h5[h5.code == code]
    #     df3 = df2.drop(['code', 'date'], axis=1)
    #     df3.to_csv(data_path)
    #
    #     redownload = False
    #     start_date = '2016-01-01'
    #
    #     df = pd.read_csv(data_path, header=0, index_col=0, parse_dates=True, usecols=[0,1,2,3,4,5])
    #     df = df.sort_index()
    #     # out = cerebro_run(stg001, code, df, start_date, 4, 8, 2000, 0.03, 0.06, logging=True)
    #
    #     try:
    #         for lwz in range(1,10):
    #             for ewz in range(1, 10):
    #                 if lwz==1 and ewz==1:
    #                     print("\ncode: {} execut lwz:{} and ewz:{}\n".format(code, lwz, ewz))
    #                 out = cerebro_run(stg001, code, df, start_date, lwz, ewz, 4000, 0.06, 0.06, logging=True)
    #                 if out['return_total']>=0.2:
    #                     break
    #             if out['return_total']>=0.2:
    #                 break
    #     except:
    #         pass
