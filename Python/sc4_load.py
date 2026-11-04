import os
import sys
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QGroupBox, QTableWidgetItem

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

def NormaliseGrid(l, m, o):
    arr = np.array(l, dtype=np.float64)
    k = np.sign(arr) * np.log(np.abs(arr) / 0.763) / np.log(4)
    result = k * m
    return result


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

print(f"")
print(f"Some subfiles have been compressed...")
#TODO decompression code

directory = []

if requires_decompression:
    dir_location = 0;
    dir_size = 0;
    for entry in index:
        if entry[0] is "DirectoryFile":
            dir_location = entry[4]
            dir_size = entry[5]

    for x in range(dir_location, dir_location + dir_size, 20):
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
        dir_entry = [known_type, typeID, groupID, instanceID, position, size]
        directory.append(dir_entry)

print(f"Directory contains {len(directory)} files.")

expanded_index = []
for entry in index:
    expanded_item = {
        "FriendlyName": "",
        "CppClassName": "",
        "Position": 0,
        "IsCompressed": False,
        "FileSize": 0,
        "DecompressedSize": 0,
        "TypeID": "",
        "GroupID": "",
        "InstanceID": "",
        "RequiresDepthCheck": False}

    expanded_item["FriendlyName"] = entry[0]
    expanded_item["TypeID"] = entry[1]
    expanded_item["GroupID"] = entry[2]
    expanded_item["InstanceID"] = entry[3]
    expanded_item["Position"] = entry[4]
    expanded_item["FileSize"] = entry[5]
    for item in directory:
        if item[4] is entry[4]:
            expanded_item["IsCompressed"] = True
            expanded_item["DecompressedSize"] = item[5]
    expanded_index.append(expanded_item)



terrain_data_exists = False
terrain_data_compressed = False
terrain_data_position = 0
terrain_data_size = 0
terrain_grid_size = 0
terrain_data = []
terrain_grid = []

for entry in expanded_index:
    if entry["FriendlyName"] is "TerrainMap":
        terrain_data_exists = True
        terrain_data_compressed = entry["IsCompressed"]
        terrain_data_position = entry["Position"]
        terrain_data_size = entry["FileSize"]
        print(f"{entry}")
        print(f"")

if terrain_data_exists:
    print(f"TerrainData found - P: {terrain_data_position} S: {terrain_data_size}")
    if terrain_data_compressed:
        print(f"TerrainData is compressed")
    else:
        terrain_raw_data = raw_bytes[terrain_data_position:terrain_data_position + terrain_data_size]
        # Header + 2 byte gap
        trim_length = len(terrain_raw_data) - (len(terrain_raw_data) % 4)
        terrain_raw_data = terrain_raw_data[:trim_length]
        terrain_data = np.frombuffer(terrain_raw_data, dtype='>f4')
        print(f"")
        terrain_grid_size = int(np.sqrt(len(terrain_data)))
        print(f"Loaded {len(terrain_data)} points | Square {terrain_grid_size}")
        for i in range(0, terrain_grid_size):
            grid_row = []
            for j in range(0, terrain_grid_size):
                k = i + j * terrain_grid_size
                grid_row.append(terrain_data[k])
            terrain_grid.append(grid_row)


# app = QApplication()
#
# table = QTableWidget()
# table.setRowCount(terrain_grid_size)
# table.setColumnCount(terrain_grid_size)
# table.setHorizontalHeaderLabels(range(0, terrain_grid_size))
# table.setVerticalHeaderLabels(range(0, terrain_grid_size))
#
# for i in range(0, terrain_grid_size):
#     for j in range(0, terrain_grid_size):
#         item = QTableWidgetItem(str(terrain_grid[i][j]))
#         table.setItem(i, j, item)
#
# table.show()
#
# sys.exit(app.exec())

class TerrainView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.viewer = QtInteractor(self)
        layout.addWidget(self.viewer.interactor)

    def load_heightmap(self, heights):
        arr = np.array(heights, dtype=np.float32)
        h_list = arr.tolist()
        z = np.asarray(h_list, dtype=float)

        rows, cols = z.shape
        x, y = np.meshgrid(
            np.arange(rows),
            np.arange(cols),
            indexing="ij")

        terrain = pv.StructuredGrid(x,y,z)
        terrain["Elevation"] = z.ravel(order="F")

        self.viewer.clear()
        self.viewer.add_mesh(terrain, scalars="Elevation", cmap="terrain", show_edges=True)
        self.viewer.reset_camera()
        self.viewer.view_isometric()

print(f"")

app = QApplication()

group = QGroupBox()
group.title = "Some shit, IDK"

test_list = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0,
             0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0,
             0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 1.0, 1.0, 2.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 3.0, 3.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 3.0, 3.0, 3.0, 3.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 2.0, 1.0, 3.0, 3.0, 0.0, 0.0, 3.0, 3.0, 1.0, 2.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 2.0, 1.0, 3.0, 0.0, 0.0, 0.0, 0.0, 3.0, 1.0, 2.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 2.0, 3.0, 0.0, 0.0, 0.0, 0.0, 3.0, 1.0, 2.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 3.0, 3.0, 0.0, 0.0, 3.0, 3.0, 2.0, 1.0, 1.0, 1.0, 1.0,
             0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 3.0, 3.0, 3.0, 3.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0,
             0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 3.0, 3.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0,
             0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0]
test_grid_size = int(np.sqrt(len(test_list)))
test_grid = []
for i in range(0, test_grid_size):
    grid_row = []
    for j in range(0, test_grid_size):
        k = i + j * test_grid_size
        grid_row.append(test_list[k])
    test_grid.append(grid_row)

multiply = 0.1
offset = 0

print(f"Terrain Data size: {len(terrain_grid)}")
print(f"Roof: {np.max(terrain_grid)}")
print(f"Floor: {np.min(terrain_grid)}")

normalised_grid = NormaliseGrid(terrain_grid, multiply, offset)

print(f"Normalised Data size: {len(normalised_grid)}")
print(f"Roof: {np.max(normalised_grid)}")
print(f"Floor: {np.min(normalised_grid)}")


terrain_view = TerrainView(group)
terrain_view.load_heightmap(normalised_grid)

group.show()

sys.exit(app.exec())
