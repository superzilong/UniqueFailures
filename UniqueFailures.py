import os, fnmatch, re, sys, getopt, urllib.request,time
from bs4 import BeautifulSoup as BS

def main():
    # Get test case types needed to be parsed.
    # Get input code line directory.
    # Get output directory.
    opts, args = getopt.getopt(sys.argv[1:],"ht:i:o:")
    cwd = os.getcwd()
    codelineDir = cwd
    outputDir = cwd
    for opt, arg in opts:
        if opt =="-t":
            types = arg.split(',')
            print(types)
        elif opt == "-i":
            codelineDir = arg
        elif opt == "-o":
            outputDir = arg
        elif opt == "-h":
            print("###################################################################################################")
            print("USAGE: python UniqueFailures.py -t casetypes [-i opt] [-o opt]")
            print("")
            print("OPTIONS:")
            print("    -t casetypes:   for now just support lrt and bbt, use comma separated.")
            print("    -i codelineDir: optional, codeline root directory, for example, your DEV_D1 directory, default value is current working dir.")
            print("    -o outputDir:   optional, the unique failures output directory, default value is current working dir, file name will be UniqueFailures_XXX.txt.")
            print("###################################################################################################")
            return

    # Get the report path.
    reportFilePath =codelineDir + r'_output\scons\debug\reports'
    # Begin to parse report files.
    for casetype in types:
        parse(reportFilePath, casetype, outputDir)

def parse(reportFilePath, caseType, outputDir):
    # Change work dir to result file foler.
    resultFilePath = os.path.join(reportFilePath, caseType)
    os.chdir(resultFilePath)
    # Get last-modified result file folder.
    all_subdirs = [d for d in os.listdir('.') if os.path.isdir(d)]
    latest_subdir = max(all_subdirs, key=os.path.getmtime)
    print('### Result file folder:' + latest_subdir)

    # If latest rerun folder exits, get .csv file from rerun folder. Otherwise, get .csv file from result folder.
    os.chdir(latest_subdir)
    all_sub_rerundirs = [d for d in os.listdir('.') if os.path.isdir(d)]
    if all_sub_rerundirs:
        latest_rerundir = max(all_sub_rerundirs, key=os.path.getmtime)
        print("### CSV folder:" + latest_rerundir)
        # todo: use regular expression justify rerun folder name.
        os.chdir(latest_rerundir)

    listOfFiles = os.listdir('.')
    pattern = "*.csv"
    csvFileName = ""
    for entry in listOfFiles:
        if fnmatch.fnmatch(entry, pattern):
                csvFileName = entry
                print("### CSV file: " + entry)
                break
    
    # Parse csv file name to get code line and cl number.
    re1 = re.compile(r'MAIN')
    re2 = re.compile(r'DEV_D[1-9]_PROJ_[A-Z]')
    re3 = re.compile(r'DEV_D[1-9]')
    res1 = re1.findall(csvFileName)
    res2 = re2.findall(csvFileName)
    res3 = re3.findall(csvFileName)
    codeline = ""
    if res1:
        codeline = res1[0]
    elif res2:
        codeline = res2[0]
    elif res3:
        codeline = res3[0]
    print("### Codeline is: "+codeline)

    CLNum = ""
    reCLNum = re.compile(r'CL[0-9]+')
    resCLNum = reCLNum.findall(csvFileName)
    if resCLNum:
        CLNum = resCLNum[0]
    CLNum = CLNum[2:]
    print("### CL Number is: "+CLNum)

    # Parse csv file to get fail, error and inclusive cases.
    resFile = open(csvFileName, 'r')
    lines = resFile.readlines()
    if len(lines) <= 1:
        print('### Empty result csv file.')
        return
    idxTestFile = 0
    idxTestMethod = 0
    idxStatus = 0
    failcount = 0
    localtime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    with open(os.path.join(outputDir, 'UniqueFailures_{}_{}.txt'.format(caseType, localtime)), 'w+') as uniqueFailFile, open(os.path.join(outputDir, 'ReportFailures_{}_{}.csv'.format(caseType, localtime)), 'w+') as reportFailFile:
        for i, line in enumerate(lines):
            line = line.strip()
            elems = line.split(',')
            if i == 0:
                if caseType=='lrt':
                    idxTestFile = elems.index('TestFile')
                    idxTestMethod = elems.index('TestMethod')
                    idxStatus = elems.index('Status')
                elif caseType=='bbt':
                    idxTestFile = -1
                    idxTestMethod = elems.index('name')
                    idxStatus = elems.index('result')
                reportFailFile.write(r'TestMethod,LocalStatus,QCRTStatus,Link'+'\n')
            else:
                bFoundInQCRT = False
                bFailedInQCRT = False
                status = elems[idxStatus]
                if status.lower() in ['fail', 'error', 'inconclusive']:
                    failcount += 1
                    #print(elems[idxTestFile]+elems[idxTestMethod])
                    testFile = ''
                    testM = ''
                    testPath = ''
                    outputTestM = ''
                    if caseType=='lrt':
                        testFile = elems[idxTestFile]
                        testFileT = testFile.replace("\\", r"$")
                        testM = elems[idxTestMethod]
                        testPath = r"{}%20@%@{}%*%".format(testFileT, testM)
                        outputTestM = testFile+r' <'+testM+r'>'
                    elif caseType=='bbt':
                        testFile = ''
                        testM = elems[idxTestMethod] 
                        testPath = testM
                        outputTestM = testM

                    url = r"http://qcrt.mscsoftware.com/TestResult/SearchTestResult.aspx?IsQueryString=True&TestType=%27{}%27&CodeLine={}&ChangeList={}&TestMethod={}&OS=Windows&#QueryString".format(caseType.upper(), codeline, CLNum, testPath)
                    print(url)
                    html = urllib.request.urlopen(url, None, 30).read().decode('utf-8')
                    #print(html)
                    soup = BS(html, features='lxml')
                    table = soup.find("table", {"id": "MainContent_GridViewTestResult"})
                    if table:
                        trSeq = table.find_all("tr")
                        if len(trSeq) == 2:
                            tdSeq = trSeq[1].find_all("td")
                            reportFailFile.write(outputTestM+','+status+','+tdSeq[5].text+','+url+'\n')
                            bFoundInQCRT = True
                            if tdSeq[5].text.lower() in ['fail', 'error', 'inconclusive']:
                                bFailedInQCRT = True
                                # print(url)
                    if not bFoundInQCRT:
                        reportFailFile.write(outputTestM+','+status+'\n')
                    if not bFailedInQCRT:
                        uniqueFailFile.write(outputTestM +'\n')
    print('### Congratulations! Execute successfully!')
if __name__ == "__main__":
    main()






