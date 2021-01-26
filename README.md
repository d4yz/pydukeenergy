# pydukeenergy
Python3 interface to the unofficial Duke Energy API.

**NOTE** This isn't using an official API therefore this library could stop working at any time, without warning.

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
