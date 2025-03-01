import os
import dotenv
from paho.mqtt import subscribe, publish

class MQTTSplitPi:
    username = ''
    password = ''
    topic = 'minisplit'
    host = 'localhost'

    def __init__(self):
        env_path = os.path.join(os.getcwd(), '.env')
        dotenv.load_dotenv(dotenv_path=env_path)
        self.host = os.getenv("MQTT_HOST", 'localhost')
        self.port = int(os.getenv("MQTT_PORT", 1883))
        username = os.getenv("MQTT_USER", '')
        password = os.getenv("MQTT_PASS", '')
        if username != '' or password != '':
            self.auth = {"username": username, "password": password}


    def listen(self):
        subscribe.simple('')

def main():
    MQTTSplitPi().listen()


if __name__ == '__main__':
    main()