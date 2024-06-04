import logging
from microkinetics_motionet.mn100 import MN100


if __name__ == "__main__":
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    # initialize controller
    controller = MN100()

    controller.connect(port="COM10")

    # identity = controller.get_id()
    # logging.info(f"identity: {identity}")

    controller.tear()
