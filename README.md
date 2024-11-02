# structio

Simple wrapper around a binary stream

## Examples

```py
from structio import StructIO

reader = StructIO(open('file.bin', 'rb'))

# Move to the tenth byte
reader.seek(10)

# Read uint32 and float
print(reader.readU32()) # 1234
print(reader.readFloat()) # 56789.0

# Can also create payloads
writer = StructIO()
writer.writeU32(5)
print(writer.dump()) # b'\5\0\0\0'

# Use big endian
writer = StructIO(b"\0\0\0\1", config=">")
print(writer.readU32()) # 1

```
