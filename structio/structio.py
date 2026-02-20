
import enum
import struct

from io import BytesIO
from typing import IO, Any, Callable, Dict, Literal, Type, Union

STRUCT_CONFIG = Union[Literal['@'], Literal['='], Literal['<'], Literal['>'], Literal['!']]

class ESigned(enum.Enum):
    invalid = "invalid"
    signed = "signed"
    unsigned = "unsigned"

class VTypeDef:
    code: str
    dtype: Type
    size: int
    signed: ESigned

    def __init__(self, code: str, dtype: Type, signed: ESigned = ESigned.invalid):
        self.code = code
        self.dtype = dtype
        self.size = struct.Struct(code).size
        self.signed = signed

class VType:
    U64 = VTypeDef("Q", int, ESigned.unsigned)
    U32 = VTypeDef("I", int, ESigned.unsigned)
    U16 = VTypeDef("H", int, ESigned.unsigned)
    U8  = VTypeDef("B", int, ESigned.unsigned)
    I64 = VTypeDef("q", int, ESigned.signed)
    I32 = VTypeDef("i", int, ESigned.signed)
    I16 = VTypeDef("h", int, ESigned.signed)
    I8 = VTypeDef("b", int, ESigned.signed)

    Char = VTypeDef("c", str)
    Float = VTypeDef("f", float)
    Double = VTypeDef("d", float)

ALL_TYPES = {
    k: v for k, v in VType.__dict__.items() if isinstance(v, VTypeDef)
}

class ReadError(Exception):
    pass
class WriteError(Exception):
    pass

class RWPair:
    __slots__ = ("read", "write")
    def __init__(self, read: Callable[[], Any], write: Callable[[Any], None]):
        self.read = read
        self.write = write

class StructIO:
    _data: IO[bytes]
    _methods: Dict[VTypeDef, RWPair]
    
    def __init__(self, data: Union[bytes, IO[bytes]] = b"", config: STRUCT_CONFIG = "@"):
        if isinstance(data, bytes):
            self._data = BytesIO(data)
        else:
            self._data = data # type: ignore

        self._methods = {}
        
        def build(name: str, v: VTypeDef):
            s = struct.Struct("%s%s" % (config, v.code))
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

            return _read, _write

        for name, v in ALL_TYPES.items():
            _read, _write = build(name, v)
            self._methods[v] = RWPair(_read, _write)

    def read(self, n: int = -1):
        """Read n bytes, raise a ReadError if the number specified could not all be read"""
        if n == 0:
            return b""
        if n < 0:
            result = self._data.read()
        else:
            result = self._data.read(n)
            if len(result) != n:
                raise ReadError("Only read %d / %d bytes" % (len(result), n))
        return result
    
    def write(self, data: bytes):
        """Write 'data' bytes, raise a WriteError if the number specified could not all be written"""
        written = self._data.write(data)
        if written != len(data):
            raise WriteError("Only wrote %d / %d bytes" % (written, len(data)))
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

    def readStr(self, encoding: str = "utf-8", ltype: VTypeDef = VType.U32) -> str:
        return self.readByteStr(ltype).decode(encoding)
    
    def writeStr(self, value: str, encoding: str = "utf-8", ltype: VTypeDef = VType.U32):
        self.writeByteStr(value.encode(encoding), ltype)
    
    def readByteStr(self, ltype: VTypeDef = VType.U32) -> bytes:
        length: int = self._methods[ltype].read()
        return self.read(length)
    
    def writeByteStr(self, value: bytes, ltype: VTypeDef = VType.U32) -> None:
        self._methods[ltype].write(len(value))
        self.write(value)
