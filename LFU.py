import sys
from page_replacement_algorithm import  page_replacement_algorithm
from disk_struct import Disk
from priorityqueue import priorityqueue
import numpy as np

# sys.path.append(os.path.abspath("/home/giuseppe/))

## Keep a LRU list.
## Page hits:
##      Every time we get a page hit, mark the page and also move it to the MRU position
## Page faults:
##      Evict an unmark page with the probability proportional to its position in the LRU list.
class LFU(page_replacement_algorithm):

    def __init__(self, n):
        
        self.N = n
        if self.N < 4:
             self.N = 4
        self.PQ = priorityqueue(self.N)
        
        self.unique = {}
        self.unique_cnt = 0
        self.pollution_dat_x = []
        self.pollution_dat_y = []
        self.time = 0
        self.reused_block_count = 0
        self.page_entering_cache = {}
        self.unique_block_count = 0
        self.block_reused_duration = 0
        self.page_lifetime_cache = {}
        self.block_lifetime_duration = 0
        self.block_lifetime_durations = []

    def get_N(self) :
        return self.N
    
    
    def __contains__(self, q):
        return q in self.PQ
    
    def visualize(self, ax):
        pass
    
    def getWeights(self):
#         return np.array([self. X, self.Y1, self.Y2,self.pollution_dat_x,self.pollution_dat_y ]).T
        return np.array([self.pollution_dat_x,self.pollution_dat_y ]).T
    
    def get_block_reused_duration(self):
        return self.block_reused_duration 

    def get_block_lifetime_duration(self):
        for pg in self.PQ.getData():
            self.block_lifetime_duration +=  self.time - self.page_lifetime_cache[pg]
            self.unique_block_count += 1
            self.block_lifetime_durations.append(self.time - self.page_lifetime_cache[pg])
        print("Unique no of blocks", self.unique_block_count )
        return self.block_lifetime_duration/ float(self.unique_block_count)
    
    def get_block_lifetime_durations(self):
        return self.block_lifetime_durations
    
    def getStats(self):
        d={}
        d['pollution'] = np.array([self.pollution_dat_x, self.pollution_dat_y ]).T
        return d
    
    def request(self,page) :
        page_fault = False
        self.time = self.time + 1
        
        if page in self.PQ :
#         if self.PQ.contain(page) :
            page_fault = False
            self.PQ.increase(page)
        else :
            print("New page", page)
            if self.PQ.size() == self.N :
                ## Remove LRU page
                evicted = self.PQ.popmin()
                # print( "Evicted Page",evicted)
                self.block_lifetime_duration +=  self.time - self.page_lifetime_cache[evicted]
                self.unique_block_count += 1
                self.block_lifetime_durations.append(self.time - self.page_lifetime_cache[evicted])
                # print( "Page", cacheevict, "Lifetime", self.page_lifetime_cache[cacheevict],"At time", self.time, "Duration", self.time - self.page_lifetime_cache[cacheevict], "Block in Cache count", self.unique_block_count  )
                del self.page_lifetime_cache[evicted] 
              
            self.PQ.add(int(page))
            self.page_lifetime_cache[page] = self.time
            page_fault = True
        
        if not page_fault and page in self.page_entering_cache :
                self.block_reused_duration +=  self.time - self.page_entering_cache[page]
                self.reused_block_count += 1
                self.page_entering_cache[page] =  self.time 

        else:
            self.page_entering_cache[page] =  self.time
        if page_fault :
            self.unique_cnt += 1
        
        self.unique[page] = self.unique_cnt
#         
#         if self.time % self.N == 0:
#             pollution = 0
#             for pg in self.PQ.getData():
#                 if self.unique_cnt - self.unique[pg] >= 2*self.N:
#                     pollution += 1
#             self.pollution_dat_x.append(self.time)
#             self.pollution_dat_y.append(100*pollution / self.N)
#         
        return page_fault


    def get_data(self):
        return [list(self.freq)]

    def get_list_labels(self) :
        return ['L']


