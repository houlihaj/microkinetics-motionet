import logging

from microkinetics_motionet.core.frame import Frame, TxPacket, RxPacket
from microkinetics_motionet.interface_wrapper.interface import Interface, ResponseTimeout


class GeneralException(Exception):
    """
    Is used to encapsulate all not specific exceptions.
    Check the inner exception for details.
    """

    def __init__(self, message):
        super().__init__(message)


class SetServerErrorException(GeneralException):
    pass


class CheckIfConnectedOrException(GeneralException):
    """
    If the interface is not ready and the current thread is not the
    creator of this instance, throw exception
    """
    pass


class ServerException(GeneralException):
    """
    Is used when the server has returned a Server Error Code.
    """
    pass


class NotConnectedException(GeneralException):
    """
    Initializes a new instance of NotConnectedException.
    """
    pass


class QuerySet:
    """
    Represents the transport layer of the communication protocol.
    Is responsible that each query of set is executed correctly,
    otherwise it will throw an exception.
    """

    def __init__(self, interface: Interface):
        """
        Initializes the communication interface.
        This object can then be passed to the Command objects like MeBasicCmd.

        :param interface:
        :type interface: Interface
        """
        super().__init__()

        self.phy_com: Interface = interface
        self.me_frame: Frame = Frame(interface=interface)

        self.is_ready: bool = False

    def check_if_connected(self) -> bool:
        """
        If the interface is not ready and the current thread is
        not the creator of this instance, throw exception

        :return:
        :rtype: bool
        """
        return True

    def query(self, tx_frame: TxPacket, timeout: int) -> RxPacket:
        """
        Executes a Query. A Query is used to get some data back from the server.
        It tries automatically 3 times to resend the package if no data is replayed from the server
        of if the returned data is wrong.

        :param tx_frame: Definition of the data to send.
        :type tx_frame: TxPacket
        :param timeout:
        :type timeout: period in milliseconds (ms)
        :raises GeneralException: On timeout or any other exception. Check the
            inner exception for details.
        :raises ServerException: When the server replays with a Server Error Code.
        :raises NotConnectedException: When the interface is not connected.
            (Only if the calling thread is different from the creator of this object)
        :return: Received data.
        :rtype: RxPacket
        """
        try:
            self.check_if_connected()

            try:
                rx_frame: RxPacket = self.local_query(tx_frame=tx_frame, timeout=timeout)
                logging.debug(f"query()\n\trx_frame : {rx_frame}")
                return rx_frame
            except ServerException as e:
                raise e
            except GeneralException as e:
                self.is_ready: bool = False
                raise e

        except NotConnectedException as e:
            raise e

    def set(self, tx_frame: TxPacket, timeout: int) -> RxPacket:
        """
        Executes a Set. A Set is used to set some data to the server.
        No data can be received from the server.
        It tries automatically 3 times to resend the package if no data is replayed from the server
        of if the returned data is wrong.

        :param tx_frame: Definition of the data to send.
        :type tx_frame: TxPacket
        :param timeout:
        :type timeout: period in milliseconds (ms)
        :raises GeneralException: On timeout or any other exception. Check the
            inner exception for details.
        :raises ServerException: When the server replays with a Server Error Code.
        :raises NotConnectedException: When the interface is not connected.
            (Only if the calling thread is different from the creator of this object)
        :return: Received data
        :rtype: TxPacket
        """
        try:
            self.check_if_connected()

            try:
                rx_frame: RxPacket = self.local_set(tx_frame=tx_frame, timeout=timeout)
                return rx_frame

            except ServerException as e:
                raise e

            except GeneralException as e:
                self.is_ready: bool = False
                raise e

        except NotConnectedException as e:
            raise e

    def local_query(self, tx_frame: TxPacket, timeout: int):
        """

        :param tx_frame:
        :type tx_frame: TxPacket
        :param timeout:
        :type timeout: period in milliseconds (ms)
        :return:
        :rtype: RxPacket
        """

        trials_left: int = 3
        rx_frame: RxPacket = RxPacket()

        while trials_left > 0:
            trials_left -= 1

            try:
                self.me_frame.send_frame(tx_frame=tx_frame)
                rx_frame: RxPacket = self.me_frame.receive_frame_or_timeout(timeout=timeout)
                logging.debug(f"local_query()\n\trx_frame : {rx_frame}")
                return rx_frame

            except ResponseTimeout:
                # Ignore timeout on this level if some trials are left
                if trials_left == 0:
                    raise GeneralException("Query failed: Timeout!")

            except ServerException as e:
                raise e

            except Exception as e:
                raise GeneralException(f"Query failed : {e}")

        if rx_frame.echo_packet.address != tx_frame.address:
            raise GeneralException(
                f"Query failed : Wrong Address received. "
                f"Received {rx_frame.echo_packet.address} ; Expected {tx_frame.address}"
            )

        raise GeneralException("Query failed : Unknown error")

    def local_set(self, tx_frame: TxPacket, timeout: int) -> RxPacket:
        """

        :param tx_frame:
        :type tx_frame: TxPacket
        :param timeout:
        :type timeout: period in milliseconds (ms)
        :return:
        :rtype: RxPacket
        """

        trials_left: int = 3
        rx_frame: TxPacket = TxPacket()

        while trials_left > 0:
            trials_left -= 1

            try:
                self.me_frame.send_frame(tx_frame=tx_frame)
                rx_frame: RxPacket = self.me_frame.receive_frame_or_timeout(timeout=timeout)
                logging.debug(f"local_set()\n\trx_frame : {rx_frame}")
                return rx_frame

            except ResponseTimeout as e:
                # Ignore Timeout on this level if some trials are left
                if trials_left == 0:
                    raise GeneralException(f"Set failed: Timeout! : {e}")

            except ServerException:
                raise ServerException

            except Exception as e:
                raise GeneralException(f"Set failed : {e}")

        if rx_frame.address != tx_frame.address:
            raise GeneralException(
                f"Set failed: Wrong Address received. "
                f"Received {rx_frame.address} ; Expected {tx_frame.address}"
            )

        raise GeneralException("Set failed: Unknown error")
