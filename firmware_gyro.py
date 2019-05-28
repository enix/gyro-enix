import machine
import network
import apa102
import ujson
import time

from umqtt.robust import MQTTClient

# CONFIG

MQTT_BROKER = '192.168.1.58'
MQTT_PREFIX = b"gyro/"

APA102_PIN_DI = 0
APA102_PIN_CI = 2
APA102_PIXELS = 16

DEFAULT_REPEAT = 1
DEFAULT_SLEEP = 0.5


def process_json(message):
    strip = apa102.APA102(machine.Pin(APA102_PIN_CI),
                          machine.Pin(APA102_PIN_DI),
                          APA102_PIXELS)
    parsed = ujson.loads(message)
    
    if 'r' not in parsed:
        parsed['r'] = DEFAULT_REPEAT
    if 's' not in parsed:
        parsed['s'] = DEFAULT_SLEEP
    
    for _ in range(parsed['r']):
        for frame in parsed['f']:
            if isinstance(frame, int):
                for _ in range(frame):
                    time.sleep(parsed['s'])
            else:
                strip.fill([0, 0, 0, 0])
                i = 0
                for pixel in frame:
                    if isinstance(pixel, int):
                        # repeat pixel mode
                        last_pixel = strip[i - 1] if i >= 1 else (0, 0, 0, 0)
                        for _ in range(pixel):
                            strip[i] = last_pixel
                            i += 1
                    else:
                        strip[i] = pixel
                        i += 1
                strip.write()
                time.sleep(parsed['s'])
    strip.fill([0, 0, 0, 0])
    strip.write()


def handle_mqtt_message(topic, message):
    if topic == MQTT_PREFIX + b'json':
        process_json(message)


if __name__ == '__main__':
    strip = apa102.APA102(machine.Pin(APA102_PIN_CI),
                              machine.Pin(APA102_PIN_DI),
                              APA102_PIXELS)
    strip.fill([0, 0, 0, 0])
    strip.write()
    del strip
    wlan = network.WLAN(network.STA_IF)
    while not wlan.isconnected():
        pass  # Wait until connected to wifi
    mqtt = MQTTClient("gyro", MQTT_BROKER)
    mqtt.set_callback(handle_mqtt_message)
    mqtt.connect()
    mqtt.subscribe(MQTT_PREFIX + b'json')
    while True:
        try:
            mqtt.wait_msg()
        except:
            pass  # Ignore errors in request handling
