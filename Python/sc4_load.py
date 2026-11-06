import os
import sys
import struct
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

IMPLEMENTED_TYPES = [
    "DirectoryFile",
    "TerrainMap"]

DBPF_HEADER_KEYS = [
    "identifier", "major_version", "minor_version", "user_major_version", "user_minor_version", "zero", "date_created", "date_modified", "index_major_version", "index_count", "index_offset", "index_size", "hole_count", "hole_offset", "hole_size", "index_minor_version", "index_offset_2", "unknown", "reserved1", "reserved2", "reserved3", "reserved4", "reserved5", "reserved6"]

DBPF_HEADER_FMT = "<4s23I" # 4 byte magic + 23 uint32s

def parse_file_header(data: bytes) -> dict:
    header = dict(zip(DBPF_HEADER_KEYS, struct.unpack_from(DBPF_HEADER_FMT, data)))
    if header["identifier"] != b"DBPF":
        raise ValueError(f"not a DBPF file (magic {header['identifier']!r})")
    return header

def parse_index(data:bytes, has_rId: bool) -> list[dict]:
    keys = ["type", "group", "instance"]
    if has_rId:
        keys.append("resource")
    keys += ["offset", "size"]

    fmt = f"<{len(keys)}I"
    return [{"resource": None, **dict(zip(keys, rec))} for rec in struct.iter_unpack(fmt, data)]

def parse_directory(data: bytes) -> dict:
    entries = [
        {"type": tId, "group": gId, "instance": iId, "size": d_size}
        for tId, gId, iId, d_size in struct.iter_unpack("<4I", data)]
    return {"Entries": entries}

def parse_data(data: bytes, t: str):
    print(f"Attempting to parse data of type: {t}")
    print(f"Payload size: {len(data)}")
    obj = {}

    # --- DIRECTORY DATA ---
    if t == "DirectoryFile":
        obj = parse_directory(data)

    # --- TERRAIN MAP DATA ---
    elif t == "TerrainMap":
        # Version (2 bytes)
        obj["Version"] = data[:2]
        # 2D array of Terrain Heights (Float32 - little endian)
        t_grid = []
        t_data = np.frombuffer(data[2:], dtype='<f4')
        grid_size = int(np.sqrt(len(t_data) - 2))

        print(f"TerrainData: Loaded {len(t_data)} points | Square {grid_size}")
        for i in range(0, grid_size):
            grid_row = []
            for j in range(0, grid_size):
                k = i + j * grid_size
                grid_row.append(t_data[k])
            t_grid.append(grid_row)

        obj["TerrainGrid"] = t_grid

    return obj

def make_kv_table(d: dict) -> QTableWidget:
    # Field | Value | Hex - for single records like the Header
    table = QTableWidget(len(d), 3)
    table.setHorizontalHeaderLabels(["Field", "Value", "Hex"])
    for r, (k, v) in enumerate(d.items()):
        table.setItem(r, 0, QTableWidgetItem(k))
        table.setItem(r, 1, QTableWidgetItem(str(v)))
        table.setItem(r, 2, QTableWidgetItem(f"0x{v:08X}" if isinstance(v, int) else ""))
    table.verticalHeader().setVisible(False)
    table.resizeColumnsToContents()
    return table

def make_records_table(records: list[dict], hex_keys=()) -> QTableWidget:
    # One row per record, one column per key - for index, directory, etc
    keys = list(records[0]) if records else []
    table = QTableWidget(len(records), len(keys))
    table.setHorizontalHeaderLabels(keys)
    for r, rec in enumerate(records):
        for c, k in enumerate(keys):
            v = rec[k]
            if k in hex_keys and isinstance(v, int):
                item = QTableWidgetItem(f"{v:08X}")
            else:
                item = QTableWidgetItem()
                item.setData(Qt.ItemDataRole.DisplayRole, v)
            table.setItem(r, c, item)
    table.resizeColumnsToContents()
    table.setSortingEnabled(True)
    return table

with open(f"{project_root}/tests/Files/{file_name}", "rb") as file:
    raw_bytes = file.read()

file_header = parse_file_header(raw_bytes)



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

    for x in range(dir_location, dir_location + dir_size, 16):
        known_type = ""
        typeID = hexString(raw_bytes, x, 4, True)
        groupID = hexString(raw_bytes, x+4, 4, True)
        instanceID = hexString(raw_bytes, x+8, 4, True)
        size = toU32(x+12)
        if typeID in INDEX_IDS:
            if INDEX_IDS[typeID][2]:
                known_type = INDEX_DEPTH[typeID][groupID][instanceID][0]
            else:
                known_type = INDEX_IDS[typeID][0]
        dir_entry = [known_type, typeID, groupID, instanceID, size]
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



#terrain_data_exists = False
#terrain_data_compressed = False
#terrain_data_position = 0
#terrain_data_size = 0
#terrain_grid_size = 0
#terrain_data = []
#terrain_grid = []
#
#for entry in expanded_index:
#    if entry["FriendlyName"] is "TerrainMap":
#        terrain_data_exists = True
#        terrain_data_compressed = entry["IsCompressed"]
#        terrain_data_position = entry["Position"]
#        terrain_data_size = entry["FileSize"]
#        print(f"{entry}")
#        print(f"")
#
#if terrain_data_exists:
#    print(f"TerrainData found - P: {terrain_data_position} S: {terrain_data_size}")
#    if terrain_data_compressed:
#        print(f"TerrainData is compressed")
#
#    else:
#        terrain_raw_data = raw_bytes[terrain_data_position+2:terrain_data_position + terrain_data_size]
#        # Header + 2 byte gap
#        trim_length = len(terrain_raw_data) - (len(terrain_raw_data) % 4)
#        print(f"Bytes: {len(terrain_raw_data)} | Trimmed: {len(terrain_raw_data) - trim_length}")
#        print(f"")
#        print(f"{terrain_raw_data[:20].hex(' ')}")
#        terrain_raw_data = terrain_raw_data[:trim_length]
#        terrain_data = np.frombuffer(terrain_raw_data, dtype='<f4')
#        print(f"")
#        terrain_grid_size = int(np.sqrt(len(terrain_data)))
#        print(f"Loaded {len(terrain_data)} points | Square {terrain_grid_size}")
#        for i in range(0, terrain_grid_size):
#            grid_row = []
#            for j in range(0, terrain_grid_size):
#                k = i + j * terrain_grid_size
#                grid_row.append(terrain_data[k])
#            terrain_grid.append(grid_row)
#

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
        print(f"Loaded TerrainMap!")

    def clear(self):
        self.viewer.clear()
        self.viewer.reset_camera()


# multiply = 0.0625
# offset = 0


# normalised_grid = NormaliseGrid(terrain_grid, multiply, offset)

# terrain_view = TerrainView(group)
# terrain_view.load_heightmap(normalised_grid)

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
        self.data_tab = QWidget()
        self.data_layout = QVBoxLayout(self.data_tab)
        self.views.addTab(self.data_tab, "Data")

        self.plotter = None
        if QtInteractor is not None:
            self.plotter = TerrainView(self.views)
            self.views.addTab(self.plotter.viewer.interactor, "3D")

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
        self.meta = {}
        for group_name, entries in groups.items():
            parent = QTreeWidgetItem(self.tree, [group_name, ""])
            if group_name in ("Header", "Index"):
                self.meta[group_name] = entries
                parent.setText(1, f"{len(entries[1])}")
                parent.setData(0, Qt.ItemDataRole.UserRole, {"kind": group_name})
                continue
            for name, type_id, group_id, instance_id, position, size, compressed, payload in entries:
                item = QTreeWidgetItem(parent, [name if group_name == "Known" else type_id, f"{size}"])
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    "kind": "Subfile",
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
        # clear 3D view when select changes
        self.plotter.clear()
        self.set_dataview(None)

        #
        if current is None:
            return
        entry = current.data(0, Qt.ItemDataRole.UserRole)
        if entry is None:
            return
        kind = entry.get("kind", "Subfile")
        if kind == "Header":
            return self.show_header()
        if kind == "Index":
            return self.show_index()
        t = entry['name']
        imp = False
        print(f"Checking if {t} is implemented...")
        if t in IMPLEMENTED_TYPES:
            print(f"{t} is an implemented type.")
            imp = True

        self.fields["Type"].setText(f"{t}")
        self.fields["Group"].setText(f"{entry['group']}")
        self.fields["Instance"].setText(f"{entry['instance']}")
        self.fields["Size"].setText(f"{entry['size']}")
        self.fields["Offset"].setText(f"{entry['position']}")
        self.fields["Friendly Name"].setText(f"{entry['name']}")
        self.fields["Implemented"].setText(f"{imp}")
        self.hex_spot.setPlainText(hex_dump(entry["data"]))
        # route to type-specific view (terrain for instance)
        if imp:
            data_obj = parse_data(entry['data'], t)
            self.update_dataview(t, data_obj)

    def update_dataview(self, t: str, obj):
        if t == "TerrainMap":
            print(f"Selected TerrainView data")
            grid = obj["TerrainGrid"]
            arr = np.array(grid, dtype=np.float64)

            # add to data tab
            dataview = QWidget()
            layout = QVBoxLayout(dataview)

            summary = QFormLayout()

            def add(label, value):
                val = QLabel(str(value))
                val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                summary.addRow(label, val)

            add("Version:", obj["Version"])
            add("Size:", f"{arr.shape[0]} x {arr.shape[1]}")
            add("Max:", f"{arr.max():2f}")
            add("Min", f"{arr.min():2f}")
            layout.addLayout(summary)

            # table of values

            table = QTableWidget(*arr.shape)
            for r in range(arr.shape[0]):
                for c in range(arr.shape[1]):
                    table.setItem(r, c, QTableWidgetItem(f"{arr[r, c]:.1f}"))
            table.resizeColumnsToContents()
            layout.addWidget(table, 1)

            self.set_dataview(dataview)

            # add values to 3D tab
            # sc4 scale factor (normalises the relative size of the grid to the heights)
            self.plotter.load_heightmap(arr * 0.0625)

        elif t == "DirectoryFile":
            entries = obj["Entries"]
            print(f"{entries[0]}")
            print(f"{entries[1]}")
            print(f"{entries[2]}")
            table = QTableWidget(len(entries),4)
            table.setHorizontalHeaderLabels(["Type","Group","Instance","Uncompressed"])
            for r, e in enumerate(entries):
                values = (f"{e['type']:08X}", f"{e['group']:08X}", f"{e['instance']:08X}", f"{e['size']:,}")
                for c, v in enumerate(values):
                    table.setItem(r, c, QTableWidgetItem(v))
            table.resizeColumnsToContents()
            table.setSortingEnabled(True)
            self.set_dataview(table)

    def set_dataview(self, widget):
        while self.data_layout.count():
            old = self.data_layout.takeAt(0).widget()
            if old is not None:
                old.deleteLater()
        if widget is not None:
            self.data_layout.addWidget(widget)

    def clear_fields(self):
        for lbl in self.fields.values():
            lbl.setText("-")

    def show_header(self):
        header, raw = self.meta["Header"]
        self.clear_fields()
        self.fields["Friendly Name"].setText("DBPF Header")
        self.fields["Offset"].setText(f"0")
        self.fields["Size"].setText(f"{len(raw)}")
        self.hex_spot.setPlainText(hex_dump(raw))
        self.set_dataview(make_kv_table(header))

    def show_index(self):
        index, raw = self.meta["Index"]
        header, _ = self.meta["Header"]
        self.clear_fields()
        self.fields["Friendly Name"].setText("DBPF Index")
        self.fields["Offset"].setText(f"{header['index_offset']}")
        self.fields["Size"].setText(f"{len(raw)}")
        self.hex_spot.setPlainText(hex_dump(raw))
        self.set_dataview(make_records_table(index, hex_keys={"type", "group", "instance", "resource"}))


e_index_known = []
e_index_unknown = []
for entry in expanded_index:
    if entry["FriendlyName"]:
        e_index_known.append(entry)
    else:
        e_index_unknown.append(entry)

start = file_header['index_offset']
index_raw = raw_bytes[start:start + file_header['index_size']]

groups = {
    "Header": (file_header, raw_bytes[:96]),
    "Index": (parse_index(index_raw, file_header["index_minor_version"] == 2), index_raw),
    "Known": [(f'{e["FriendlyName"]}',f'{e["TypeID"]}', f'{e["GroupID"]}', f'{e["InstanceID"]}', e["Position"], e["FileSize"], e["IsCompressed"], raw_bytes[e["Position"]:e["Position"] + e["FileSize"]]) for e in e_index_known],
    "Unknown": [(f"-",f'{e["TypeID"]}', f'{e["GroupID"]}', f'{e["InstanceID"]}', e["Position"], e["FileSize"], e["IsCompressed"], raw_bytes[e["Position"]:e["Position"] + e["FileSize"]]) for e in e_index_unknown]}

app = QApplication(sys.argv)
win = MainWindow()
win.load_tree(groups)
win.show()
sys.exit(app.exec())
