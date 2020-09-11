import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import mainapp
from matplotlib import pyplot as plt

# print('creating app')
app = QApplication(sys.argv)
# print('importing mainapp')
# print('initialise mainapp')
OM = mainapp.MainApp(app, sys.argv)

# List All Widget names (accessibleName)
print(OM.list_widgets())

# Modify a widget
OM.modify_widget('CLA-S02:CLA-S02-MAG-QUAD-01:k1l',1)

# Get screen indices for modifying plotting screen
OM.get_screen_indices()
# Set Screen name
OM.set_screen_name('CLA-C2V-MARK-01')
# Set Screen by index
OM.set_screen_index(6)

# Plot row 0 in the runs table
OM.plot_row(0)
# Find the id of a row
id = OM.get_id_for_row(0)
# Plot run_id
OM.plot_run_id(id)

# Get twiss table for row, at screen set above
OM.get_twiss_at_screen_for_row(0)
# Get twiss table for a specific z-position (by interpolation)
OM.get_twiss_at_zpos_for_row(0, 13.5)
# Get twiss table for all *plotted* rows
print(OM.get_twiss())

# Get slice plot data for given run table row
slicedata = OM.get_slice_data_for_row(0)

# Get beam plot data for given run table row
beamdata = OM.get_beam_data_for_row(0)
# Get SimFrame beamObject for given row
beam_object = OM.get_beam_object_for_row(0)
# Get beam objects for all *plotted* rows
beam_objects = OM.get_beam_objects()
# Get keys (run_id's) for the beam objects
keys = list(beam_objects.keys())

#Plot lines
lines = []
for k in keys:
    line, = plt.plot(beam_objects[keys[0]].t, beam_objects[keys[0]].cpz, '.', label=k, markersize=1)
    lines.append(line)
plt.legend(handles=lines, loc='upper right')
plt.grid()
plt.show()
