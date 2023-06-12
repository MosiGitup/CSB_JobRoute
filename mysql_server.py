from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtWidgets import *
from qgis.analysis import QgsNativeAlgorithms
import os, sys, shutil
import schedule, time
import subprocess

# Initialize QGIS application
QgsApplication.setPrefixPath("/usr/bin/qgis.bin", True)
qgs = QgsApplication([], False)
qgs.initQgis()

# Set the application path
qgs.setPluginPath('/usr/lib/qgis/plugins')
sys.path.append('/usr/share/qgis/python/plugins')

# Import processing modules
import processing
from processing.core.Processing import Processing
from qgis.server import *

Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

QgsProject.instance().removeAllMapLayers()

## *** Running project
project_path = sys.argv[1]
project = QgsProject.instance()

## *** Mysql connection
mydb = sys.argv[2]
host_name = sys.argv[3]
host_port = sys.argv[4]
host_user = sys.argv[5]
host_pass = sys.argv[6]
host_layername = sys.argv[7]
uri = "MySQL:" + mydb + ",host=" + host_name + ",port=" + host_port + ",user=" + host_user + ",password=" + host_pass + "|layername=" + host_layername + ""
vlayer = QgsVectorLayer(uri, "Jobs", "ogr")

## *** Create directory
seconds = time.time()
yr_mon_day = time.localtime(seconds)
pro_dir = 'JobRoute_' + str(yr_mon_day.tm_year) + str(yr_mon_day.tm_mon) + str(yr_mon_day.tm_mday) + '-' + str(yr_mon_day.tm_hour) + 'h' + str(yr_mon_day.tm_min)
path = os.path.join(project_path, pro_dir)
try:
    os.mkdir(path)
except:
    print('')

## *** Extract by Attribute
output1 = 'serJob.shp'
jobId = 0
processing.run("qgis:extractbyattribute", {
    'INPUT': vlayer,
    'FIELD': 'id',
    'OPERATOR': 2,
    'VALUE': jobId,
    'OUTPUT': project_path + pro_dir + '/' + output1})

linestring_layer = QgsVectorLayer(project_path + pro_dir + '/' + output1, output1[:-4], "ogr")
if linestring_layer.isValid():
    QgsProject.instance().addMapLayer(linestring_layer)
else:
    print('Error: Failed to load vector layer')
extent = linestring_layer.extent()
xmin = extent.xMinimum()
xmax = extent.xMaximum()
ymin = extent.yMinimum()
ymax = extent.yMaximum()
layer_id = linestring_layer.id()

## *** Save the project
project_name = "JobRoute_server.qgs"
project.writeEntry("WMSServiceCapabilities", "/", "True")
project.writeEntry("WMSServiceTitle", "/", "Raster maps")
project.writeEntry("WMSContactOrganization", "/", "CIDCO")
project.writeEntry("WMSOnlineResource", "/", "www.cidco.ca")
project.writeEntry("WMSContactPerson", "/", "Mosi")
project.writeEntry("WMSContactMail", "/", "mohsen.feizabadi@cidco.ca")
project.writeEntry("WMSContactOrganization", "/", "CIDCO")

project.writeEntry("WMSExtent", "/", [str(xmin), str(ymin), str(xmax), str(ymax)])
project.writeEntry("WMSEpsgList", "/", "4326")
project.writeEntry("WMSCrsList", "/", "EPSG:4326")

project.writeEntry("WMTSLayers", "Project", True)
project.writeEntry("WMTSPngLayers", "Project", True)
project.writeEntry("WMTSJpegLayers", "Project", True)

project.writeEntry("WMTSLayers", "Layer", [layer_id])
project.writeEntry("WMTSPngLayers", "Layer", [layer_id])
project.writeEntry("WMTSJpegLayers", "Layer", [layer_id])

project.writeEntry("WFSLayers", "/", [layer_id])
project.writeEntry("WFSTLayers", "Update", [layer_id])
project.writeEntry("WFSTLayers", "Insert", [layer_id])
project.writeEntry("WFSTLayers", "Delete", [layer_id])
for j in layer_id.split():
    project.writeEntry("WFSLayersPrecision", "/" + j, 5)
project.write(project_path + pro_dir + '/' + project_name)

## *** Showing the execution time
exe_time = time.ctime(seconds)
print('')
print('\033[0;0mExecute time:', exe_time, '\n')

## *** Sending to server
local_dir_path = project_path + pro_dir + '/'
remote_dir_path = sys.argv[8]
dir_name = sys.argv[9]

remote_password = sys.argv[10]

for file_name in os.listdir(local_dir_path):
    print(remote_dir_path + file_name)
    source = local_dir_path + file_name
    destination = remote_dir_path + file_name
    if os.path.isfile(source):
        shutil.copy(source, destination)

## *** Running bash file in server
sh_file_path = sys.argv[11]
command = f"sh {sh_file_path} {dir_name} {remote_dir_path}"
process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           shell=True, universal_newlines=True)
process.stdin.write(remote_password + '\n')
process.stdin.flush()
result = process.communicate()[0]
print('')
print(f'\033[1;34m{result}')
