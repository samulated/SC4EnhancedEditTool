import os
import sys
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QGroupBox,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QFormLayout,
    QGridLayout,
    QLabel,
    QTabWidget,
    QPlainTextEdit,
    QSplitter
)

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
    # k = np.sign(arr) * np.log(np.abs(arr) / 0.763) / np.log(4)
    result = arr * m
    return result

def hex_dump(data: bytes, width: int = 16, limit: int = 64 * 1024) -> str:
    # Hex Dump / ASCII readout. Capped in order to not stall out UI
    lines = []
    for off in range(0, min(len(data), limit), width):
        chunk = data[off:off + width]
        hexes = " ".join(f"{b:02X}" for b in chunk)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{off:08X}  {hexes:<{width*3}} {text}")
    if len(data) > limit:
        lines.append(f"... ({len(data) - limit:,} more bytes not shown)")
    return "\n".join(lines)

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
        terrain_raw_data = raw_bytes[terrain_data_position+2:terrain_data_position + terrain_data_size]
        # Header + 2 byte gap
        trim_length = len(terrain_raw_data) - (len(terrain_raw_data) % 4)
        print(f"Bytes: {len(terrain_raw_data)} | Trimmed: {len(terrain_raw_data) - trim_length}")
        print(f"")
        print(f"{terrain_raw_data[:20].hex(' ')}")
        terrain_raw_data = terrain_raw_data[:trim_length]
        terrain_data = np.frombuffer(terrain_raw_data, dtype='<f4')
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

multiply = 0.0625
offset = 0

print(f"Terrain Data size: {len(terrain_grid)}")
print(f"Roof: {np.max(terrain_grid)}")
print(f"Floor: {np.min(terrain_grid)}")

normalised_grid = NormaliseGrid(terrain_grid, multiply, offset)

#print(f"Normalised Data size: {len(normalised_grid)}")
#print(f"Roof: {np.max(normalised_grid)}")
#print(f"Floor: {np.min(normalised_grid)}")


#terrain_view = TerrainView(group)
#terrain_view.load_heightmap(normalised_grid)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SC4 Viewer")
        self.resize(1280, 800)

        # --- Left: file tree (subfile navigation)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Subfile", "Size"])
        self.tree.setColumnWidth(0, 220)
        self.tree.currentItemChanged.connect(self.on_select)

        # --- Right ---
        # --- Top: Header / Directory / Metadata
        #header = QWidget()
        #form = QFormLayout(header)
        #self.lbl_type = QLabel("-")
        #self.lbl_group = QLabel("-")
        #self.lbl_instance = QLabel("-")
        #self.lbl_size = QLabel("-")
        #for lbl in (self.lbl_type, self.lbl_group, self.lbl_instance, self.lbl_size):
        #    lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        #form.addRow("Type:", self.lbl_type)
        #form.addRow("Group:", self.lbl_group)
        #form.addRow("Instance:", self.lbl_instance)
        #form.addRow("Size:", self.lbl_size)
        header = QWidget()
        grid = QGridLayout(header)
        grid.setHorizontalSpacing(12)
        self.fields = {}

        columns = [["Type", "Group", "Instance", "Offset"],
                   ["Friendly Name", "Compressed", "Implemented", "Size"]]
        for col, names in enumerate(columns):
            for row, name in enumerate(names):
                key = QLabel(f"{name}:")
                val = QLabel(f"-")
                val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                grid.addWidget(key, row, col * 2, Qt.AlignmentFlag.AlignRight)
                grid.addWidget(val, row, col * 2 + 1)
                self.fields[name] = val
            grid.setColumnMinimumWidth(col * 2 + 1, 140)

        grid.setColumnStretch(len(columns) * 2, 1)

        # --- Middle: Data Views
        self.views = QTabWidget()
        self.table = QTableWidget()
        self.views.addTab(self.table, "Table")

        self.plotter = None
        if QtInteractor is not None:
            self.plotter = QtInteractor(self.views)
            self.views.addTab(self.plotter.interactor, "3D")

        # --- Bottom: Hex / Graph
        self.bottom = QTabWidget()
        self.hex_spot = QPlainTextEdit()
        self.hex_spot.setReadOnly(True)
        self.hex_spot.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.hex_spot.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.bottom.addTab(self.hex_spot, "Hex")
        self.bottom.addTab(QWidget(), "Graph") # placeholder

        # --- LAYOUT: Vertical splitter on right
        right = QSplitter(Qt.Orientation.Vertical)
        right.addWidget(header)
        right.addWidget(self.views)
        right.addWidget(self.bottom)
        right.setStretchFactor(0, 0) # header
        right.setStretchFactor(1, 3) # data view is prioritised
        right.setStretchFactor(2, 1)
        right.setSizes([110, 470, 220])

        # --- LAYOUT: Horizontal splitter (tree | right)
        main = QSplitter(Qt.Orientation.Horizontal)
        main.addWidget(self.tree)
        main.addWidget(right)
        main.setStretchFactor(0,0)
        main.setStretchFactor(1,1)
        main.setSizes([300, 980])
        self.setCentralWidget(main)

    def load_tree(self, groups):
        for group_name, entries in groups.items():
            parent = QTreeWidgetItem(self.tree, [group_name, ""])
            for name, type_id, group_id, instance_id, position, size, payload in entries:
                n = type_id
                if group_name is "Known":
                    n = name
                item = QTreeWidgetItem(parent, [n, f"{size}"])
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    "type": type_id,
                    "group": group_id,
                    "instance": instance_id,
                    "position": position,
                    "size": size,
                    "data": payload,
                    "name": name
                })
        self.tree.expandAll()

    def on_select(self, current, _previous):
        if current is None:
            return
        entry = current.data(0, Qt.ItemDataRole.UserRole)
        if entry is None:
            return
        self.fields["Type"].setText(f"{entry['type']}")
        self.fields["Group"].setText(f"{entry['group']}")
        self.fields["Instance"].setText(f"{entry['instance']}")
        self.fields["Size"].setText(f"{entry['size']}")
        self.fields["Offset"].setText(f"{entry['position']}")
        self.fields["Friendly Name"].setText(f"{entry['name']}")
        self.hex_spot.setPlainText(hex_dump(entry["data"]))
        # route to type-specific view (terrain for instance)

e_index_known = []
e_index_unknown = []
for entry in expanded_index:
    if entry["FriendlyName"]:
        e_index_known.append(entry)
    else:
        e_index_unknown.append(entry)

groups = {
    "Known": [(f'{e["FriendlyName"]}',f'{e["TypeID"]}', f'{e["GroupID"]}', f'{e["InstanceID"]}', e["Position"], e["FileSize"], raw_bytes[e["Position"]:e["Position"] + e["FileSize"]]) for e in e_index_known],
    "Unknown": [(f"-",f'{e["TypeID"]}', f'{e["GroupID"]}', f'{e["InstanceID"]}', e["Position"], e["FileSize"], raw_bytes[e["Position"]:e["Position"] + e["FileSize"]]) for e in e_index_unknown]}

app = QApplication(sys.argv)
win = MainWindow()
win.load_tree(groups)
win.show()
sys.exit(app.exec())
