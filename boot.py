###########################################################################
# Emergency Holographic Filter Set
# Set up basic connectivity to simplify upgrades
###########################################################################

from network import WLAN
import time 
import machine
wlan = WLAN(mode=WLAN.STA)

wlan.connect(ssid='SSID_NAME', auth=(WLAN.WPA2, 'WLANPASSWORD'))
while not wlan.isconnected():
    machine.idle()
print("WiFi connected succesfully")
print(wlan.ifconfig())
rtc = machine.RTC()
rtc.ntp_sync("pool.ntp.org")
while not rtc.synced():
    machine.idle()
print("RTC synced with NTP time")

#adjust your local timezone, by default, NTP time will be GMT
time.timezone(10*60**2) #we are located at GMT+10, thus 2*60*60
