from typing import List
from struct import unpack, pack


CONVERT_TO_HEX_DICT = {
    0: "0", 1: "1", 2: "2", 3: "3",
    4: "4", 5: "5", 6: "6", 7: "7",
    8: "8", 9: "9", 10: "A", 11: "B",
    12: "C", 13: "D", 14: "E", 15: "F"
}


CONVERT_TO_DEC_DICT = {
    "0": 0, "1": 1, "2": 2, "3": 3,
    "4": 4, "5": 5, "6": 6, "7": 7,
    "8": 8, "9": 9, "A": 10, "B": 11,
    "C": 12, "D": 13, "E": 14, "F": 15
}


class VarConvert:
    def __init__(self):
        super().__init__()

    # def add_address(self, stream: str, value: int) -> str:
    #     """
    #
    #     :param stream: Writes data to this stream.
    #     :type stream: str
    #     :param value: Device address value to be added.
    #     :type value: int
    #     :return:
    #     :rtype: str
    #     """
    #     value = value | 0x80  # the high bit of the address must be set to 1
    #
    #     stream += "{:02X}".format(value)
    #     return stream

    def add_address(self, stream: list, value: int) -> list:
        """

        :param stream: Writes data to this stream.
        :type stream: list
        :param value: Device address value to be added.
        :type value: int
        :return:
        :rtype: list
        """
        value: int = value | 0x80  # the high bit of the address must be set to 1

        stream.append(value)
        return stream

    def add_string(self, stream: str, value: str) -> str:
        """
        Writes a string to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: str
        :return:
        :rtype: str
        """
        stream += value
        return stream

    # def add_uint8(self, stream: str, value: int) -> str:
    #     """
    #     Writes a UINT8 (unsigned byte) to the stream.
    #
    #     :param stream: Writes data to this stream.
    #     :type stream: str
    #     :param value: Value to be added.
    #     :type value: int
    #     :return: str
    #     """
    #     stream += "{:02X}".format(value)
    #     return stream

    def add_uint8(self, stream: list, value: int) -> list:
        """
        Writes a UINT8 (unsigned byte) to the stream.

        :param stream: Writes data to this stream.
        :type stream: list
        :param value: Value to be added.
        :type value: int
        :return: list
        """
        stream.append(value)
        return stream

    def add_uint16(self, stream: str, value: int) -> str:
        """
        Writes a UINT16 (unsigned byte) to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: int
        :return: str
        """
        stream += "{:04X}".format(value)
        return stream

    def add_int32(self, stream: str, value: int) -> str:
        """
        Writes a INT32 (signed byte) to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: int
        :return: str
        """
        return self.add_uint32(stream=stream, value=value)

    def add_uint32(self, stream: str, value: int) -> str:
        """
        Writes a UINT32 (unsigned byte) to the stream.

        :param stream: Writes data to this stream.
        :type stream: str
        :param value: Value to be added.
        :type value: int
        :return:
        :rtype: str
        """
        stream += "{:08X}".format(value)
        return stream

    def convert_to_hex(self, value: int):
        """
        Converts a value from 0 to 15 to a char '0' - 'F'

        :param value: Number value to be converted.
        :type value: int
        :return: char value '0' - 'F' represented by a byte value.
        :rtype: str
        """
        return CONVERT_TO_HEX_DICT[value]

    def read_uint8(self, stream: str) -> int:
        """
        Reads a UINT8 (byte) from the stream.

        :param stream: Stream where the value is read from.
        :type stream: str
        :return: The read and converted value.
        :rtype: int
        """
        rsp_format = "!B"
        return unpack(rsp_format, bytes.fromhex(stream))[0]

    def read_uint16(self, stream: str) -> str:
        """
        Reads a UINT16 from the stream.

        :param stream: Stream where the value is read from.
        :type stream: str
        :return: The read and converted value.
        :rtype: str
        """
        rsp_format = "!H"
        return unpack(rsp_format, bytes.fromhex(stream))[0]

    def read_int32(self, stream: str) -> int:
        """
        Reads a INT32 from the stream.

        :param stream: Stream where the value is read from.
        :type stream: str
        :return: The read and converted value.
        :rtype: int
        """
        rsp_format = "!i"
        return unpack(rsp_format, bytes.fromhex(stream))[0]

    def convert_to_dec(self, hex_value: str):
        """
        Converts a char from '0' - 'F' to a number value 0-15.

        :param hex_value: char value '0' - 'F' represented by a int.
        :type hex_value: str
        :return: Number value 0-15.
        :rtype: int
        """
        return CONVERT_TO_DEC_DICT[hex_value]
