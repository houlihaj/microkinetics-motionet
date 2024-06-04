import logging

from microkinetics_motionet.core.frame import TxPacket, RxPacket
from microkinetics_motionet.core.query_set import QuerySet
from microkinetics_motionet.core.var_convert import VarConvert


class ComCommandException(Exception):
    def __init__(self, message):
        super().__init__(message)


class BasicCmd:
    """
    Basic communication commands. Most of the products do support them.

    A response from each device is obtained upon receipt of a command and at the
    completion of each command with the exception of the special input which, if
    activated, will generate a message automatically. Refer to Page 5 in the
    MN100 Motion Controller Manual.
    """

    def __init__(self, query_set: QuerySet):
        """
        Initializes a new instance of BasicCmd.

        :param query_set: Reference to the communication interface.
        :type query_set: QuerySet
        """
        super().__init__()
        
        self.query_set: QuerySet = query_set

    # region Functions for ID Parameter system
    def get_command(self, address: int, command: str, timeout: int) -> RxPacket:
        """
        Returns a signed int 32-bit value from the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on QuerySet.
        :type address: int
        :param command:
        :type command: str
        :param timeout:
        :type timeout: period in milliseconds (ms)
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        :return: Returned value.
        :rtype: int
        """
        var_convert: VarConvert = VarConvert()
        try:
            tx_frame: TxPacket = TxPacket(address=address)
            tx_frame.payload = var_convert.add_string(stream=tx_frame.payload, value=command)
            rx_frame: RxPacket = self.query_set.query(tx_frame=tx_frame, timeout=timeout)
            logging.debug(f"get_command\n\trx_frame : {rx_frame}")
            logging.info(
                "get_command() rx_frame.echo_packet.return_code : "
                f"{rx_frame.echo_packet.return_code}"
            )
            return rx_frame
        except Exception as e:
            raise ComCommandException(f"Get command value failed: {e}")

    def set_command(self, address: int, command: str, value: int, timeout: int) -> RxPacket:
        """
        Sets a command value to the device.

        :param address: Device Address. Use null to use the DefaultDeviceAddress defined on QuerySet.
        :type address: int
        :param command: Device Parameter ID.
        :type command: str
        :param value: Vale to set.
        :type value: int
        :param timeout:
        :type timeout: period in milliseconds (ms)
        :raises ComCommandException: When the command fails. Check the inner exception for details.
        """
        var_convert: VarConvert = VarConvert()
        try:
            tx_frame: TxPacket = TxPacket(address=address)
            tx_frame.payload = var_convert.add_string(
                stream=tx_frame.payload, value=f"{command}{value}"
            )
            rx_frame: RxPacket = self.query_set.set(tx_frame=tx_frame, timeout=timeout)
            return rx_frame

        except Exception as e:
            raise ComCommandException(
                f"Set Command Value failed: Address: {address}; "
                f"Command: {command}; Value: {value} : {e}"
            )

    # endregion
