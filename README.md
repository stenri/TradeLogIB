# TradeLogIB
Python script to dumps trades from IB TWS via API into a .csv file which can then be imported into OptionNET Explorer.

TradeLogIB python script dumps a list of trades from Interactive Brokers using TWS API interface and stores them into a .csv file. This allows one to import trades into ONE software in "realtime", i.e. there is no need to wait till the end of the trading session e.t.c. It makes the overall trading process much more convenient and pleasurable, and almost eliminates the lack of proper broker integration in OptionNET software.

## Motivation:
As you may know, OptionNET Explorer lacks proper broker integration: it can only send orders to the broker but after the order is sent, it lives its own life. ONE does not know when and if the order is filled, at what price, how much commissions are paid and so on. It is assumes user manually downloads trades from the broker and uses Import Wizard to import trades, or just enters trades and commissions manually into Trade Log.

In case of Interactive Brokers user is only able to export broker activity statements after the session is over. So after you place an order and receive a fill you have to wait till the end of the session for activity statements or save the trade into Trade Log and manually enter commissions (this process is very error-prone). 

All this makes trading process much less convenient than it should be. And we need a solution to import trades from a broker Trade Log into ONE without much effort. Here it is: TradeLogIB.py.

## How it works:

* After order is filled in IB, run TradeLogIB.py script, it generates an output file TradeLogIB.csv with a list of trades in OptionXpress format.
![tradelog_csv thumb png 0bf7ee9bf90fc9696e9d4b7bc0001e07](https://user-images.githubusercontent.com/2657778/34121901-ad5354b0-e43b-11e7-8d3d-549214b63a1b.png)

* Then open Import wizard in ONE and import the required trades. ONE allows to import only selected trades you want, add trades to an existing trade, e.t.c.
![one_importwizard png d89f485993f324f9b4d771c52eff6542](https://user-images.githubusercontent.com/2657778/34121983-ed94da3a-e43b-11e7-8c78-dacf8542afe4.png)

That's all! No need to manually enter commissions, wait till the end of session, or login to Interactive Brokers Account Management.

## Configuration
Script requires one-time configuration before use:
* Install some Python environment. I recommend to use Anaconda, and I use Python 2.7: https://www.anaconda.com/download/
* Install IB API: https://www.interactivebrokers.com/en/index.php?f=5041 (needed for IbPy and TradeLogIB.py to work);
* Unpack TradeLogIB.zip somewhere on the hard-drive;
* TradeLogIB.py uses IbPy package: https://github.com/blampe/IbPy  I included IbPy in TradeLogIB repository in ib folder. But in case TradeLogIB.py complains on ib.opt, ib.exp packages missing, just install IbPy into your python environment;
* Configure IB TWS to enable Socket API's, set Socket Port to some value (this should match Python script configuration), set Master API client ID (should also be the same in the script configuration). Below is example of TWS configuration:

![tws_configuration](https://user-images.githubusercontent.com/2657778/34122189-9e909d56-e43c-11e7-9e9f-36d89e92d8de.png)

* Check that TradeLogIB.py python script configuration matches the settings made on previous steps, modify the script accordingly (or just pass appropriate options via command line using --host, --port, --clientId settings):

![script_config](https://user-images.githubusercontent.com/2657778/34122353-3f10fb72-e43d-11e7-840c-a3e1a4294f63.png)

* Also it may be a good idea to go to Mosaic / TradeLog and set "Show trades for: Last 7 days" in TWS. That somehow affects a number of trades TWS reports via API as well as in GUI interface.

![tws_tradelog_config](https://user-images.githubusercontent.com/2657778/34122403-6bd725d2-e43d-11e7-86cc-3ffdc8bf5fa2.png)

* In case your system locale is set to something other than United States there is one more critical step. Please go to Control Panel / Region and Language / Additional Settings / Time, and check that "AM" and "PM" modifiers are set (even if your time format is 24-hour based and does not require AM/PM - ONE needs this to be set in order to properly import OptionExpress account statement file. So, your time configuration should look like this:

![regionalsettings_datetime_format_config png 98fea5ca3d633a17d23c75d1d5442875](https://user-images.githubusercontent.com/2657778/34122480-9ef98ff4-e43d-11e7-98a5-11a5f27a2dd5.png)

That's all.

## Some final notes

* Initially I wanted to use TOS file format as an intermediate file to export/import trades. But when I contacted ONE support and asked them to TOS file format sample file, they said they do not have samples of TOS files other than customers sent them. And they can not share these. But they provided me with OptionXpress file sample, so I decided to use OptionXpress format.

* The script is tested with the latest beta version of ONE software: 1.28.5 beta. It is entirely possible current ONE release version will not be able the OptionXpress trades file produced by the script, since ONE support mentioned to me that OptionXpress changed file format recently. Please, contact ONE support and ask them to provide you with latest beta version in case you want to test my script (by the way, ONE beta is great, in contains some hot-keys to simplify the navigation process between expirations).

* UPD: As of ONE 1.28.6BETA locale specific bug has been fixed. ONE now seems to always expect date and time in US locale format. However ONE still wants AM/PM to be set in Regional Settings in Control Panel. 
old text: The hardest part was to force ONE Import wizard to import the trades produced by the script. ONE has a bug: it expects Date to be in the locale specific format, the same as in system Regional and Language settings, but always wants Time to be in 12-hour based format with AM/PM modifiers. Moreover, import does not work when AM/PM symbols are not set in Regional Settings. I contacted ONE support and asked them to fix this bug, but their response was as usual in such cases - it does work somehow, there is a workaround, so "setting AM/PM symbols does not hurt, even on systems with 24-hour time format". And they closed the ticket. So in case Import process fails, the first thing to check: set your date/time Region and Language to United States, restart ONE, rerun TradeLogIB.py script. And try to import file again. Ensure import process works. Then you may try to restore your locate to the one you usually use. And just set AM/PM modifiers as outlines in configuration steps above.

* Interactive Brokers API only reports all trades (from all API clients and TWS GUI) to an API client with "master client id". That's why you need to configure TWS and set master client id to be the same both in TWS GUI and in TradeLogIB.py. Otherwise the script will not be able to receive any trades, since my script does not make any trades itself, and all API clients except master client receive only their own trades from TWS API.
 
## No guarantees
**And the last note. The script is provided AS IS. I may not be able to fully support it, answer all questions, investigate and research any problems you may encounter. Also I expect Option Express format to be changed some time in the future, and I may not be around to quickly modify TradeLogIB.py to work with the latest format. So, use the script at your own risk.**
 
**That being said, I made my best to ensure the script works and is stable enough for use in production environment. I myself enjoy using TradeLogIB.py for around a month. It made my trading process using ONE and IB very simple. You may post your questions and comments related to my script in this post. I'll try to answer them whenever I have time.**

Good luck with your trading!
