import logging
import time
import sys
import datetime
from datetime import datetime
from datetime import timezone 
from datetime import timedelta 
import time
import xml.etree.ElementTree as ET

_LOGGER = logging.getLogger(__name__)


class Meter(object):
    """
    This is a collection of meter data that we care about.
    """

    def __init__(self, api_interface, meter_type, meter_id, update_interval):
        self.api = api_interface
        self.type = meter_type
        self.id = meter_id
        self.start_date = datetime.today().strftime("%m / %d / %Y")
        self.update_interval = 10
        if update_interval > 10:
            self.update_interval = update_interval
        self.date = datetime.now()
        self.update(True)

    def get_daily_usage(self,days):
        tree = ET.parse(self.id + '.xml')
        root = tree.getroot()

        data_dict={}

        for item in root:
            for child in item:
                for child2 in child:
                    for child3 in child2:
                        for child4 in child3:
                            if(child4.tag == '{http://naesb.org/espi}start'):
                                data_time = child4.text
                        if(child3.tag == '{http://naesb.org/espi}value'):
                            data_value = child3.text
                            data_dict.update({data_time: data_value})


        yesterday = datetime.now() - timedelta(days)

        yesterday_beginning = datetime(yesterday.year, yesterday.month, yesterday.day,0,0,0,0)
        yesterday_beginning = int(yesterday_beginning.replace(tzinfo=timezone.utc).timestamp())



        yesterday_end = datetime(yesterday.year, yesterday.month, yesterday.day,23,59,59,999)
        yesterday_end = int(yesterday_end.replace(tzinfo=timezone.utc).timestamp())




        total=0
        for x in data_dict.keys():
            if ((int(x) >= yesterday_beginning) and (int(x) <= (yesterday_end))):
                total += float(data_dict[x])
            
        return (round(total,2))

    def get_total(self):
        if self.type == "ELECTRIC":
            return self.total_kwh
        elif self.type == "GAS":
            return self.total_gas
        else:
            _LOGGER.error("Invalid meter type {}".format(self.type))


    def update(self, force=False):
        if ((datetime.now() - self.date).seconds / 60 >= self.update_interval) or force:
            _LOGGER.info("Getting new meter info")
            self.date = datetime.now()
            self.api.download_data(self)
