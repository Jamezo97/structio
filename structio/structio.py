
import struct

from io import BytesIO
from typing import IO, Literal, Union

STRUCT_CONFIG = Union[Literal['@'], Literal['='], Literal['<'], Literal['>'], Literal['!']]

CONFIG = {
    "U64": "Q",
    "U32": "I",
    "U16": "H",
    "U8" : "B",
    
    "I64": "q",
    "I32": "i",
    "I16": "h",
    "I8" : "b",

    "Char" : "c",
    "Float" : "f",
    "Double" : "d"
}

class ReadError(Exception):
    pass
class WriteError(Exception):
    pass

class StructIO:
    _data: IO[bytes]
    def __init__(self, data: Union[bytes, IO[bytes]] = b"", config: STRUCT_CONFIG = "@"):
        if isinstance(data, bytes):
            self._data = BytesIO(data)
        else:
            self._data = data # type: ignore

        for name, struct_type in CONFIG.items():

            def build(s: struct.Struct):
                # As much as possible, we reduce the number of attribute reads required
                self_write = self.write
                self_read = self.read
                s_pack = s.pack
                s_unpack = s.unpack
                size = s.size
                def _write(value):
                    self_write(s_pack(value))
                def _read():
                    return s_unpack(self_read(size))[0]
                setattr(self, "read%s" % name, _read)
                setattr(self, "write%s" % name, _write)

            build(struct.Struct("%s%s" % (config, struct_type)))

    def read(self, n: int = -1):
        """Read n bytes, raise a ReadError if the number specified could not all be read"""
        if n == 0:
            return b""
        if n < 0:
            result = self._data.read()
        else:
            result = self._data.read(n)
            if len(result) != n:
                raise ReadError("Not enough bytes read")
        return result
    
    def write(self, data: bytes):
        """Write 'data' bytes, raise a WriteError if the number specified could not all be written"""
        written = self._data.write(data)
        if written != len(data):
            raise WriteError("Could not write all bytes")
        return written

    def tell(self) -> int:
        return self._data.tell()

    def seek(self, pos: int = -1, whence: int = 0):
        self._data.seek(pos, whence)

    def dump(self) -> bytes:
        """Return the entire contents of the payload as a single byte string."""
        self.seek(0)
        return self.read()

    def readU64(self) -> int: ...
    def readU32(self) -> int: ...
    def readU16(self) -> int: ...
    def readU8(self) -> int: ...
    def readI64(self) -> int: ...
    def readI32(self) -> int: ...
    def readI16(self) -> int: ...
    def readI8(self) -> int: ...
    
    def writeU64(self, value: int): ...
    def writeU32(self, value: int): ...
    def writeU16(self, value: int): ...
    def writeU8(self, value: int): ...
    def writeI64(self, value: int): ...
    def writeI32(self, value: int): ...
    def writeI16(self, value: int): ...
    def writeI8(self, value: int): ...

    def readChar(self) -> str: ...
    def readFloat(self) -> float: ...
    def readDouble(self) -> float: ...
    
    def writeChar(self, value: str): ...
    def writeFloat(self, value: float): ...
    def writeDouble(self, value: float): ...  
