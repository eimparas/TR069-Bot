import paramiko, re, hashlib, requests, config
from bs4 import BeautifulSoup

class Router():

    def __init__(self):
        self.attainableUP = 0
        self.attainableDOWN = 0
        self.syncUP = 0
        self.syncDOWN = 0
        self.snrUP = 0
        self.snrDOWN = 0
        self.attenuationUP = 0
        self.attenuationDOWN = 0
        self.powerUP = 0
        self.powerDOWN = 0
        self.stats = [[0,0],[0,0]] #[[FECDOWN,FECUP], [CRCDOWN, CRCUP]]
        self.lastDayStats = [[0,0],[0,0]] #FEC, CRC of previous day
        self.isOnline = True
    
    def fetchNums(self,string, integer):
        if integer:
            outlist = [int(s) for s in re.findall("\d+",string)]
        else:
            outlist = [float(s) for s in re.findall("[+-]?[0-9]+\.[0-9]+",string)]
        return outlist
    
    def connect(self):
        pass
    
    def disconnect(self):
        pass
    
    def updateStats(self):
        raise NotImplementedError
    
    def showStats(self):
        print(self.stats)
        print("ATTAINABLE UP %d ATTAINABLE DOWN %d" %(self.attainableUP, self.attainableDOWN))
        print("SYNC UP: %d SYNC DOWN %d" % (self.syncUP, self.syncDOWN))
        print("SNRS %f %f\nATT %f %f\nPOWER %f %f" % (self.snrUP, self.snrDOWN, self.attenuationUP, self.attenuationDOWN, self.powerUP, self.powerDOWN))
    
    

class TechnicolorRouter(Router):
    def __init__(self, HOST, USERNAME, PASSWORD):
        super().__init__()
        self.HOST = HOST
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
    
    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.HOST,username=self.USERNAME, password=self.PASSWORD)
    
    def disconnect(self):
        if self.client is not None:
            self.client.close()
    
    def updateStats(self):
        if self.client is not None:
            stdin, stdout, stderr = self.client.exec_command("xdslctl info --stats")
            lines = stdout.readlines()
            for i in range(len(lines)):
                #print(lines[i])
                if lines[i].startswith("Status"):
                    print("STATUS OUT: %s" % lines[i].strip())
                    words = re.findall("\S+", lines[i])
                    if words[1] == "Showtime":
                        self.isOnline = True
                    else:
                        self.isOnline = False
                        
                if lines[i].startswith("Total time"):
                    FEC = self.fetchNums(lines[i+1].strip(), True)
                    CRC = self.fetchNums(lines[i+2].strip(), True)         
                    self.stats[0] = FEC
                    self.stats[1] = CRC
                
                if lines[i].startswith("Previous 1 day time"):
                    FEC = self.fetchNums(lines[i+1].strip(), True)
                    CRC = self.fetchNums(lines[i+2].strip(), True)         
                    self.lastDayStats[0] = FEC
                    self.lastDayStats[1] = CRC

                if lines[i].startswith("Max"):
                    attainables = self.fetchNums(lines[i].strip(), True)
                    self.attainableUP = attainables[0]
                    self.attainableDOWN = attainables[1]
                    syncs = self.fetchNums(lines[i+1].strip(), True)
                    self.syncUP = syncs[1]
                    self.syncDOWN = syncs[2]
                
                if lines[i].startswith("SNR"):
                    SNRs = self.fetchNums(lines[i].strip(), False)
                    att = self.fetchNums(lines[i+1].strip(), False)
                    powers = self.fetchNums(lines[i+2], False)
                    self.snrDOWN, self.snrUP = SNRs
                    self.attenuationDOWN, self.attenuationUP = att
                    self.powerDOWN, self.powerUP = powers

    def reboot(self):
        if self.client is not None:
            self.client.exec_command("reboot")
    
    def showStats(self):
        super().showStats() 
        print("Last day [FEC, CRC]: ",self.lastDayStats)

class ZTERouter(Router):
    def __init__(self, HOST, USERNAME, PASSWORD):
        super().__init__()
        self.IPAddress = ""
        self.HOST = HOST
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD

    def parseData(self, source):
        #print("--------------------------------------------------------------------------------------------------------")
        #soup = BeautifulSoup(source, "lxml")
        labels = source.find_all("paraname")
        values = source.find_all("paravalue")
        #This implementation is bad, I know
        for i in range(len(labels)):
            #print(labels[i].text, values[i].text)
            label = labels[i].text
            if label == "IPAddress":
                self.IPAddress = values[i].text
                continue

            if label == "Fec_errors":
                self.stats[0][0] = int(values[i].text)
                continue

            if label == "Atuc_fec_errors":
                self.stats[0][1] = int(values[i].text)
                continue

            if label == "Upstream_max_rate":
                self.attainableUP = int(values[i].text)
                continue

            if label == "Downstream_max_rate":
                self.attainableDOWN = int(values[i].text)
                continue

            if label == "Upstream_current_rate":
                self.syncUP = int(values[i].text)
                continue

            if label == "Downstream_current_rate":
                self.syncDOWN = int(values[i].text)
                continue

            if label == "UpCrc_errors":
                self.stats[1][1] = int(values[i].text)
                continue

            if label == "DownCrc_errors":
                self.stats[1][0] = int(values[i].text)
                continue

            if label == "Upstream_attenuation":
                self.attenuationUP = float(values[i].text)/10
                continue

            if label == "Downstream_attenuation":
                self.attenuationDOWN = float(values[i].text)/10
                continue

            if label == "Upstream_power":
                self.powerUP = float(values[i].text)/10
                continue

            if label == "Downstream_power":
                self.powerDOWN = float(values[i].text)/10
                continue

            if label == "Upstream_noise_margin":
                self.snrUP = float(values[i].text)/10
                continue
            
            if label == "Downstream_noise_margin":
                self.snrDOWN = float(values[i].text)/10
                continue
    
    def updateStats(self):
        h = hashlib.new("sha256")
        session = requests.Session()
        session.get("http://{}".format(self.HOST))
        randomnumber = session.get("http://{}/function_module/login_module/login_page/logintoken_lua.lua".format(self.HOST))
        soup = BeautifulSoup(randomnumber.content, "lxml")
        passnumber = soup.find("ajax_response_xml_root").text
        #print(randomnumber.content)
        h.update((("{}"+passnumber).format(self.PASSWORD)).encode())
        password = h.hexdigest()
        #print(password)
        payload={"Username":self.USERNAME, "Password":password, "action":"login"}
        r = session.post("http://{}".format(self.HOST), data=payload, allow_redirects=False)
        r = session.get("http://{}".format(self.HOST))
        print(r.status_code)
        session.get("http://{}/getpage.lua?pid=1002&nextpage=Internet_AdminInternetStatus_DSL_t.lp".format(self.HOST))
        dataXML = session.get("http://{}/common_page/internet_dsl_interface_lua.lua".format(self.HOST))
        internetSoup = BeautifulSoup(dataXML.content, "lxml")
        self.parseData(internetSoup.find("instance"))
        dataXML = session.get("http://{}/common_page/Internet_Internet_lua.lua?TypeUplink=1&pageType=1".format(self.HOST))
        IPSoup = BeautifulSoup(dataXML.content, "lxml")
        self.parseData(IPSoup.find_all("instance")[4])
        payload = {"IF_LogOff":1, "IF_LanguageSwitch":""} #log out
        session.post("http://{}".format(self.HOST), headers={"Connection":"close"}, data=payload)
        session.close()
    
    def showStats(self):
        super().showStats()
        print("IP ADDRESS: ", self.IPAddress)

def getRouter():
    router = None
    brand = config.ROUTER_BRAND.lower()
    if brand.__contains__("zte"):
        router = ZTERouter(config.HOST, config.USERNAME, config.PASSWORD)
    elif brand.__contains__("technicolor"):
        router = TechnicolorRouter(config.HOST, config.USERNAME, config.PASSWORD)
    return router
