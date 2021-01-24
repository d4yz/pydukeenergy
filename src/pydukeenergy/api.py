import logging
import json
import sys
from datetime import datetime, timedelta

import requests

from pydukeenergy.meter import Meter

BASE_URL = "https://www.duke-energy.com/"
LOGIN_URL = BASE_URL + "form/SignIn/GetAccountValidationMessage"
# LOGIN_URL = BASE_URL + "form/Login/GetAccountValidationMessage"
USAGE_ANALYSIS_URL = BASE_URL + "api/UsageAnalysis/"
BILLING_INFORMATION_URL = USAGE_ANALYSIS_URL + "GetBillingInformation"
METER_ACTIVE_URL = BASE_URL + "my-account/usage-analysis"
USAGE_CHART_URL = USAGE_ANALYSIS_URL + "GetUsageChartData"
DOWNLOAD_DATA_URL = USAGE_ANALYSIS_URL + "DownloadMyData"

USER_AGENT = {"User-Agent": "python/{}.{} pyduke-energy/0.0.6"}
LOGIN_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}
USAGE_ANALYSIS_HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/plain, */*"}

_LOGGER = logging.getLogger(__name__)


class DukeEnergy(object):
    """
    API interface object.
    """

    def __init__(self, email, password, electric_meters, gas_meters=None, update_interval=60, verify_ssl=False):
        """
        Create the Duke Energy API interface object.
        Args:
            email (str): Duke Energy account email address.
            password (str): Duke Energy account password.
            electric_meters (list of str): List of electric meter ID's to monitor
            gas_meters (list of str): List of gas meter ID's to monitor
            update_interval (int): How often an update should occur. (Min=10)
        """
        global USER_AGENT
        version_info = sys.version_info
        major = version_info.major
        minor = version_info.minor
        USER_AGENT["User-Agent"] = USER_AGENT["User-Agent"].format(major, minor)
        self.email = email
        self.password = password
        self.verify = verify_ssl
        if self.verify is False:
            _LOGGER.warning("User has chosen to disable SSL verification. Supressing all insecure request warnings.")
            import urllib3
            urllib3.disable_warnings()
        if type(electric_meters) is not list:
            electric_meters = list([electric_meters])
        if not gas_meters:
            self._meters = {"ELECTRIC": electric_meters, "GAS": []}
        else:
            if type(gas_meters) is not list:
                gas_meters = list([gas_meters])
            self._meters = {"ELECTRIC": electric_meters, "GAS": gas_meters}
        self.meters = []
        self.session = requests.Session()
        self.update_interval = update_interval
        if not self._login():
            raise DukeEnergyException("")

    def get_meters(self):
        self._get_meters()
        return self.meters

    def get_billing_info(self, meter):
        """
        Pull the billing info for the meter.
        """
        if self.session.cookies or self._login():
            post_body = {"MeterNumber": f"{meter.type} - {meter.id}"}
            headers = USAGE_ANALYSIS_HEADERS.copy()
            headers.update(USER_AGENT)
            response = self.session.post(BILLING_INFORMATION_URL, data=json.dumps(post_body), headers=headers,
                                         timeout=10, verify=self.verify)
            _LOGGER.debug(str(response.content))
            try:
                if response.status_code != 200:
                    _LOGGER.error("Billing info request failed: " + response.status_code)
                    self._logout()
                    return False
                if response.json()["Status"] == "ERROR":
                    self._logout()
                    return False
                if response.json()["Status"] == "OK":
                    meter.set_billing_usage(response.json()["Data"][-1])
                    return True
                else:
                    _LOGGER.error("Status was {}".format(response.json()["Status"]))
                    self._logout()
                    return False
            except Exception as e:
                _LOGGER.exception("Something went wrong. Logging out and trying again.")
                self._logout()
                return False

    def get_usage_chart_data(self, meter):
        """
        billing_frequency ["Week", "Billing Cycle", "Month"]
        graph ["hourlyEnergyUse", "DailyEnergy", "averageEnergyByDayOfWeek"]
        """
        if datetime.today().weekday() == 6:
            the_date = meter.date - timedelta(days=1)
        else:
            the_date = meter.date
        #~ if self.session.cookies or self._login():
            #~ post_body = {
                #~ "Graph": "DailyEnergy",
                #~ "BillingFrequency": "Billing Cycle",
                #~ "GraphText": "Daily Energy and Avg. ",
                #~ "Date": meter.start_date,
                #~ "MeterNumber": meter.type + " - " + meter.id,
                #~ "ActiveDate": "11/18/2019"
            #~ }
            #~ headers = USAGE_ANALYSIS_HEADERS.copy()
            #~ headers.update(USER_AGENT)
            #~ response = self.session.post(USAGE_CHART_URL, data=json.dumps(post_body), headers=headers, 
                                        #~ timeout=10, verify=self.verify)
            #~ _LOGGER.debug(str(response.content))
            
        if self.session.cookies or self._login():
            post_body = {
                "MeterNumber": meter.type + " - " + meter.id,
            }
            print (post_body)
            headers = USAGE_ANALYSIS_HEADERS.copy()
            headers.update(USER_AGENT)
            response = self.session.post(DOWNLOAD_DATA_URL, data=json.dumps(post_body), headers=headers, 
                                        timeout=10, verify=self.verify)
            _LOGGER.debug(str(response.content))


            try:
                if response.status_code != 200:
                    _LOGGER.error("Usage data request failed: " + response.status_code)
                    self._logout()
                    return False
                else:
                    open('data.xml', 'w').write(response.text)
                    return True
            except Exception as e:
                print ("dsg")
                _LOGGER.exception("Something went wrong. Logging out and trying again.")
                self._logout()
                return False

    def _login(self):
        """
        Authenticate. This creates a cookie on the session which is used to authenticate with
        the other calls. Unfortunately the service always returns 200 even if you have a wrong
        password.
        """
        _LOGGER.debug("Logging in.")
        data = {"userId": self.email, "userPassword": self.password, "deviceprofile": "mobile"}
        headers = LOGIN_HEADERS.copy()
        headers.update(USER_AGENT)
        try:
            response = self.session.post(LOGIN_URL, data=data, headers=headers, timeout=10, verify=self.verify)
        except requests.exceptions.SSLError:
            _LOGGER.error("SSL certificate error. Trying setting 'verify' to False.")
        except Exception:
            _LOGGER.exception("Failed to log in")
        if response.status_code != 200:
            _LOGGER.exception("Failed to log in")
            return False
        response = self.session.get(METER_ACTIVE_URL, timeout=10)
        return True

    def _logout(self):
        """
        Delete the session.
        """
        _LOGGER.debug("Logging out.")
        self.session.cookies.clear()

    def _get_meters(self):
        """
        There doesn't appear to be a service to get this data.
        Collecting the meter info to build meter objects.
        """
        
        if self._login():
            for meter in self._meters['ELECTRIC']:
                self.meters.append(Meter(self, "ELECTRIC", str(meter), self.update_interval))
            if len(self._meters['GAS']) != 0:
                for meter in self._meters['GAS']:
                    self.meters.append(Meter(self, "GAS", str(meter), self.update_interval))
            self._logout()


class DukeEnergyException(Exception):
    pass
