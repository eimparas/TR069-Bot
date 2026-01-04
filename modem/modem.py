from sys import stderr, stdout
import paramiko, re, hashlib, requests, traceback
from bs4 import BeautifulSoup
from datetime import datetime
import json
from Exscript.protocols import Telnet
from Exscript import Account
import logging
import paramiko.util


class CustomFileHandler(logging.StreamHandler):
    def emit(self, record):
        record.msg = f"[modem.py] {record.msg}"
        super().emit(record)

# Proper Logging
paramiko.util.logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[CustomFileHandler()])

class Modem():

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
        self.crcUP = 0
        self.crcDOWN = 0
        self.fecUP = 0
        self.fecDOWN = 0
        self.isOnline = True
    
    def fetchNums(self,string, integer):
        return [float(s) for s in re.findall("[+-]?[0-9]+\.?[0-9]*",string)]
    
    def connect(self):
        pass
    
    def disconnect(self):
        pass
    
    def updateStats(self):
        raise NotImplementedError
    
    def showStats(self):
        logging.debug(f"FEC UP: {self.fecUP}, FEC DOWN: {self.fecDOWN}")
        logging.debug(f"ATTAINABLE UP: {self.attainableUP}, ATTAINABLE DOWN: {self.attainableDOWN}")
        logging.debug(f"SYNC UP: {self.syncUP}, SYNC DOWN: {self.syncDOWN}")
        logging.debug(f"SNR UP: {self.snrUP}, SNR DOWN: {self.snrDOWN}")
        logging.debug(f"ATTENUATION UP: {self.attenuationUP}, ATTENUATION DOWN: {self.attenuationDOWN}")
        logging.debug(f"POWER UP: {self.powerUP}, POWER DOWN: {self.powerDOWN}")

class TechnicolorModem(Modem):
    def __init__(self, HOST, USERNAME, PASSWORD):
        super().__init__()
        self.HOST = HOST
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.COMMANDS = {
            "dsl_status":"sys.class.xdsl.@line0.Status",
            "dsl_type":"sys.class.xdsl.@line0.ModulationType",
            "dsl_linerate_up":"sys.class.xdsl.@line0.UpstreamCurrRate",
            "dsl_linerate_down":"sys.class.xdsl.@line0.DownstreamCurrRate",
            "dsl_linerate_up_max":"sys.class.xdsl.@line0.UpstreamMaxRate",
            "dsl_linerate_down_max":"sys.class.xdsl.@line0.DownstreamMaxRate",
            "dsl_uptime":"sys.class.xdsl.@line0.ShowtimeStart",
            "dsl_power_up":"sys.class.xdsl.@line0.UpstreamPower",
            "dsl_power_down":"sys.class.xdsl.@line0.DownstreamPower",
            "dsl_attenuation_up":"sys.class.xdsl.@line0.UpstreamAttenuation",
            "dsl_attenuation_down":"sys.class.xdsl.@line0.DownstreamAttenuation",
            "dsl_margin_up":"sys.class.xdsl.@line0.UpstreamNoiseMargin",
            "dsl_margin_down":"sys.class.xdsl.@line0.DownstreamNoiseMargin",
            "dsl_fec_up":"sys.class.xdsl.@line0.UpstreamFECTotal",
            "dsl_fec_down":"sys.class.xdsl.@line0.DownstreamFECTotal",
            "dsl_crc_up":"sys.class.xdsl.@line0.UpstreamCRCTotal",
            "dsl_crc_down":"sys.class.xdsl.@line0.DownstreamCRCTotal",
        }# Transformer Commands
    
    def connect(self):
        logging.info(f"SSH CONNECTING to {self.HOST}")
        self.client = paramiko.SSHClient()
        try:
            self.client.load_host_keys("host_key.txt")
            self.client.connect(self.HOST,username=self.USERNAME, password=self.PASSWORD)
        except FileNotFoundError:
            logging.warning("Key file not found, saving current")
            with open("host_key.txt", "w") as f:
                pass
            self.client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
            self.client.connect(self.HOST,username=self.USERNAME, password=self.PASSWORD)
            self.client.save_host_keys("host_key.txt")
    
    def disconnect(self):
        if self.client is not None:
            self.client.close()

    def getStats(self, cmd):
        if self.client is not None:
            stdin, stdout, stderr = self.client.exec_command("transformer-cli get " + self.COMMANDS[cmd])
            return stdout.readline().split("=")[1].strip()

    def updateStats(self):
        if self.getStats("dsl_status") == "Up":
            self.isOnline = True
        else:
            self.isOnline = False
        try:
            self.attainableUP = self.fetchNums(self.getStats("dsl_linerate_up_max"), True)[0]
            self.attainableDOWN = self.fetchNums(self.getStats("dsl_linerate_down_max"), True)[0]
            self.syncUP = self.fetchNums(self.getStats("dsl_linerate_up"), True)[0]
            self.syncDOWN = self.fetchNums(self.getStats("dsl_linerate_down"), True)[0]
            self.snrUP = self.fetchNums(self.getStats("dsl_margin_up"), False)[0]
            self.snrDOWN = self.fetchNums(self.getStats("dsl_margin_down"), False)[0]
            self.attenuationUP = self.fetchNums(self.getStats("dsl_attenuation_up"), False)[0]
            self.attenuationDOWN = self.fetchNums(self.getStats("dsl_attenuation_down"), False)[0]
            self.powerUP = self.fetchNums(self.getStats("dsl_power_up"), False)[0]
            self.powerDOWN = self.fetchNums(self.getStats("dsl_power_down"), False)[0]
            self.crcUP = self.fetchNums(self.getStats("dsl_crc_up"), True)[0]
            self.crcDOWN = self.fetchNums(self.getStats("dsl_crc_down"), True)[0]
            self.fecUP = self.fetchNums(self.getStats("dsl_fec_up"), True)[0]
            self.fecDOWN = self.fetchNums(self.getStats("dsl_fec_down"), True)[0]
        except IndexError as i:
            logging.error(f"IndexError: {i}")
            timestr = datetime.now().strftime("%m-%d-%Y_%H.%M.%S")
            with open(timestr+".txt", "a") as file:
                file.write(traceback.format_exc()+"\n")
                logging.error("==============================DATA=================================")
                file.write("==============================DATA=================================\n")
                values = self.COMMANDS.keys()
                for value in values:
                    logging.error(f"{value}: {self.getStats(value)}")
                    file.write(value+"\t"+self.getStats(value)+"\n")
                logging.error("==============================END DATA=============================")
                file.write("==============================END DATA============================="+"\n")

    def updateLineState(self):
        if self.getStats("dsl_status") == "Up":
            self.isOnline = True
        else:
            self.isOnline = False
            
    def reboot(self):
        if self.client is not None:
            self.client.exec_command("reboot")
    
    def disconnectLine(self):
        if self.client is not None:
            self.client.exec_command("xdslctl connection --down")

    def connectLine(self):
        if self.client is not None:
            self.client.exec_command("xdslctl connection --up")

    def showStats(self):
        super().showStats() 

class ZTEModem(Modem):
    def __init__(self,HOST,USERNAME,PASSWORD):
        super().__init__()
        self.HOST = HOST
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
    
    def parseData(self, source: BeautifulSoup):
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
                self.fecDOWN = int(values[i].text)
                continue

            if label == "Atuc_fec_errors":
                self.fecUP = int(values[i].text)
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
                self.crcUP = int(values[i].text)
                continue

            if label == "DownCrc_errors":
                self.crcDOWN = int(values[i].text)
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

class ZTEh267a(ZTEModem):
    def __init__(self, HOST, USERNAME, PASSWORD):
        super().__init__(HOST,USERNAME,PASSWORD)
        self.IPAddress = ""
    
    def updateStats(self):
        h = hashlib.new("sha256")
        session = requests.Session()
        session.get("http://{}".format(self.HOST))
        randomnumber = session.get("http://{}/function_module/login_module/login_page/logintoken_lua.lua".format(self.HOST))
        soup = BeautifulSoup(randomnumber.content, "lxml")
        passnumber = soup.find("ajax_response_xml_root").text
        h.update((("{}"+passnumber).format(self.PASSWORD)).encode())
        password = h.hexdigest()
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
    
    def showStats(self):
        super().showStats()
        print("IP ADDRESS: ", self.IPAddress)

class ZTEh1600(ZTEModem):
    def __init__(self, HOST, USERNAME, PASSWORD):
        super().__init__(HOST,USERNAME,PASSWORD)
    
    def updateStats(self):
        with requests.Session() as session:
            r = session.get(f"http://{self.HOST}/?_type=loginData&_tag=login_entry").content.decode()
            sessionToken = json.loads(r)["sess_token"]
            xml = session.get(f"http://{self.HOST}/?_type=loginData&_tag=login_token&_={int(datetime.now().timestamp()*1000)}").content.decode()
            num = re.findall("\d+", xml)[0]
            #print(sessionToken, num)
            password = hashlib.sha256((self.PASSWORD+num).encode()).hexdigest()
            authorizationData = {"action":"login","Username":self.USERNAME,"Password":password, "_sessionTOKEN":sessionToken}
            response = session.post(f"http://{self.HOST}/?_type=loginData&_tag=login_entry",data=authorizationData).content.decode()
            resp = json.loads(response)
            if "loginErrMsg" in resp:
                raise Exception("Failed to log in to ZTE H1600: %s" %
                                resp["loginErrMsg"])
            elif "login_need_refresh" in resp and resp["login_need_refresh"] : 
                session.get(f"http://{self.HOST}/")
                session.get(f"http://{self.HOST}/?_type=menuView&_tag=dslWanStatus&Menu3Location=0&_={int(datetime.now().timestamp()*1000)}")
                response = session.get(f"http://{self.HOST}/?_type=menuData&_tag=dsl_interface_status_lua.lua&_={int(datetime.now().timestamp()*1000)}").content.decode()
                dataXML = BeautifulSoup(response,"lxml")
                self.parseData(dataXML.find("instance"))
                #print(session.cookies.get_dict()) #for debugging
            else:
                raise Exception(("Failed to log in to ZTE H1600, response "
                                 "was: %s") % response)

class OpenWRT(Modem):
    def __init__(self, HOST, USERNAME, PASSWORD):
        super().__init__()
        self.HOST = HOST
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.sid = "00000000000000000000000000000000"

    def _ubus_rpc(self, payload):
        url = f"http://{self.HOST}/ubus"
        try:
            r = requests.post(url, json=payload, timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logging.error(f"UBUS RPC failed: {e}")
            raise

    def connect(self):
        # No persistent connection needed for HTTP API
        pass
    
    def disconnect(self):
        # No persistent connection needed for HTTP API
        pass
    
    def _login(self):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": [
                "00000000000000000000000000000000",
                "session",
                "login",
                {"username": self.USERNAME, "password": self.PASSWORD}
            ]
        }
        data = self._ubus_rpc(payload)
        if "result" in data and len(data["result"]) > 1:
            self.sid = data["result"][1]["ubus_rpc_session"]
        else:
            raise Exception("Login failed, could not retrieve session ID")

    def updateStats(self):
        try:
            self._login()
            
            payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "call",
                "params": [
                    self.sid,
                    "dsl",
                    "metrics",
                    {}
                ]
            }
            
            resp = self._ubus_rpc(payload)
            parsed_payload = resp["result"][1]

            if parsed_payload.get('power_state') == "L0 - Synchronized":
                self.isOnline = True
                
                upstream = parsed_payload.get('upstream', {})
                downstream = parsed_payload.get('downstream', {})
                errors = parsed_payload.get('errors', {})
                errors_near = errors.get('near', {})
                errors_far = errors.get('far', {})

                self.attainableUP = upstream.get('attndr', 0) / 1000
                self.attainableDOWN = downstream.get('attndr', 0) / 1000
                self.syncUP = upstream.get('data_rate', 0) / 1000
                self.syncDOWN = downstream.get('data_rate', 0) / 1000
                self.snrUP = upstream.get('snr', 0)
                self.snrDOWN = downstream.get('snr', 0)
                self.attenuationUP = upstream.get('latn', 0)
                self.attenuationDOWN = downstream.get('latn', 0)
                self.powerUP = upstream.get('actatp', 0)
                self.powerDOWN = downstream.get('actatp', 0)
                self.crcUP = errors_far.get('crc_p', 0)
                self.crcDOWN = errors_near.get('crc_p', 0)
                self.fecUP = errors_far.get('fecs', 0)
                self.fecDOWN = errors_near.get('fecs', 0)
            else:
                self.isOnline = False

        except Exception as e:
            logging.error(f"Error updating stats: {e}")
            self.isOnline = False
            # Optional: Keep the file logging if desired, but simplified
            timestr = datetime.now().strftime("%m-%d-%Y_%H.%M.%S")
            # Minimal error logging to avoid file spam if desired, or keep original logic. 
            # Sticking to logging to stderr/log file for now as per clean up.

    def updateLineState(self):
        # Reuse updateStats logic or similar lightweight check
        self.updateStats()
            
    def reboot(self):
        raise NotImplementedError("Reboot via UBUS not implemented")
    
    def disconnectLine(self):
        raise NotImplementedError
    
    def connectLine(self):
        raise NotImplementedError

class DraytekModem(Modem):
    def __init__(self, HOST, USERNAME, PASSWORD):
        super().__init__()
        self.HOST = HOST
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.client = None
    
    def connect(self):
        logging.info(f"Telnet CONNECTING to {self.HOST}")
        self.client = Telnet()
        account = Account(self.USERNAME, self.PASSWORD)
        try:
            self.client.set_username_prompt('Account:')
            self.client.set_password_prompt('Password:')
            self.client.connect(self.HOST)
            self.client.login(account)
        except Exception as e:
            logging.error(f"Login exception: {e}")
            self.client = None
    
    def disconnect(self):
        if self.client is not None:
            self.client.send('exit\n')
            self.client.close()
            self.client = None

    def getStats(self):
        if self.client is not None:
            try:
                self.client.execute('vdsl status')
                status = self.client.response
                self.client.execute('vdsl status more')
                statusmore = self.client.response
                return status, statusmore
            except Exception as e:
                logging.error(f"CMD execution exception: {e}")
                self.disconnect()
                return None, None
        return None, None

    def updateStats(self):
        status, statusmore = self.getStats()
        if status is None or statusmore is None:
            return
        
        patterns = {
            "State": r"State\s*:\s*(\w+)",
            "DS Actual Rate": r"DS Actual Rate\s*:\s*(-?\d+\s*(?:\.\s*\d+)?)\s*bps",
            "US Actual Rate": r"US Actual Rate\s*:\s*(-?\d+\s*(?:\.\s*\d+)?)\s*bps",
            "DS Attainable Rate": r"DS Attainable Rate\s*:\s*(-?\d+\s*(?:\.\s*\d+)?)\s*bps",
            "US Attainable Rate": r"US Attainable Rate\s*:\s*(-?\d+\s*(?:\.\s*\d+)?)\s*bps",
            "NE Current Attenuation": r"NE Current Attenuation\s*:\s*(-?\d+\s*(?:\.\s*\d+)?)\s*dB",
            "Cur SNR Margin": r"Cur SNR Margin\s*:\s*(-?\d+\s*(?:\.\s*\d+)?)\s*dB",
            "Far Current Attenuation": r"Far Current Attenuation\s*:\s*(-?\d+\s*(?:\.\s*\d+)?)\s*dB",
            "Far SNR Margin": r"Far SNR Margin\s*:\s*(-?\d+\s*(?:\.\s*\d+)?)\s*dB"
        }

        for line in status.splitlines():
            for key, pattern in patterns.items():
                if match := re.search(pattern, line):
                    if key == "State":
                        self.isOnline = match.group(1) == "SHOWTIME"
                    elif key == "DS Actual Rate":
                        self.syncDOWN = int(match.group(1)) / 1000
                    elif key == "US Actual Rate":
                        self.syncUP = int(match.group(1)) / 1000
                    elif key == "DS Attainable Rate":
                        self.attainableDOWN = int(match.group(1)) / 1000
                    elif key == "US Attainable Rate":
                        self.attainableUP = int(match.group(1)) / 1000
                    elif key == "NE Current Attenuation":
                        self.attenuationDOWN = float(match.group(1))
                    elif key == "Cur SNR Margin":
                        self.snrDOWN = float(match.group(1))
                    elif key == "Far Current Attenuation":
                        self.attenuationUP = float(match.group(1))
                    elif key == "Far SNR Margin":
                        self.snrUP = float(match.group(1))

        for line in statusmore.splitlines():
            if match := re.search(r'\s+FECS\s+:\s+(\d+)\s+(\d+) \(seconds\)', line):
                self.fecDOWN = int(match.group(1))
                self.fecUP = int(match.group(2))
            if match := re.search(r'\s+CRC\s+:\s+(\d+)\s+(\d+)', line):
                self.crcDOWN = int(match.group(1))
                self.crcUP = int(match.group(2))

    def updateLineState(self):
        status, _ = self.getStats()
        if status is None:
            return
        
        pattern = r"State\s*:\s*(\w+)"
        for line in status.splitlines():
            if match := re.search(pattern, line):
                self.isOnline = match.group(1) == "SHOWTIME"
                break
    
    def reboot(self):
        if self.client is not None:
            self.client.execute("sys reboot")
    
    def disconnectLine(self):
        raise NotImplementedError
    
    def connectLine(self):
        raise NotImplementedError