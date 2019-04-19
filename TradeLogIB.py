#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (c) 2017 Stanislav Vinokurov, All rights reserved.
#
import re
import sys
import math
import time
import pytz
import logging
import datetime
import optparse
import traceback

from tzlocal import get_localzone
from ib_insync import *

version = '4.00'

def InitLogging():      
    if opts.logLevel > 0:
        logging.basicConfig(level=opts.logLevel, filename='TradeLogIB.log', filemode='w+', format='%(asctime)s: %(threadName)-10s: %(message)s', )

        logging.info('-------------------------------------------------------------------------')
        logging.info('Starting...')
        logging.info('-------------------------------------------------------------------------')

    root = logging.getLogger('')
    #root.propagate = False
    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    ch.setLevel(opts.consoleLogLevel)
    root.addHandler(ch)

def AsTimeZone(dt, src_timezone, dst_timezone):
        #
        # NOTE: dt is already localized, so we do not need to call src_timezone.localize(dt) here,
        #       and we use directly dt as is.
        #
        return src_timezone.normalize(dt).astimezone(dst_timezone)

def ConverSymbol_IB2OX(symbol):
    matchObj = re.match('(.+)\s+(.+)', symbol)

    if not matchObj:
        return '!!!ERROR!!!'

    ticker  = matchObj.group(1).strip()
    opra_id = matchObj.group(2).strip()

    return ticker.ljust(6, '^') + opra_id 

class MyParser(optparse.OptionParser):
    def format_epilog(self, formatter):
        return self.epilog

parser = MyParser(
                  version     = '%prog version {}'.format(version), 
                  description = 'IB Trades Dumper.', 
                  usage       = 'usage: %prog [options] [TradeLogIB.csv]',
                  epilog      = """
Examples:

  TradeLogIB.py
  TradeLogIB.py TradeLogIB.csv

"""
                 )

parser.add_option('', '--host',            help='Host to connect to (default: 127.0.0.1).', default='127.0.0.1', action='store')
parser.add_option('', '--port',            help='Port to connect to (default: 4001).', default='4001', action='store')
parser.add_option('', '--daemon',          help='Turn on deamon mode (default: False).', default=False, action='store_true')
parser.add_option('', '--UTC',             help='Store trades in UTC timezone, i.e. do not convert time to Local Time Zone) (default: False).', default=False, action='store_true')
parser.add_option('', '--clientId',        help='Client Id (default: 0).', default='0', action='store')
parser.add_option('', '--logLevel',        help='Log level for log file output (DEBUG=10, INFO=20, WARNING=30, ERROR: 40, CRITICAL: 50, default: 0).',  default=0, action='store')
parser.add_option('', '--consoleLogLevel', help='Log level for console output  (DEBUG=10, INFO=20, WARNING=30, ERROR: 40, CRITICAL: 50, default: 20).', default=30, action='store')

(opts, args) = parser.parse_args()

opts.port            = int(opts.port)
opts.clientId        = int(opts.clientId)
opts.logLevel        = int(opts.logLevel)
opts.consoleLogLevel = int(opts.consoleLogLevel)

if len(args) > 0:
    output_file = args[0]
else:
    output_file = 'TradeLogIB.csv'

InitLogging()

try:    
    import locale
    locale.setlocale(locale.LC_ALL, 'american')

    ib = IB()
    ib.connect(host=opts.host, port=opts.port, clientId=opts.clientId)

    trades_map = {}

    if opts.daemon:
        print('Entering daemon mode...')

    src_timezone = pytz.utc
    dst_timezone = get_localzone()

    while True:
        has_new_data = False

        for fill in ib.fills():
            if fill.contract.secType != 'OPT':
                continue

            dt = fill.execution.time

            if not opts.UTC:
                dt = AsTimeZone(dt, src_timezone, dst_timezone)

            if fill.execution.side == 'BOT':
                action = 'Buy To Open'
            elif fill.execution.side == 'SLD':
                action = 'Sell To Open'
            else:
                logging.error('Error: unable to parse fill.execution.side "{}".\n'.format(fill.execution.side))
                sys.exit(1)

            symbol = ConverSymbol_IB2OX(fill.contract.localSymbol)

            if fill.contract.right == 'C':
                desc           = '{} {} {} Call'.format(fill.contract.symbol, fill.contract.lastTradeDateOrContractMonth, fill.contract.strike)
            elif fill.contract.right == 'P':
                desc           = '{} {} {} Put'.format(fill.contract.symbol, fill.contract.lastTradeDateOrContractMonth, fill.contract.strike)
            else:
                logging.error('Error: unable to parse fill.contract.right "{}".\n'.format(fill.contract.right))
                sys.exit(1)

            qty            = int(fill.execution.shares)
        
            req_fees       = 0.0
            transaction_id = fill.execution.permId
            order_id       = fill.execution.orderId

            price = math.fabs(float(fill.execution.price))

            if hasattr(fill, 'commissionReport'):
                commission = fill.commissionReport.commission
            else:
                commission = 0

                if not opts.daemon:
                    logging.warning('Warning: skipping trade as commission detail are not available ({} {} {} {} {})'.format(symbol, desc, action, qty, price))
        
                continue       

            total_cost     = qty * price + commission + req_fees
            #total_cost     = format(total_cost, '.6f')

            #
            # We want output to be sorted by date/time and order_id, so here we just add output line to trades_map map, and then dump output in a separate cycle.
            #
            key   = dt.strftime('%Y.%m.%d %H:%M:%S') + '{:08d}'.format(fill.execution.orderId) + fill.execution.execId
     
            if not key in trades_map:
                has_new_data = True
            else:
                ### print 'Warning: duplicate key ({}).'.format(key)
                pass

            #
            # Symbol, Description, Action, Quantity, Price, Commission, Reg Fees, Date, TransactionID, Order Number, Transaction Type ID, Total Cost
            #
            # SPX^^^130921P01660000,SPX Sep13 1660 Put,Buy To Open,2,3.15,2.27,0.06,09.12.2013 10:31:15 PM,111111111,222222222,34,-632.33
            #
            trades_map[key] = '{},{},{},{},{},{},{},{},{},{},34,{}\n'.format(symbol, desc, action, qty, price, commission, req_fees, dt.strftime('%x %X'), transaction_id, order_id, total_cost)

        if has_new_data:       
            with open(output_file, "w") as out:
                out.write('Symbol, Description, Action, Quantity, Price, Commission, Reg Fees, Date, TransactionID, Order Number, Transaction Type ID, Total Cost\n')
        
                for key in sorted(trades_map): 
                    out.write(trades_map[key])

            if opts.daemon:
                print('{} TradeLog updated.'.format(datetime.datetime.now().strftime('%H:%M:%S')))

        if opts.daemon:
            ib.sleep(1)
        else:
            break

except:
    logging.error('EXCEPTION:\n' + traceback.format_exc()) 

ib.disconnect()
