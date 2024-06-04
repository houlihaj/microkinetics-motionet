import logging
from typing import Optional

from microkinetics_motionet.core.query_set import QuerySet
from microkinetics_motionet.core.basic_cmd import BasicCmd
from microkinetics_motionet.core.basic_cmd import ComCommandException

from microkinetics_motionet.interface_wrapper.interface import Interface


class TimeoutException(Exception):
    def __init__(self, message):
        super().__init__(message)
        
        
class InterfaceException(Exception):
    """
    Represents general physical interface errors.

    Initializes a new instance of the Exception class with a specified error message.
    """
    def __init__(self, message):
        super().__init__(message)


class MN100(object):
    """
    A response from each device is obtained upon receipt of a command and at the
    completion of each command with the exception of the special input which, if
    activated, will generate a message automatically. Refer to Page 5 in the
    MN100 Motion Controller Manual.
    """
    def __init__(self, address: int) -> None:
        """

        :param address:
        :type address:
        """
        super().__init__()
        self.phy_com: Optional[Interface] = None
        self.basic_cmd: Optional[BasicCmd] = None
        self.address: int = address

    def connect(self, port: str = "COM10") -> None:
        """
        Connects to a serial port. On Windows, these are typically 'COMX' where X
        is the number of the port. In Linux, they are often /dev/ttyXXXY where XXX
        usually indicates if it is a serial or USB port, and Y indicates the number.
        E.g. /dev/ttyUSB0 on Linux and 'COM7' on Windows

        :param port: Port, as described in description
        :type port: str
        :return:
        """
        self.phy_com: Interface = Interface()
        self.phy_com.connect(port=port)

        query_set = QuerySet(interface=self.phy_com)
        self.basic_cmd = BasicCmd(query_set=query_set)

        retries: int = 3
        for _ in range(retries):
            try:
                logging.debug(f"connected to {self.address}")
                return
            except ComCommandException as e:
                logging.debug(f"[ComCommandException] : {e}")
                continue
        raise ComCommandException(
            f"Could not successfully query the controller address after {retries} retries..."
        )

    def tear(self) -> None:
        """
        Tear should always be called when the instrument is being disconnected. It should
        also be called when the program is ending.

        :return: None
        """
        self.phy_com.tear()

    def get_firmware_revision(self) -> str:
        """
        Returns the device name and firmware revision

        :return:
        :rtype: str
        """
        logging.debug(f"get the firmware revision")
        rsp = self.basic_cmd.get_command(address=self.address, command="?", timeout=500)
        rev: bytes = rsp.data_packet.payload
        return rev.decode()  # decode bytes to str

    def read_position(self) -> int:
        """
        Returns the read position counter

        :return: the read position counter
        :rtype: int
        """
        logging.debug(f"get the read position")
        rsp = self.basic_cmd.get_command(address=self.address, command="E", timeout=500)
        pos: bytes = rsp.data_packet.payload
        return int(pos.decode())  # decode bytes to str and typecast to int

    def set_velocity(self, velocity: int):
        """
        NOT IMPLEMENTED!!

        :return:
        :rtype: str
        """
        logging.debug(f"set velocity")
        rsp = self.basic_cmd.set_command(
            address=self.address, command="V", value=velocity, timeout=5_000
        )
        velocity: bytes = rsp.data_packet.payload
        raise NotImplementedError

    def move(self, pos: int = 10_000):
        """
        Position is in units of steps

        :param pos: position in units of steps
        :type pos: int
        :return:
        """
        logging.debug(f"move position")

        # First, query the starting position
        staring_position: int = int(self.read_position())
        # Second, get the delta position
        delta_position: int = abs(pos - staring_position)
        # Third, get the delta time in seconds
        velocity_steps_per_second: int = 2000
        delta_seconds: float = delta_position / velocity_steps_per_second
        # Fourth, define the timeout period from the expected time to travel (i.e. delta_seconds)
        timeout_seconds: float = 1.2 * delta_seconds
        timeout_milliseconds: int = round(1000 * timeout_seconds)
        logging.info(f"timeout_milliseconds : {timeout_milliseconds}")

        # Then, send the move command
        pos = self.basic_cmd.set_command(
            address=self.address, command="M", value=pos, timeout=timeout_milliseconds
        )
        return pos

    def abort_move(self):
        """
        Aborts the move in progress

        :return:
        """
        raise NotImplementedError

    def read_count(self) -> int:
        """
        Returns the number of uncompleted steps

        :return: the number of uncompleted steps
        :rtype: int
        """
        logging.debug(f"get the read count")
        rsp = self.basic_cmd.get_command(address=self.address, command="N", timeout=500)
        count: bytes = rsp.data_packet.payload
        return int(count.decode())  # decode bytes to str and typecast to int
