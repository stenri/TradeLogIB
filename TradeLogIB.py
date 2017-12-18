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
import logging
import optparse
import datetime
import traceback

from ib.opt import Connection, message
from ib.ext.ExecutionFilter import ExecutionFilter 
from ib.opt import ibConnection 

version = '1.02'

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
parser.add_option('', '--clientId',        help='[Master] client Id (default: 0).', default='0', action='store')
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

def ConverSymbol_IB2OX(symbol):
    matchObj = re.match('(.+)\s+(.+)', symbol)

    if not matchObj:
        return '!!!ERROR!!!'

    ticker  = matchObj.group(1).strip()
    opra_id = matchObj.group(2).strip()

    return ticker.ljust(6, '^') + opra_id 

def watcher(msg): 
    logging.debug('%s', msg)

# global dict of orderId : Execution 
EXEC_DETAILS        = {} 
COMM_DETAILS        = {}
flag_nextValidId    = False
flag_execDetailsEnd = False

def handle_execDetails(msg):
    global EXEC_DETAILS

    ### print('ID',msg.execution.m_execId,'PRICE',msg.execution.m_price)
    EXEC_DETAILS[msg.execution.m_execId] = msg 

def handle_execDetailsEnd(msg):
    global flag_execDetailsEnd
    flag_execDetailsEnd = True

def handle_commReport(msg):
    global COMM_DETAILS

    ### print('ID',msg.commissionReport.m_execId,'COMM',msg.commissionReport.m_commission)
    COMM_DETAILS[msg.commissionReport.m_execId] = msg

def handle_nextValidId(msg):
    global flag_nextValidId
    flag_nextValidId = True

def handle_error(msg):
    global con

    if msg.errorCode != 2104 and msg.errorCode != 2106:
        logging.error(msg)

    if msg.errorCode == 504:
        #
        # Handle not connected event.
        #
        try:
            con.disconnect()
            con.connect()
        except:
            print('EXCEPTION (Not connected):\n' + traceback.format_exc()) 

InitLogging()

try:    
    import locale
    #locale.setlocale(locale.LC_TIME, '')
    locale.setlocale(locale.LC_ALL, 'american')

    con = ibConnection(host=opts.host, port=opts.port, clientId=opts.clientId)
    con.register(handle_execDetails, message.execDetails)
    con.register(handle_execDetailsEnd, message.execDetailsEnd)
    con.register(handle_commReport, message.commissionReport)
    con.register(handle_nextValidId, message.nextValidId)
    con.register(handle_error, message.error)
    con.registerAll(watcher) 
    con.connect() 
    
    while not flag_nextValidId:
        time.sleep(0.1)

    if opts.daemon:
        print 'Entering deamon mode...'

    cur_reqId = 1
    trades_map = {}

    while True:
        con.reqExecutions(cur_reqId, ExecutionFilter()) 
        
        while not flag_execDetailsEnd: 
            time.sleep(0.1)
        
        has_new_data = False
        
        for execId in EXEC_DETAILS: 
            if EXEC_DETAILS[execId].contract.m_secType != 'OPT':
                continue
        
            if False:
                print '  reqId:               {}'.format(EXEC_DETAILS[execId].reqId)
                print '  m_orderId:           {}'.format(EXEC_DETAILS[execId].execution.m_orderId)
                print '  m_clientId:          {}'.format(EXEC_DETAILS[execId].execution.m_clientId)
                print '  m_execId:            {}'.format(EXEC_DETAILS[execId].execution.m_execId)
                print '  m_time:              {}'.format(EXEC_DETAILS[execId].execution.m_time)
                print '  m_acctNumber:        {}'.format(EXEC_DETAILS[execId].execution.m_acctNumber)
                print '  m_exchange:          {}'.format(EXEC_DETAILS[execId].execution.m_exchange)
                print '  m_side:              {}'.format(EXEC_DETAILS[execId].execution.m_side)
                print '  m_shares:            {}'.format(EXEC_DETAILS[execId].execution.m_shares)
                print '  m_price:             {:.6f}'.format(EXEC_DETAILS[execId].execution.m_price)
                print '  m_permId:            {}'.format(EXEC_DETAILS[execId].execution.m_permId)
                print '  m_liquidation:       {}'.format(EXEC_DETAILS[execId].execution.m_liquidation)
                print '  m_cumQty:            {}'.format(EXEC_DETAILS[execId].execution.m_cumQty)
                print '  m_avgPrice:          {:.6f}'.format(EXEC_DETAILS[execId].execution.m_avgPrice)
                print '  m_orderRef:          {}'.format(EXEC_DETAILS[execId].execution.m_orderRef)
                print '  m_evRule:            {}'.format(EXEC_DETAILS[execId].execution.m_evRule)
                print '  m_evMultiplier:      {}'.format(EXEC_DETAILS[execId].execution.m_evMultiplier)
                print
                
                if execId in COMM_DETAILS:        
                    print '  COMMISSIONS:         {}'.format(COMM_DETAILS[execId].commissionReport.m_commission)
                else:
                    print '  COMMISSIONS:         N/A'
                
                print
                
                print 'm_conId:               {}'.format(EXEC_DETAILS[execId].contract.m_conId)
                print 'm_symbol:              {}'.format(EXEC_DETAILS[execId].contract.m_symbol)
                print 'm_secType:             {}'.format(EXEC_DETAILS[execId].contract.m_secType)
                print 'm_expiry:              {}'.format(EXEC_DETAILS[execId].contract.m_expiry)
                print 'm_strike:              {}'.format(EXEC_DETAILS[execId].contract.m_strike)
                print 'm_right:               {}'.format(EXEC_DETAILS[execId].contract.m_right)
                print 'm_multiplier:          {}'.format(EXEC_DETAILS[execId].contract.m_multiplier)
                print 'm_exchange:            {}'.format(EXEC_DETAILS[execId].contract.m_exchange)
                print 'm_currency:            {}'.format(EXEC_DETAILS[execId].contract.m_currency)
                print 'm_localSymbol:         {}'.format(EXEC_DETAILS[execId].contract.m_localSymbol)
                print 'm_tradingClass:        {}'.format(EXEC_DETAILS[execId].contract.m_tradingClass)
                print 'm_primaryExch:         {}'.format(EXEC_DETAILS[execId].contract.m_primaryExch)
                print 'm_includeExpired:      {}'.format(EXEC_DETAILS[execId].contract.m_includeExpired)
                print 'm_secIdType:           {}'.format(EXEC_DETAILS[execId].contract.m_secIdType)
                print 'm_secId:               {}'.format(EXEC_DETAILS[execId].contract.m_secId)
                print 'm_comboLegsDecrip:     {}'.format(EXEC_DETAILS[execId].contract.m_comboLegsDescrip)
                print 'm_comboLegs:           {}'.format(EXEC_DETAILS[execId].contract.m_comboLegs)
                print 'm_underComp:           {}'.format(EXEC_DETAILS[execId].contract.m_underComp)
                print '-------------'
        
            dt = datetime.datetime.strptime(EXEC_DETAILS[execId].execution.m_time, '%Y%m%d %H:%M:%S')
        
            if EXEC_DETAILS[execId].execution.m_side == 'BOT':
                action = 'Buy To Open'
            elif EXEC_DETAILS[execId].execution.m_side == 'SLD':
                action = 'Sell To Open'
            else:
                logging.error('Error: unable to parse EXEC_DETAILS[execId].execution.m_side "{}".\n'.format(EXEC_DETAILS[execId].execution.m_side))
                sys.exit(1)
        
            symbol         = ConverSymbol_IB2OX(EXEC_DETAILS[execId].contract.m_localSymbol)
        
            if EXEC_DETAILS[execId].contract.m_right == 'C':
                desc           = '{} {} {} Call'.format(EXEC_DETAILS[execId].contract.m_symbol, EXEC_DETAILS[execId].contract.m_expiry, EXEC_DETAILS[execId].contract.m_strike)
            elif EXEC_DETAILS[execId].contract.m_right == 'P':
                desc           = '{} {} {} Put'.format(EXEC_DETAILS[execId].contract.m_symbol, EXEC_DETAILS[execId].contract.m_expiry, EXEC_DETAILS[execId].contract.m_strike)
            else:
                logging.error('Error: unable to parse EXEC_DETAILS[execId].contract.m_right "{}".\n'.format(EXEC_DETAILS[execId].contract.m_right))
                sys.exit(1)
        
            qty            = int(EXEC_DETAILS[execId].execution.m_shares)
        
            req_fees       = 0.0
            transaction_id = EXEC_DETAILS[execId].execution.m_permId
            order_id       = EXEC_DETAILS[execId].execution.m_orderId

            price = math.fabs(float(EXEC_DETAILS[execId].execution.m_price))
        
            if execId in COMM_DETAILS:        
                commission     = COMM_DETAILS[execId].commissionReport.m_commission
            else:
                commission     = 0.0
               
                if not opts.daemon:
                    logging.warning('Warning: skipping trade as commission detail are not available ({} {} {} {} {})'.format(symbol, desc, action, qty, price))
        
                continue       
       
            total_cost     = qty * price + commission + req_fees
        
            if EXEC_DETAILS[execId].execution.m_side == 'BOT':
                total_cost *= 1
        
            #
            # We want output to be sorted by date/time and order_id, so here we just add output line to trades_map map, and then dump output in a separate cycle.
            #
            key   = dt.strftime('%Y.%m.%d %H:%M:%S') + '{:08d}'.format(order_id) + execId
        
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
            cur_reqId += 1
            time.sleep(1)
        else:
            break

except:
    logging.error('EXCEPTION:\n' + traceback.format_exc()) 

con.disconnect()
con.close()
