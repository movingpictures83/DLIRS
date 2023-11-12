import random
import sys
from disk_struct import Disk
from page_replacement_algorithm import  page_replacement_algorithm
import numpy as np

import DLIRS
import DLIRS_adaptive
import dlirslecar4lfu

import PyIO
import PyPluMA

class DLIRSPlugin:
  def input(self, inputfile):
        self.parameters = PyIO.readParameters(inputfile)

  def run(self):
        pass

  def output(self, outputfile):
    n = int(self.parameters["n"])
    infile = open(PyPluMA.prefix()+"/"+self.parameters["infile"], 'r')
    kind = self.parameters["kind"]
    outfile = open(outputfile, 'w')
    outfile.write("cache size "+str(n))
    if (kind == "DLIRS"):
       dlirs = DLIRS.DLIRS(n)
    elif (kind == "DLIRS_adaptive"):
       dlirs = DLIRS_adaptive.DLIRS(n)
    else:
       dlirs = dlirslecar4lfu.dlirslecar4lfu(n)
    page_fault_count = 0
    page_count = 0
    for line in infile:
        line = int(line.strip())
        outfile.write("request: "+str(line))
        if dlirs.request(line) :
            page_fault_count += 1
        page_count += 1

    
    outfile.write("page count = "+str(page_count))
    outfile.write("\n")
    outfile.write("page faults = "+str(page_fault_count))
    outfile.write("\n")
