import json
import logging
import os
import signal
import sys
import time

import dotenv
import paho.mqtt.client as mqtt

from Mitsi.Mitsi import HeatPump
from Mitsi.State import State


class MitsiQTT:
    running = False
    topic = 'homeassistant/mitsi'
    host = 'localhost'
    username = ''
    password = ''
    connected_state = 0
    client = mqtt
    state = None
    logger = logging

    def __init__(self, logger, **kwargs):
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        self._load_env()
        self.running = True
        self.logger = logger
        self._setup_heatpump()
        self._setup_state(**kwargs)
        self._setup_client()

    def _setup_heatpump(self):
        self.hp = HeatPump('/dev/ttyAMA0')

    def _setup_state(self, **kwargs):
        if self.state is None:
            self.state = State()
        self.state.update(kwargs)

    def _setup_client(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv31)
        if self.username != '' or self.password != '':
            self.client.username_pw_set(self.username, self.password)
        will_topic = "connected"
        if self.topic:
            will_topic = "%s/%s" % (self.topic, will_topic)
        self.client.will_set(will_topic, "0", qos=1, retain=True)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.host, port=self.port)
        self.on_publish("connected", 1, qos=1, retain=True)
        self.connected_state = 1
        self.client.subscribe("%s/command/#" % self.topic)

    def _load_env(self):
        env_path = os.path.join(os.getcwd(), '.env')
        dotenv.load_dotenv(dotenv_path=env_path)
        self.host = os.getenv("MQTT_HOST", 'localhost')
        self.port = int(os.getenv("MQTT_PORT", 1883))
        self.username = os.getenv("MQTT_USER", '')
        self.password = os.getenv("MQTT_PASS", '')

    def on_connect(self, client, userdata, flags, rc, properties):
        if rc.is_failure:
            raise Exception("Connectivity to MQTT broker failed")
        self.logger.info("Connected to MQTT broker: %s", self.host)
        self.on_publish("connected", 1, qos=1, retain=True)
        self.connected_state = 1
        self.client.subscribe("%s/command/#" % self.topic)
        self.hp.connect()
        self.hp.dirty = True

    def on_publish(self, topic, payload, **kwargs):
        topic = "%s/%s" % (self.topic, topic)
        self.client.publish(topic, payload, **kwargs)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        if self.topic:
            topic = topic.partition("%s/" % self.topic)[2]
        msg_type, s, topic = topic.split("/")
        if msg_type == "command" and topic == "state":
            state = 'Unknown'  # Fallback for the logger error
            try:
                self.state.update(json.loads(msg.payload.decode('utf-8')))
                self.hp.set(self.state.reverse_state())
            except ValueError:
                self.logger.warning("Invalid JSON: %s" % msg.payload)
            except Exception:
                self.logger.error("Failed to set state %s" % json.dumps(state))

    def run(self):
        while self.running:
            self.hp.loop()
            if self.hp.valid and self.hp.dirty:
                if self.connected_state != 2:
                    self.on_publish("connected", 2, qos=1, retain=True)
                    self.connected_state = 2
                self.state.update(self.hp.to_dict())
                self.on_publish("state", json.dumps(self.state.reverse_state()), retain=True)
                self.hp.dirty = False
            if self.client.loop() != 0:
                self.logger.warning("Disonnected from MQTT broker: %s", self.host)
                self.connected_state = 0
                try:
                    self.client.connect(self.host)
                    self.connected_state = 0
                except Exception:
                    self.logger.error("Failed reconnecting to broker!")
                    time.sleep(1)

    def cleanup(self, signum, frame):
        self.client.disconnect()
        self.running = False
        self.connected_state = False
        sys.exit(signum)
