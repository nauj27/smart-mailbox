import time
import machine
import secrets
import network
from pinout import Pinout
from umqtt.simple import MQTTClient

MS_IN_SECOND = 1000
DEEPSLEEP_SECONDS = 28800 # eight hours
WAIT_BEFORE_SLEEP_MS = 1000
CONNECT_WIFI_TIMEOUT_MS = 10000
CONNECT_WIFI_WAIT_MS = 100

wlan = network.WLAN(network.STA_IF)    
barrier = machine.Pin(
    Pinout.D6,
    machine.Pin.IN,
    machine.Pin.PULL_UP,
)
print('Pin configured successfully!')

def mail_detected():
    return not barrier.value()

def connect_wifi(timeout=CONNECT_WIFI_TIMEOUT_MS):
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(secrets.WIFI_ESSID, secrets.WIFI_PSK)
        time_waiting = 0
        while not wlan.isconnected() and time_waiting < timeout:
            time.sleep_ms(CONNECT_WIFI_WAIT_MS)
            time_waiting += CONNECT_WIFI_WAIT_MS
    return wlan.isconnected()
    
def disconnect_wifi():
    wlan.disconnect()
    wlan.active(False)

def notify_mail():
    c = MQTTClient(
        'mailbox',
        secrets.MQTT_HOST,
        secrets.MQTT_PORT,
    )
    c.connect()
    c.publish(
        secrets.MQTT_TOPIC,
        '{"mail": 1}',
        retain = False,
        qos = 1,
    )
    c.disconnect()
    
def deep_sleep(seconds):
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    rtc.alarm(rtc.ALARM0, seconds * MS_IN_SECOND)
    machine.deepsleep()

def main():
    if mail_detected():
        print('You have a mail!')
        if connect_wifi():
            notify_mail()
        else:
            print('Cannot connect to wifi')
    else:
        print('There is no new mail')

    print('Now going to sleep for %d seconds...' % DEEPSLEEP_SECONDS)
    time.sleep_ms(WAIT_BEFORE_SLEEP_MS)
    deep_sleep(DEEPSLEEP_SECONDS)

if __name__ == '__main__':
    main()

