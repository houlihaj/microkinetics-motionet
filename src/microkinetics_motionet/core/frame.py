import logging

from enum import Enum
from typing import Optional
from dataclasses import dataclass

from microkinetics_motionet.core.var_convert import VarConvert
from microkinetics_motionet.interface_wrapper.interface import Interface


class WrongChecksumException(Exception):
    def __init__(self, message):
        super().__init__(message)


class ReturnCode(Enum):
    START = 3  # command was received and is being processed
    MOVE_ABORTED = 4
    COMMAND_FINISHED = 5  # the command has been processed
    SLAVE_CHECKSUM_ERROR = 7
    SLAVE_ADDRESS_ERROR = 8
    INVALID_COMMAND = 12
    INVALID_PARAMETER = 14
    NO_COMMAND = 15  # no command in packet sent to MN slave
    NO_MOVE_PENDING = 16
    MOVE_ALREADY_PENDING = 17
    BUSY = 20  # a move is in process and no commands can be received
    PRESENT = 22  # the MN slave is present at specified address
    NOT_AVAILABLE = 29  # the specified port is unavailable
    MOVE_STOPPED = 32  # move stopped by 'Q' command (decelerated move)


@dataclass
class TxPacket:
    """
    Represents all fields within a package.

    :param address: Device address. The address of the device that is to receive
        the packer. The high bit of the address must be set to 1. The setting of
        the high bit of the address is handled by the MN Library routines.
    :type address: int
    :param command: MN100 command from the command set located in the programmer's
        manual
    :type command: int
    :param parameter: The number required by the command. The parameter must be
        in ASCII format with the value between 48 ("0") and 57 ("9"). Also, the
        data must be within the specified range for the command.
    :type parameter: int
    """

    address: int
    command: int  # top-level wrapper will use ASCII character, have to convert to int
    parameter: int

    def __init__(self, address: int = 1):
        """
        Initializes a new instance of a data package.

        :param address: Destination address.
        :type address: int
        """
        super().__init__()

        self.address = address
        self.command = 0
        self.parameter = 0
        self.payload = ""


@dataclass
class EchoPacket:
    """
    Represents all fields within a package.

    :param address: Device address. The address of the device that is to receive
        the packer. The high bit of the address must be set to 1. The setting of
        the high bit of the address is handled by the MN Library routines.
    :type address: int
    :param command: MN100 command from the command set located in the programmer's
        manual
    :type command: int
    :param return_code: A single character value that indicates if an error has
        occured or not
    :type return_code: int
    """

    address: int
    command: int  # top-level wrapper will use ASCII character, have to convert to int
    return_code: int

    def __init__(self, address: int = 1):
        """
        Initializes a new instance of a data package.

        :param address: Destination address.
        :type address: int
        """
        super().__init__()

        self.address = address
        self.command = 0
        self.return_code = 0


@dataclass
class DataPacket:
    """
    Represents all fields within a package.

    :param address: Device address. The address of the device that is to receive
        the packer. The high bit of the address must be set to 1. The setting of
        the high bit of the address is handled by the MN Library routines.
    :type address: int
    :param command: MN100 command from the command set located in the programmer's
        manual
    :type command: int
    :param parameter: The number required by the command. The parameter must be
        in ASCII format with the value between 48 ("0") and 57 ("9"). Also, the
        data must be within the specified range for the command.
    :type parameter: int
    :param return_code: A single character value that indicates if an error has
        occured or not
    :type return_code: int
    """

    address: int
    command: int  # top-level wrapper will use ASCII character, have to convert to int
    parameter: int
    payload: bytes

    def __init__(self, address: int = 1):
        """
        Initializes a new instance of a data package.

        :param address: Destination address.
        :type address: int
        """
        super().__init__()

        self.address = address
        self.command = 0
        self.parameter = 0
        self.payload = b""


@dataclass
class RxPacket:
    """
    Represents all fields within a package.

    :param echo_packet:
    :type echo_packet: Optional[EchoPacket]
    :param data_packet:
    :type data_packet: Optional[DataPacket]
    """

    echo_packet: Optional[EchoPacket]
    data_packet: Optional[DataPacket]

    def __init__(self, address: int = 1):
        """
        Initializes a new instance of a data package.

        :param address: Destination address.
        :type address: int
        """
        super().__init__()

        self.echo_packet: Optional[EchoPacket] = None
        self.data_packet: Optional[DataPacket] = None


class Frame:
    """
    Handles the communication Frame level of the Meerstetter Engineering GmbH
    Communication protocol.
    """

    def __init__(self, interface: Interface):
        """
        Saves the needed interface internally for further use.

        :param interface: interface to the physical interface.
        :type interface: Interface
        """
        super().__init__()

        self.phy_com: Interface = interface

        self.tx_checksum: int = 0

    def send_frame(self, tx_frame: TxPacket) -> None:
        """
        Serializes the given Data structure to a proper
        frame and sends it to the physical interface.
        It returns immediately.

        :param tx_frame: Data to send.
        :type tx_frame: TxPacket
        :raises PhyInterfaceException:
        :return: None
        """
        var_convert = VarConvert()

        # Build the Transmit Frame (i.e. tx_stream)
        tx_stream: list[int] = []

        tx_stream: list[int] = var_convert.add_address(stream=tx_stream, value=tx_frame.address)

        for ascii_char in tx_frame.payload:
            tx_stream.append(ord(ascii_char))

        tx_stream: list[int] = var_convert.add_address(stream=tx_stream, value=tx_frame.address)

        self.tx_checksum: int = self._calc_checksum(frame=tx_stream)

        tx_stream: list[int] = var_convert.add_uint8(stream=tx_stream, value=self.tx_checksum)

        logging.debug(f"tx_stream : {tx_stream}")

        tx_stream_bytes: bytes = bytes(tx_stream)

        logging.debug(f"tx_stream_bytes : {tx_stream_bytes}")

        self.phy_com.send_string(stream=tx_stream_bytes)

    def receive_frame_or_timeout(self, timeout: int) -> RxPacket:
        """
        Receives a correct frame or throws a timeout exception.

        A response from each device is obtained upon receipt of a command and at the
        completion of each command with the exception of the special input which, if
        activated, will generate a message automatically. Refer to Page 5 in the
        MN100 Motion Controller Manual.

        :param timeout:
        :type timeout: period in milliseconds (ms)
        :return: Received data.
        :rtype: RxPacket
        """
        rx_frame: RxPacket = RxPacket()

        rx_stream: bytes = self.phy_com.get_data_or_timeout(timeout=timeout)

        logging.debug(f"receive_frame_or_timeout() rx_stream : {rx_stream}")

        rx_frame: RxPacket = self._decode_frame(rx_frame=rx_frame, rx_stream=rx_stream)

        logging.debug(f"receive_frame_or_timeout()\n\trx_frame : {rx_frame}")

        return rx_frame

    def _decode_frame(self, rx_frame: RxPacket, rx_stream: bytes) -> RxPacket:
        """

        :param rx_frame:
        :type rx_frame: RxPacket
        :param rx_stream:
        :type rx_stream: bytes
        :return:
        :return: RxPacket
        """
        echo_frame: EchoPacket = self._decode_echo(rx_stream=rx_stream)

        data_frame: DataPacket = self._decode_data(rx_stream=rx_stream)

        rx_frame.echo_packet = echo_frame
        rx_frame.data_packet = data_frame

        return rx_frame

    def _decode_echo(self, rx_stream: bytes) -> EchoPacket:
        """

        :param rx_stream:
        :type rx_stream: bytes
        :return:
        :return: EchoPacket
        """
        echo_frame = EchoPacket()

        echo_frame.address = rx_stream[0]
        echo_frame.command = rx_stream[1]
        echo_frame.return_code = ReturnCode(rx_stream[2])

        echo_checksum: int = self._calc_checksum(frame=rx_stream[0:4])

        # Verify echo checksum
        if echo_checksum != rx_stream[4]:
            raise Exception(
                "Calculated echo checksum does not match actual echo checksum ; "
                f"calculated : {echo_checksum} , actual : {rx_stream[4]}"
            )

        return echo_frame

    def _decode_data(self, rx_stream: bytes) -> DataPacket:
        """

        :param rx_stream:
        :return:
        """
        data_frame = DataPacket()

        data_frame.address = rx_stream[5]
        data_frame.command = rx_stream[6]

        i = 7
        while rx_stream[i] != data_frame.address:
            i += 1

        data_frame.payload = rx_stream[7:i]

        data_checksum: int = self._calc_checksum(frame=rx_stream[5:i + 1])

        # Verify data checksum
        if data_checksum != rx_stream[i + 1]:
            raise Exception(
                "Calculated data checksum does not match actual data checksum ; "
                f"calculated : {data_checksum} , actual : {rx_stream[i + 1]}"
            )

        return data_frame

    def _calc_checksum(self, frame: list | bytes) -> int:
        """

        :param frame: frame without the checksum
        :type frame: list | bytes
        :return: the checksum for the given frame
        :rtype: int
        """
        checksum = 0
        for byte in frame:
            checksum += byte
        checksum = (checksum & 0x7F)  # AND with 0x7F to clear the high bit
        return checksum
