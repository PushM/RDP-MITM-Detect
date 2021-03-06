import argparse, sys, os, time, concurrent.futures, csv, io
import pickle
from sklearn.ensemble import RandomForestClassifier
from pandas import DataFrame, read_csv, concat

sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'probes'))
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn", lineno=484)
from RTTfeatureProbes import *
from TLSfeatureProbes import *

class Detector:

    RTTfeatureProbes = [
        tcpSYNTiming,
        x224ConnReqTiming,

    ]

    TLSfeatureProbes = [
        TLSLibrary,
        #TLSVersions,
    ]

    def __init__(self, rdp_port=3389, numIterations=3,
                modelFile="./rdpmitm_rfc.pickle", rawData=False,
                outputFile=None, outputFormat="csv"):

        self.rdp_port = rdp_port
        self.numIterations = numIterations
        self.modelFile = modelFile
        self.outputFile = outputFile
        self.outputFormat = outputFormat
        self.rawData = rawData
        self.model = pickle.load(open(self.modelFile, 'rb'))

    def crawl(self, ips):
        crawlResults = {}

        for ip in ips :
            print("probing: {}".format(ip))
            try:
                # 检测目标ip
                result = self.testSite(ip)
            except Exception as e:
                print("{} probe error".format(ip))
                print(e)
                continue
            #result = self.testSite(ip)

            crawlResults[result['ip']] = {'classification' : result['classification'],
                                            'data' : result['data']}
            if(self.outputFile == None and not self.rawData):
                if(len(ips) == 1):
                    print(result['classification'])
                    #print(result['data'])
                else:
                    print(f"{result['ip']}: {result['classification']}")

        output = self.writeResultsToFile(crawlResults)
        if(output and self.rawData):
            print(output)


    def testSite(self, ip):
        result = {'ip' : ip}
        #提取目标RDP服务端的RTT和TLS特征
        result['data'] = self.probeSite(ip)
        #特征输入分类器得到分类结果
        result['classification'] = self.classifySite(result['data'])
        return result

    def classifySite(self, recordings):
        classification = None

        recordingsDataFrame = DataFrame([recordings])
        #columnsToDrop = [column for column in recordingsDataFrame if column not in self.model.feature_names]
        #recordingsDataFrame = recordingsDataFrame.drop(columnsToDrop, axis=1)
        if(recordingsDataFrame.isna().sum().sum() > 0):
            return classification

        recordingsDataFrame = recordingsDataFrame.reindex(sorted(recordingsDataFrame.columns), axis=1)

        try:
            classification = self.model.predict(recordingsDataFrame)[0]
        except Exception as e:
            print(e)
        if classification == 0:
            result = "no rdp-mitm"
        else:
            result = "yes rdp-mitm!"
        return result

    def probeSite(self, ip):
        probeResults = {}
        #TLS特征提取
        for probe in Detector.TLSfeatureProbes:
            TLSlibResults = probe(ip, self.rdp_port).test()

        #RTT特征提取
        for probe in Detector.RTTfeatureProbes:
            currentProbeResults = probe(ip, self.rdp_port).test()
            probeResults[probe.__name__] = currentProbeResults
        #计算RTT之比
        probeResults['x224ReqTCPSynRatio'] = probeResults['x224ConnReqTiming'] / probeResults['tcpSYNTiming']

        probeResults.update(TLSlibResults)
        return probeResults

    def writeResultsToFile(self, siteResults):
        if(self.outputFile != None):
            f = open(self.outputFile, 'w')
        else:
            f = io.StringIO()

        if(self.outputFormat == 'csv'):
            resultsToFile = []

            for key,value in siteResults.items():
                currentResults = {}
                if(self.rawData):
                    currentResults.update(value['data'])
                currentResults['classification'] = value['classification']
                currentResults['site'] = key

                resultsToFile.append(currentResults)

            writer = csv.DictWriter(f, fieldnames=resultsToFile[0].keys())
            writer.writeheader()
            for row in resultsToFile:
                writer.writerow(row)
        elif(self.outputFormat == 'json'):
            for key in siteResults.keys():
                if(not self.rawData):
                    del siteResults[key]['data']

            json.dump(siteResults, f)

        if(self.outputFile == None):
            output = f.getvalue()
        else:
            output = None
        f.close()
        return output



def process_args():
    ######################################
    programDescription = "RDP_MITM_PROBER：Detect RDP MITM Attack"

    parser = argparse.ArgumentParser(description=programDescription, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ip",
                        nargs="?",
                        help="ip to classify as a RDP MITM . Not required if input file specified with -r argument.")
    parser.add_argument("-R", "--raw-data",
                        action="store_true",
                        default=False,
                        help="Record and output raw classification data about site(s).")
    parser.add_argument("-w", "--output-file",
                        type=str,
                        help="File to write probe outputs to. This argument is required if in record mode.",
                        default=None)
    parser.add_argument("-r", "--input-file",
                        type=str,
                        help="File containing  IP addresses . Each line should contain only the IP.")
    parser.add_argument("--rdp-port", type=int, default=3389,
                        help="Set the port to scan rdp servers. Defaults to 3389.")
    parser.add_argument("--output-format", help="Format to produce output if in \"Record\" mode. Options include: csv, json. Default format is csv.", default="csv")

    args = vars(parser.parse_args())

    if(args["ip"] == None and args["input_file"] == None):
        parser.print_help(sys.stderr)
        sys.exit(1)
    elif(os.geteuid() != 0):
        print("Root permissions not granted. Run program as root to enable TCP SYN/ACK timing probe.")
        sys.exit(1)
    return args

if(__name__ == '__main__'):
    args = process_args()

    if(args['input_file'] != None):
        with open(args['input_file'], "r") as f:
            ips = [ip.strip() for ip in f.readlines()]
    else:
        ips = [args["ip"]]

    detector = Detector( rawData=args['raw_data'],
                        outputFile=args['output_file'],
                        outputFormat=args['output_format'])

    detector.crawl(ips)
