# UniqueFailures.py
## Introduce:
Use this python script can get the **unique failures** from your failed cases in the report file compared to QCRT results. 
## How to use:
1. Install python 3.
2. Use `pip3` to install `BeautifulSoup` and `lxml` modules:
   `pip3 install beautifulsoup4`
   `pip3 install lxml`
3. Change current working directory to your root code line dir.
4. Use `python3 UniqueFailures.py -t lrt,bbt` to get lrt and bbt unique failures.
5. Unique failures will be listed in `UniqueFailures_lrt_XXX.txt` or `UniqueFailures_bbt_XXX.txt` .
