import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_name = "City - Mesa Canyon.sc4"

def toU32(n):
    return int.from_bytes(raw_bytes[n:n+4], byteorder='little', signed=False)

def hexString(arr, x, n, little_endian):
    b = arr[x:x+n]
    if little_endian:
        return b[::-1].hex()
    else:
        return  b.hex()

with open(f"{project_root}/tests/Files/{file_name}", "rb") as file:
    raw_bytes = file.read()

INDEX_IDS = { #FriendlyName, CppClassName, Depth (need to check group and instance IDs)
    "e86b1eef": ["DirectoryFile", "cGZDBSegmentPackedFile", True],
    "a9dd6ff4": ["TerrainMap", "cSTETerrain", True],
    "6a0f82b2": ["NetworkIndex", "cSC4TrafficNetworkMap", False],
    "c9c05c6e": ["NetworkSubfile1", "cSC4NetworkOccupant", False],
    "ca16374f": ["NetworkSubfile2", "cSC4SubwayOccupant", False],
    "6534284a": ["Type10Exemplars", "", False]}

INDEX_DEPTH = {
    "e86b1eef": {
        "e86b1eef": {
            "286b1f03": ["DirectoryFile", ""]}},
    "a9dd6ff4": {
        "e98f9525": {
            "00000067": ["ReconcileMapSouthSide","SaveEdgeAltitudes"],
            "00000066": ["ReconcileMapEastSide","SaveEdgeAltitudes"],
            "00000065": ["ReconcileMapNorthSide","SaveEdgeAltitudes"],
            "00000064": ["ReconcileMapWestSide","SaveEdgeAltitudes"],
            "00000001": ["TerrainMap","SaveAltitudes"]}}}

print(f"Total size: {len(raw_bytes)} bytes")
print(f"First 20 bytes (Hex): {raw_bytes[:20].hex(' ')}")
print("")
print(f"Index Location (Hex): {raw_bytes[40:44].hex(' ')}")
index_location = toU32(40)
print(f"Index Location (u32): {index_location}")
print("")
print(f"Index Size (Hex): {raw_bytes[44:48].hex(' ')}")
index_size = toU32(44)
print(f"Index Size (u32): {index_size}")
print("")
print("==== INDEX ====")

index = []
for x in range(index_location, index_location + index_size, 20):
    known_type = ""
    typeID = hexString(raw_bytes, x, 4, True)
    groupID = hexString(raw_bytes, x+4, 4, True)
    instanceID = hexString(raw_bytes, x+8, 4, True)
    position = toU32(x+12)
    size = toU32(x+16)
    if typeID in INDEX_IDS:
        if INDEX_IDS[typeID][2]:
            known_type = INDEX_DEPTH[typeID][groupID][instanceID][0]
        else:
            known_type = INDEX_IDS[typeID][0]
    index_entry = [known_type, typeID, groupID, instanceID, position, size]
    index.append(index_entry)

print(f"{index[0]}")
print(f"...")
print(f"")

requires_decompression = False

for entry in index:
    if entry[0]:
        print(f"{entry}")
    if entry[0] is "DirectoryFile":
        requires_decompression = True

