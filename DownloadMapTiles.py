import sys
import subprocess
import os
import os.path
import uuid
from pathlib import Path
import signal
from threading import Thread


#Note: it's prudent to run this at least twice on the same data, to get anything that might've been missed. It's not perfect.


#Set following to your heart's desire. I've set it to, more or less, Cascadia and surroundings; or, everything I'm willing to drive to.
xs = 19
xe = 23
ys = 43
ye = 49
zs = 7

#Each entry is a map name, an extension, one past end of finest zoom level, and a base url. Hopefully won't need frequent updating. F12->Network helps get the links.
sources = [
	["USFS2016",   ".png", 16, "https://ctusfs.s3.amazonaws.com/2016a/"],
	["USFS2013",   ".png", 16, "https://ctusfs.s3.amazonaws.com/fstopo/"],
	["OSM",        ".png", 16, "https://b.tile.openstreetmap.org/"],
]


#Ideally no need to muck around after this point.
print("The following sources are available:")
for i in range(0, len(sources)):
	print(" " + str(i) + ": " + sources[i][0])
print("")

sourceID = int(input("Type the index of the one you want to download from: "))

name = sources[sourceID][0]
ext  = sources[sourceID][1]
ze   = sources[sourceID][2]
base = sources[sourceID][3]

print("Selected " + name)
print("")

#This uses aria2 on a whole column (instead of wget on individual files). Works faster this way.
#Create a guaranteed unique name for the temp file, so that concurrent runs of this won't conflict.
tempfilename = "temp_" + str(uuid.uuid4()) + ".txt"

def GetTiles(x, ys, ye, z, dstdir):
	#Dump list of files to download into a text file.
	f = open(tempfilename, "w")

	for y in range(ys, ye):
		filename = str(y) + ext

		#aria2 does an integrity check, or something such. I don't know. Let's just use Python to see if file exists, and skip if so.
		if(os.path.isfile(dstdir + filename)):
			continue

		url = base + str(z) + '/' + str(x) + '/' + filename
		f.write(url + "\n")

	f.close()

	#Ask aria2 to get them. os.system(cmd) is easier, but results in aria2 catching signals, which I don't want.
	#See https://stackoverflow.com/questions/5045771/python-how-to-prevent-subprocesses-from-receiving-ctrl-c-control-c-sigint
	cmd = "aria2c --auto-file-renaming=false --continue=false --dir " + dstdir + " --input-file=" + tempfilename

#	p = subprocess.Popen(cmd, preexec_fn=os.setpgrp)		#Anything but Windows. Untested.
	p = subprocess.Popen(cmd, creationflags=0x00000200)		#Windows only.
	p.wait()


#Put facility to catch Ctrl C in place, so that if pressed it will wait for current downloads to finish before quitting. Doesn't print feedback, unfortunately, just wait and it'll quit.
#It seems like what happens, in Windows at least, is that the main thread doesn't recieve Ctrl C until the running subprocess (in GetTiles) finishes.
def CtrlCHandler(signum = [], frame = []):
	os.remove(tempfilename)
	sys.exit()

signal.signal(signal.SIGINT, CtrlCHandler)


#Loop from coarsest to finest zoom.
for z in range(zs, ze):
	for x in range(xs, xe):
		#Make directory.
		dstdir = ".\\Imagery\\" + name + "\\" + str(z) + '\\' + str(x) + '\\'
		os.system("mkdir " + dstdir)

		GetTiles(x, ys, ye, z, dstdir)

	#At the end of every zoom level, get correct extents for next zoom by doubling starts and doubling the widths.
	xe = 2*xs + (xe - xs)*2
	xs = 2*xs
	ye = 2*ys + (ye - ys)*2
	ys = 2*ys


#Use this as cleanup in the event of normal exit.
CtrlCHandler()







