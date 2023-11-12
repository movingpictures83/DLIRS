from disk_struct import Disk
from collections import OrderedDict
from page_replacement_algorithm import page_replacement_algorithm

class CacheMetaData(object):
    def __init__(self):
        super(CacheMetaData, self).__setattr__("_isLir", False)
        super(CacheMetaData, self).__setattr__("_isResident", False)
        super(CacheMetaData, self).__setattr__("_isDemoted", False)

    @property
    def isLir(self):
        return self._isLir

    @isLir.setter
    def isLir(self, value):
        self._isLir = value

    @property
    def isResident(self):
        return self._isResident

    @isResident.setter
    def isResident(self, value):
        self._isResident = value

    @property
    def isDemoted(self):
        return self._isDemoted

    @isDemoted.setter
    def isDemoted(self, value):
        self._isDemoted = value

    def __setattr__(self, name, value):
        if not hasattr(self, name):
            raise AttributeError("Creating new attributes is not allowed!")
        super(CacheMetaData, self).__setattr__(name, value)



class DLIRS(page_replacement_algorithm):
    f3 = open('debugFile', 'w+')

    def __init__(self, cache_size):
        #assert 'cache_size' in param

        self.size = int(cache_size)
        if self.size < 10:
            self.size = 10
        print("size: %d" % self.size)
        self.hirsRatio = 0.01
        self.hirsSize = int(self.size*self.hirsRatio + 0.5)
        if self.hirsSize < 2:
            self.hirsSize = 2
        # print(self.hirsSize)

        self.lirsSize = self.size - self.hirsSize
        self.currentHIRSSize = 0
        self.currentLIRSSize = 0
        self.demotedBlocks = 0
        self.lirsStack = OrderedDict()
        self.hirStack = OrderedDict()
        self.residentHIRList = OrderedDict()
        self.nonresidentHIRsInStack = 0

    def __contains__(self, page):
        if page in self.lirsStack:
            return self.lirsStack[page].isResident
        elif page in self.residentHIRList:
            return True
        else:
            return False

    def request(self, page):
        assert self.currentHIRSSize + self.currentLIRSSize <= self.size
        test_size = (self.currentHIRSSize + self.currentLIRSSize
                + self.nonresidentHIRsInStack)
        assert (test_size) <= (self.size * 2), "size %d self.size: %d" % (test_size, self.size)
        assert len(self.lirsStack) <= 2*self.size, "true size %d" % len(self.lirsStack)

        # DLIRS.f3.write("_____________ page : <%d> _____________________\n" % page)
        # DLIRS.f3.write("lirs_size: %d hirs_size %d \n" % (self.lirsSize, self.hirsSize))
        # DLIRS.f3.write("size: lirs: %d hir: %d non_red: %d\n" % (self.currentLIRSSize, self.currentHIRSSize, self.nonresidentHIRsInStack))
        pageFault = False
        if page in self.lirsStack:
            if self.lirsStack[page].isLir:
                # self.f3.write("hirLIRinLIR\n")
                self.hitLIRInLIRS(page)
            else:
                # self.f3.write("hitInHIRInLIRStack\n")
                pageFault = not self.hitInHIRInLIRStack(page)
        elif page in self.residentHIRList:
            # self.f3.write("hitInHIRList\n")
            self.hitInHIRList(page)
        else:
            # self.f3.write("processMiss\n")
            self.processMiss(page)
            pageFault = True
        #self.print_stack()
        return pageFault

    def hitLIRInLIRS(self, page):
        first_page = next(iter(self.lirsStack))

        page_obj = self.lirsStack[page]
        del self.lirsStack[page]

        self.lirsStack[page] = page_obj

        if first_page == page:
            # self.f3.write("PRUNE !!")
            self.pruneStack()

    def pruneStack(self):
        lirsKeys = []
        hirsKeys = []
        for key in self.lirsStack:
            data = self.lirsStack[key]
            if data.isLir:
                break
            #del self.lirsStack[key]
            lirsKeys.append(key)

            if key in self.hirStack:
                hirsKeys.append(key)
                #del self.hirStack[key]
            else:
                # self.f3.write("assert key in self.residentHIRList")
                assert key in self.residentHIRList, "key is %d" % key

            if not data.isResident:
                self.nonresidentHIRsInStack-= 1
        for key in lirsKeys:
            del self.lirsStack[key]
        for key in hirsKeys:
            del self.hirStack[key]
            # DLIRS.f3.write(
            #     "DEL <%d> red: <%r> lir: <%r> demoted: <%r>\n" % (key, data.isResident, data.isLir, data.isDemoted))

    def hitInHIRInLIRStack(self, page):
        page_obj = self.lirsStack[page]
        result = page_obj.isResident

        page_obj.isLir = True

        del self.lirsStack[page]
        del self.hirStack[page]

        if result:
            del self.residentHIRList[page]
            self.currentHIRSSize -= 1
        else:
            self.adjustSize(True)
            page_obj.isResident = True
            self.nonresidentHIRsInStack -= 1

        while self.currentLIRSSize >= self.lirsSize:
            self.ejectLIR()

        while self.currentHIRSSize + self.currentLIRSSize >= self.size:
            self.ejectResidentHIR()

        self.lirsStack[page] = page_obj
        self.currentLIRSSize += 1

        return result

    def ejectLIR(self):
        first_key = next(iter(self.lirsStack))

        tmpData = self.lirsStack[first_key]
        tmpData.isLir = False
        del self.lirsStack[first_key]

        self.currentLIRSSize -= 1
        tmpData.isDemoted = True
        self.demotedBlocks += 1

        self.residentHIRList[first_key] = tmpData
        self.currentHIRSSize += 1
        self.pruneStack()

    def ejectResidentHIR(self):
        first_page_key = next(iter(self.residentHIRList))
        first_page = self.residentHIRList[first_page_key]
        del self.residentHIRList[first_page_key]

        if first_page_key in self.lirsStack:
            page_lir = self.lirsStack[first_page_key]
            page_lir.isResident = False
            self.nonresidentHIRsInStack += 1
        if first_page.isDemoted:
            first_page.isDemoted = False  # hmm
            self.demotedBlocks -= 1
        self.currentHIRSSize -= 1

    def hitInHIRList(self, page):
        page_obj = self.residentHIRList[page]
        if page_obj.isDemoted:
            self.adjustSize(False)
            page_obj.isDemoted = False
            self.demotedBlocks -= 1

        del self.residentHIRList[page]

        self.residentHIRList[page] = page_obj
        self.lirsStack[page] = page_obj
        self.hirStack[page] = page_obj
        self.limitStackSize()

    def limitStackSize(self):
        #pruneSize = (self.currentHIRSSize + self.currentLIRSSize + self.nonresidentHIRsInStack) - self.size*2
        pruneSize = (self.currentHIRSSize + self.currentLIRSSize + self.nonresidentHIRsInStack) - self.size * 2
        DLIRS.f3.write("prune_size: %d\n" % pruneSize)

        pruneKeys = []
        for key in self.hirStack:
            if pruneSize <= 0:
                break
            data = self.lirsStack[key]
            DLIRS.f3.write("removing: %d\n" % key)
            pruneKeys.append(key)
            #del self.lirsStack[key]
            #del self.hirStack[key]

            if not data.isResident:
                self.nonresidentHIRsInStack -= 1

            pruneSize -= 1
        for key in pruneKeys:
            del self.lirsStack[key]
            del self.hirStack[key]

    def limitStackSize2(self):
        pruneSize = self.nonresidentHIRsInStack - self.size
        pruneKeys = []
        for key in self.hirStack:
            if pruneSize <= 0:
                break
            data = self.lirsStack[key]
            if data.isResident:
                continue

            self.nonresidentHIRsInStack -= 1
            #del self.lirsStack[key]
            #del self.hirStack[key]
            pruneKeys.append(key)
            pruneSize -= 1
        for key in pruneKeys:
            del self.lirsStack[key]
            del self.hirStack[key]


    def processMiss(self, page):
        if self.currentLIRSSize < self.lirsSize and self.currentHIRSSize == 0:
            data = CacheMetaData()
            data.isLir = True
            data.isResident = True
            self.lirsStack[page] = data
            self.currentLIRSSize += 1
            return
        else:
            while self.currentHIRSSize + self.currentLIRSSize >= self.size:
                while self.currentLIRSSize > self.lirsSize:
                    self.ejectLIR()
                if len(self.residentHIRList) == 0:
                    break
                self.ejectResidentHIR()

        data = CacheMetaData()
        data.isLir = False
        data.isResident = True

        self.lirsStack[page] = data
        self.hirStack[page] = data
        self.residentHIRList[page] = data

        self.currentHIRSSize += 1
        self.limitStackSize()

    def adjustSize(self, hitHir):
        if hitHir:
            if self.nonresidentHIRsInStack > self.demotedBlocks:
                delta = 1
            else:
                delta = int((float(self.demotedBlocks) / float(self.nonresidentHIRsInStack) + 0.5))
        else:
            if self.demotedBlocks > self.nonresidentHIRsInStack:
                delta = -1
            else:
                delta = -int((float(self.nonresidentHIRsInStack) / float(self.demotedBlocks) + 0.5))

        self.hirsSize += delta

        if self.hirsSize < 1:
            self.hirsSize = 1
        if self.hirsSize > self.size - 1:
            self.hirsSize = self.size - 1
        self.lirsSize = self.size - self.hirsSize


    # def print_stack(self):
    #     DLIRS.f3.write("LIR stack:\n")
    #     for key in self.lirsStack:
    #         data = self.lirsStack[key]
    #         DLIRS.f3.write("LIR <%d> red: <%r> lir: <%r> demoted: <%r>\n" % (key, data.isResident, data.isLir, data.isDemoted))
    #
    #     DLIRS.f3.write("\n\nHIR stack:\n")
    #     for key in self.hirStack:
    #         data = self.hirStack[key]
    #         DLIRS.f3.write("HIR <%d> red: <%r> lir: <%r> demoted: <%r>\n" % (key, data.isResident, data.isLir, data.isDemoted))
    #
    #     DLIRS.f3.write("\n\nresidentHIRList stack:\n")
    #     for key in self.residentHIRList:
    #         data = self.residentHIRList[key]
    #         DLIRS.f3.write("redHIR <%d> red: <%r> lir: <%r> demoted: <%r>\n" % (key, data.isResident, data.isLir, data.isDemoted))
    #     DLIRS.f3.write("\n\n")

    def get_N(self):
        return self.size

    def __del__(self):
        #DLIRS.f3.close()
        print('Closing file')


    def get_list_labels(self):
        return ['L']

    def delete(self, page):
        DLIRS.f3.write("_____Delete %d _____\n" % page)
        DLIRS.f3.write("lirs_size: %d hirs_size %d \n" % (self.lirsSize, self.hirsSize))
        DLIRS.f3.write("size: lirs: %d hir: %d non_red: %d\n" % (self.currentLIRSSize, self.currentHIRSSize, self.nonresidentHIRsInStack))
        if page in self.lirsStack:
            if self.lirsStack[page].isLir:
                # Lirs2.f3.write("delete lir\n")
                self.deleteLIRpage(page)
            else:
                # Lirs2.f3.write("delete hir in lirs\n")
                self.deleteHIRInLIRStack(page)
        elif page in self.residentHIRList:
            # Lirs2.f3.write("delete red\n")
            self.deleteResidentHIR(page)
        else:
            raise KeyError("Page not in cache")
        # Lirs2.f3.write("print stack: \n")
        self.limitStackSize2()
        #self.print_stack()

    def deleteLIRpage(self, page):
        del self.lirsStack[page]  # NBW

        if self.currentHIRSSize > 1:
            #assert self.currentLIRSSize == self.lirsSize
            self.forceHIRtoLIR()

        self.currentLIRSSize -= 1

        self.pruneStack()

    def forceHIRtoLIR(self):
        firstKey = next(iter(self.residentHIRList))
        firstHIRdata = self.residentHIRList[firstKey]

        # Lirs2.f3.write("\nFirstkey: %d\n" % firstKey)
        # print("__________________________________________________BOE")
        del self.residentHIRList[firstKey]

        firstHIRdata.isLir = True
        firstHIRdata.isResident = True

        if firstKey in self.lirsStack:
            assert firstKey in self.hirStack

            del self.hirStack[firstKey]
            self.lirsStack[firstKey] = firstHIRdata

        else:
            self.ordered_dict_prepend(self.lirsStack, firstKey, firstHIRdata)

        self.currentLIRSSize += 1
        self.currentHIRSSize -= 1

        # Lirs2.f3.write("\nis LIR %r\n" % self.lirStack[firstKey].isLIR)

    def deleteHIRInLIRStack(self, page):
        data = self.lirsStack[page]
        result = data.isResident

        if result:
            del self.residentHIRList[page]
            self.currentHIRSSize -= 1
        else:
            raise KeyError("Page not in cache")

        data.isResident = False
        assert self.hirStack[page].isResident == False

        self.nonresidentHIRsInStack += 1

    def deleteResidentHIR(self, page):
        del self.residentHIRList[page]
        if page in self.lirsStack:
            tmpData = self.lirsStack[page]
            tmpData.isResident = False

            assert self.lirsStack[page].isResident == False
            assert page in self.hirStack
            assert self.hirStack[page].isResident == False

            self.nonresidentHIRsInStack += 1
        self.currentHIRSSize -= 1

    def ordered_dict_prepend(self, dct, key, value, dict_setitem=dict.__setitem__):
        dct[key] = value
        dct.move_to_end(key, last=False)
        #root = dct.__root
        #first = root[1]

        #if key in dct:
        #    link = dct._OrderedDict__map[key]
        #    link_prev, link_next, _ = link
        #    link_prev[1] = link_next
        #    link_next[0] = link_prev
        #    link[0] = root
        #    link[1] = first
        #    root[1] = first[0] = link
        #else:
        #    root[1] = first[0] = dct._OrderedDict__map[key] = [root, first, key]
        #    dict_setitem(dct, key, value)


if __name__ == "__main__":
    params = {'cache_size': 10}
    alg = DLIRS(params)
    total_pg_refs = 0
    num_pg_fl = 0

    f = open('m.txt', 'r')
    last_ref_block = -1
    for line in f:
        try:
            ref_block = int(line)
        except:
            continue
        total_pg_refs += 1
        if ref_block == last_ref_block:
            continue
        else:
            last_ref_block = ref_block

        pg_fl = alg.request(ref_block)#pageRequest(ref_block)

        if pg_fl:
            num_pg_fl += 1
    #alg.print_stack()
    print(total_pg_refs)
    print(num_pg_fl)
    print(1.0 - num_pg_fl / total_pg_refs)
