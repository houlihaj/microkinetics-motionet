import logging
import time

from serial import Serial, SerialException, SerialTimeoutException


class ResponseException(Exception):
    """
    Represents general response errors occur during data reception.

    Initializes a new instance of the Exception class with a specified error message.
    """
    def __init__(self, message):
        super().__init__(message)


class ResponseTimeout(ResponseException):
    """
    Represents timeout errors occur during data reception.
    """
    pass


def sleep(duration_seconds: float) -> None:
    """
    This method has finer sleep resolution when compared to the
    conventional time.sleep() method.

    :param duration_seconds: time to sleep for in units of seconds
    :type duration_seconds: float
    """
    now: float = time.perf_counter()
    end: float = now + duration_seconds
    while now < end:
        now: float = time.perf_counter()


class Interface:
    """
    The upper communication level uses this interface 
    to have standardized interface to the physical level.
    The physical interface which implements this interface must already be open, 
    before you can use functions of this interface.
    """

    def __init__(self):
        """
        Implements the IMeComPhy interface for the Serial Port interface.
        """
        super().__init__()
        self.ser = Serial()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ser.__exit__(exc_type, exc_val, exc_tb)

    def __enter__(self):
        return self

    def connect(
            self,
            port: str = "COM10",
            baudrate: int = 9600,
            timeout: int = 1
    ) -> None:
        """

        :param port: Port, as described in description
        :type port: str
        :param baudrate:
        :type baudrate: int
        :param timeout:
        :type timeout: int
        :return:
        """

        self.ser.port = port
        self.ser.baudrate = baudrate
        self.ser.parity = "N"
        self.ser.stopbits = 1
        self.ser.timeout = timeout
        self.ser.write_timeout = timeout
        if self.ser.is_open is False:
            try:
                self.ser.open()
            except SerialException as e:
                raise e
        else:
            raise ResponseException("Serial device is already open!")

    def tear(self) -> None:
        """
        Tear should always be called when the instrument is being disconnected. It should
        also be called when the program is ending.

        :return: None
        """
        self.ser.flush()
        self.ser.close()

    def _read(self, size) -> bytes:
        """
        Read n=size bytes from serial, if <n bytes are received (serial.read() return because of timeout),
        raise a timeout.

        :return:
        :rtype: bytes
        """
        recv: bytes = self.ser.read(size=size)
        if len(recv) < size:
            raise ResponseTimeout("timeout because serial read returned less bytes than expected")
        else:
            return recv

    def send_string(self, stream: bytes) -> None:
        """
        Sends data to the physical interface.

        :param stream: The whole content of the Stream is sent to the physical interface.
        :type stream: bytes
        :return: None
        """
        # clear buffers
        self.ser.reset_output_buffer()
        self.ser.reset_input_buffer()

        # send query
        self.ser.write(stream)

        # flush write cache
        self.ser.flush()

    def get_data_or_timeout(self, timeout: int) -> bytes:
        """
        Tries to read data from the physical interface or throws a timeout exception.

        Reads the available data in the physical interface buffer and returns immediately.
        If the receiving buffer is empty, it tries to read at least one byte.
        It will wait till the timeout occurs if nothing is received.
        Must probably be called several times to receive the whole frame.

        :param timeout:
        :type timeout: period in milliseconds (ms)
        :raises MeComPhyInterfaceException: Thrown when the underlying physical interface
            is not OK.
        :raises MeComPhyTimeoutException: Thrown when 0 bytes were received during the
            specified timeout time.
        :return:
        :rtype: bytes
        """
        try:
            sleep(0.1)  # wait 0.1 seconds for some data

            response_frame: bytes = b''

            # read until timeout is triggered
            runtime_milliseconds: float = 0.0
            start_time_seconds: float = time.monotonic()
            # while (self.ser.in_waiting != 0) and (runtime_milliseconds < timeout):
            while runtime_milliseconds < timeout:
                try:
                    # Read one byte at a time, timeout is set on instance level
                    response_byte: bytes = self._read(size=1)
                except ResponseTimeout:
                    logging.debug("timeout because serial read returned less bytes than expected")
                    if runtime_milliseconds >= timeout:
                        logging.debug(
                            "The timeout has triggered inside of the at get_data_or_timeout() ; "
                            f"there are {self.ser.in_waiting} bytes in-waiting to read"
                        )
                        break
                    else:
                        logging.debug(f"response_frame : {response_frame}")
                        runtime_milliseconds = 1000 * (time.monotonic() - start_time_seconds)
                        logging.debug(f"self.ser.in_waiting : {self.ser.in_waiting}")
                        logging.debug(f"runtime_milliseconds : {runtime_milliseconds}\n")
                        sleep(duration_seconds=0.01)
                        continue
                response_frame += response_byte
                logging.debug(f"response_frame : {response_frame}")
                runtime_milliseconds = 1000 * (time.monotonic() - start_time_seconds)
                logging.debug(f"self.ser.in_waiting : {self.ser.in_waiting}")
                logging.debug(f"runtime_milliseconds : {runtime_milliseconds}\n")
                sleep(duration_seconds=0.01)
            if runtime_milliseconds >= timeout:
                logging.debug(
                    "The timeout has triggered outside of the at get_data_or_timeout() ; "
                    f"there are {self.ser.in_waiting} bytes in-waiting to read\n"
                )

            logging.debug(f"get_data_or_timeout() response_frame : {response_frame}")

            return response_frame

        except SerialTimeoutException as e:
            raise ResponseTimeout(e)

        except Exception as e:
            raise ResponseException(f"Failure during receiving: {e}")
