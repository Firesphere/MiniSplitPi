import json
import logging
import os
import signal
import sys
import time

import dotenv
import paho.mqtt.client as mqtt

from MiniSplitPi.mitsi import HeatPump


class MQTTSplitPi:
    running = False
    topic = 'minisplit'
    host = 'localhost'
    connected_state = False

    def __init__(self, logger):
        self.running = True
        self.logger = logger
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        self.hp = HeatPump('/dev/ttyAMA0')
        env_path = os.path.join(os.getcwd(), '.env')
        dotenv.load_dotenv(dotenv_path=env_path)
        self.host = os.getenv("MQTT_HOST", 'localhost')
        self.port = int(os.getenv("MQTT_PORT", 1883))
        username = os.getenv("MQTT_USER", '')
        password = os.getenv("MQTT_PASS", '')
        self.client = mqtt.Client()
        if username != '' or password != '':
            self.client.username_pw_set(username, password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.listen
        self.client.connect(self.host, port=self.port)
        self.connected_state = True
        self.client.subscribe("%s/command/#" % self.topic)

    def on_connect(self):
        self.logger.info("Connected to MQTT broker: %s", self.host)
        self.talk("connected", 1, qos=1, retain=True)
        self.connected_state = True
        self.client.subscribe("%s/command/#" % self.topic)
        self.hp.connect()
        self.hp.dirty = True

    def run(self):
        while self.running:
            self.hp.loop()
            if self.hp.valid and self.hp.dirty:
                if self.connected_state != 2:
                    self.talk("connected", 2, qos=1, retain=True)
                    self.connected_state = 2
                self.talk("state", json.dumps(self.hp.to_dict()), retain=True)
                self.hp.dirty = False
            if self.client.loop() != 0:
                self.logger.warning("Disonnected from MQTT broker: %s", self.host)
                self.connected_state = False
                try:
                    self.client.connect(self.host)
                    self.connected_state = True
                except Exception:
                    self.logger.error("Failed reconnecting to broker!")
                    time.sleep(1)

    def cleanup(self, signum):
        self.client.disconnect()
        self.running = False
        self.connected_state = False
        sys.exit(signum)

    def talk(self, topic, payload, **kwargs):
        topic = "%s/%s" % (self.topic, topic)
        self.client.publish(topic, payload, **kwargs)

    def listen(self, client, userdata, msg):
        topic = msg.topic
        if self.topic:
            topic = topic.partition("%s/" % self.topic)[2]
        msg_type, s, topic = topic.partition("/")
        if msg_type == "command":
            if topic == "state":
                state = 'Unknown' # Fallback, so
                try:
                    state = json.loads(msg.payload.decode('utf-8'))
                    self.hp.set(state)
                except ValueError:
                    self.logger.warning("Invalid JSON: %s" % msg.payload)
                except Exception:
                    self.logger.error("Failed to set state %s" % state)


def main():
    logger = logging.getLogger("MQMitsi logger")
    logger.setLevel(logging.WARNING)
    handler = logging.FileHandler(os.path.join(os.getcwd(), 'mqmitsi.log'))
    formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    split_pi = MQTTSplitPi(logger)
    try:
        split_pi.run()
    except Exception:
        split_pi.cleanup(signal.SIGTERM)


if __name__ == '__main__':
    main()
