# pydukeenergy
Python3 interface to the unofficial Duke Energy API.

**NOTE** This isn't using an official API therefore this library could stop working at any time, without warning.

This script will click on the "Download my Data" button that is on the Duke Energy Usage Analysis page (https://www.duke-energy.com/my-account/usage-analysis)

It will download the XML of all your data which has been updated every 15/30/60 minutes depending on the smart meter installed.

**Example Code**
```python
from pydukeenergy.api import DukeEnergy

duke = DukeEnergy(username, password, electric_meters=[xxx],update_interval=60,verify_ssl=False)
meters = duke.get_meters()
for meter in meters:
    print (meter.get_daily_usage(1)) #1 Day ago Usage in kWh
    print (meter.get_daily_usage(2)) #2 Day ago Usage in kWh
    print (meter.get_daily_usage(3)) #3 Day ago Usage in kWh
    print (meter.get_daily_usage(4)) #etc..
    print (meter.get_daily_usage(5))
    print (meter.get_daily_usage(6))

```
