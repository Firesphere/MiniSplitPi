import logging
import os
import signal

from Mitsi.MitsiQTT import MitsiQTT


def main():
    logger = logging.getLogger("MQMitsi logger")
    logger.setLevel(logging.WARNING)
    handler = logging.FileHandler(os.path.join(os.getcwd(), 'mqmitsi.log'))
    formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    split_pi = MitsiQTT(logger)
    try:
        split_pi.run()
    except Exception:
        split_pi.cleanup(signal.SIGTERM, None)
        main()


if __name__ == '__main__':
    main()
