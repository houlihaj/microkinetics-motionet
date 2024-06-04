import logging
from microkinetics_motionet.mn100 import MN100


if __name__ == "__main__":
    # start logging
    logging.basicConfig(
        # level=logging.DEBUG,
        level=logging.INFO,
        format="%(asctime)s:%(module)s:%(levelname)s:%(message)s"
    )

    # initialize controller
    controller = MN100(address=2)

    controller.connect(port="COM10")

    try:
        position: int = controller.read_position()
        logging.info(f"position: {position}")

        firmware_rev: str = controller.get_firmware_revision()
        logging.info(f"firmware_rev : {firmware_rev}")

        # Move here
        move_pos = controller.move(pos=25_000)
        logging.info(f"move_pos : {move_pos}")

        position: int = controller.read_position()
        logging.info(f"position: {position}")

    except Exception as e:
        logging.exception(f"{e}")

    finally:
        controller.tear()
