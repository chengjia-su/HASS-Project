from novaclient import client
from keystoneclient.auth.identity import v2
from novaclient import client
import logging

class Recovery (object):

    clusterList = {}
    
    def __init__ (self):        
        self.novaClient = client.Client(2, "admin", "pdclab!@#$", "admin", "http://10.52.52.50:5000/v2.0")
        
    def createCluster(self, clusterName):
        import uuid
        newClusterUuid = str(uuid.uuid4())
        newCluster = Cluster(uuid = newClusterUuid, name = clusterName)
        Recovery.clusterList[newClusterUuid] = newCluster
        return "0;"+newClusterUuid
            
    def deleteCluster(self, uuid):
        try:
            del Recovery.clusterList[uuid]
            logging.info("Recovery Recovery - The cluster %s is deleted." % uuid)
            return "0;The cluster %s is deleted." % uuid
        except:
            logging.info("Recovery Recovery - The cluster is not found (uuid = %s)." % uuid)
            return "1;The cluster is not found (uuid = %s)." % uuid
        
    def listCluster(self):
        result = []
        for uuid, cluster in Recovery.clusterList.iteritems() :
            result.append((uuid, cluster.name))
        return result
        
    def addNode(self, clusterId, nodeList):
        hypervisorList = self.novaClient.hypervisors.list()
        hostList = []
        for hypervisor in hypervisorList:
            hostList.append(str(hypervisor.hypervisor_hostname))
        
        notMatchNode = [nodeName for nodeName in nodeList if nodeName not in hostList]
        if not notMatchNode:
            try:
                Recovery.clusterList[clusterId].addNode(nodeList)
                logging.info("Recovery Recovery - The node %s is added to cluster." % ', '.join(str(node) for node in nodeList))
                return "0;The node %s is added to cluster." % ', '.join(str(node) for node in nodeList)
            except:
                logging.error("Recovery Recovery - Add node to cluster %s failed." % clusterId)
                return "1;Add node to cluster %s failed." % clusterId                
        else:
            logging.info("Recovery Recovery - The node is not found (name = %s)." % ', '.join(str(node) for node in notMatchNode))
            return "1;The node is not found (name = %s)." % ', '.join(str(node) for node in notMatchNode)
            
    def deleteNode(self, clusterId, nodeName):
        try:
            Recovery.clusterList[clusterId].deleteNode(nodeName)
            logging.info("Recovery Recovery - The node %s is deleted from cluster." % ', '.join(str(node) for node in nodeList))
            return "0;The node %s is deleted from cluster." % ', '.join(str(node) for node in nodeList)
        except:
            logging.error("Recovery Recovery - Delete node from cluster %s failed." % clusterId)
            return "1;Delete node from cluster %s failed." % clusterId      
#    def setDetector(self):
        
    
    
class Cluster(object):

    def __init__(self, uuid, name):
        self.id = id
        self.name = name
        self.nodeList = []
        self.instanceList = []

        
    def addNode(self, nodeList):
        self.nodeList.extend(nodeList)
        
    def deleteNode(self, nodeName):
        self.nodeList.remove(nodeName)
     