from DetectionManager import DetectionManager

class Cluster(object):

    def __init__(self, uuid, name):
        self.id = uuid
        self.name = name
        self.nodeList = []
        self.instanceList = []
        self.detect = DetectionManager()
        
    def addNode(self, nodeList, test=False):
        if test == False:
            for node in nodeList :
                self.detect.pollingRegister(self.id, node)
        self.nodeList.extend(nodeList)
        
    def deleteNode(self, nodeName, test=False):
        if test == False:
            self.detect.pollingCancel(self.id, nodeName)
        self.nodeList.remove(nodeName)
        self.instanceList = [instance for instance in self.instanceList if instance[1]!=nodeName]
    
    def getNode(self):
        nodeStr = ','.join(self.nodeList)
        return nodeStr
    
    def addInstance(self, id, node):
        self.instanceList.append([id, node])
        
    def deleteInstance(self, instance):
        self.instanceList.remove(instance)
        
    def getInstance(self):
        instanceStr = ",".join("%s:%s" % (instance[0],instance[1]) for instance in self.instanceList)
        return instanceStr
        