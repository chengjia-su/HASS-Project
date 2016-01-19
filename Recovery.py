from novaclient import client
from keystoneclient.auth.identity import v2
import logging
import ConfigParser

from DetectionManager import DetectionManager

class Recovery (object):

    clusterList = {}

    def __init__ (self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('hass.conf')
        
        self.novaClient = client.Client(2, self.config.get("openstack", "openstack_admin_account"), self.config.get("openstack", "openstack_admin_password"), self.config.get("openstack", "openstack_admin_account"), "http://controller:5000/v2.0")
        hypervisorList = self.novaClient.hypervisors.list()
        self.hostList = []
        for hypervisor in hypervisorList:
            self.hostList.append(str(hypervisor.hypervisor_hostname))
        
        
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
        
        notMatchNode = [nodeName for nodeName in nodeList if nodeName not in self.hostList]
        if not notMatchNode:
            try:
                Recovery.clusterList[clusterId].addNode(nodeList)
                logging.info("Recovery Recovery - The node %s is added to cluster." % ', '.join(str(node) for node in nodeList))
                self.hostList = [nodeName for nodeName in self.hostList if nodeName not in nodeList]
                return "0;The node %s is added to cluster." % ', '.join(str(node) for node in nodeList)
            except:
                logging.info("Recovery Recovery - The cluster is not found (uuid = %s)." % clusterId)
                return "1;The cluster is not found (uuid = %s)." % clusterId                
        else:
            logging.info("Recovery Recovery - The node is not found (name = %s)." % ', '.join(str(node) for node in notMatchNode))
            return "1;The node is not found (name = %s)." % ', '.join(str(node) for node in notMatchNode)
            
    def deleteNode(self, clusterId, nodeName):
        try:
            Recovery.clusterList[clusterId].deleteNode(nodeName)
            logging.info("Recovery Recovery - The node %s is deleted from cluster." % nodeName)
            return "0;The node %s is deleted from cluster." % nodeName
        except:
            logging.info("Recovery Recovery - Delete node from cluster failed. The cluster is not found. (uuid = %s)" % clusterId)
            return "1;Delete node from cluster failed. The cluster is not found. (uuid = %s)" % clusterId

    def listNode(self, clusterId):
        try:
            nodeList = Recovery.clusterList[clusterId].getNode()
            return "0;"+nodeList
        except:
            return "1;The cluster is not found. (uuid = %s)" % clusterId
            
    def addInstance(self, clusterId, instanceId):
        if self.novaClient.volumes.get_server_volumes(instanceId) == [] :
            logging.info("Recovery Recovery - The instance can not be protected. (No volume)")
            return "1;The instance can not be protected. (No volume)"
        #else :
    def recoveryNode(self, clusterId, nodeName):
        print "Recovery"       
    
class Cluster(object):

    def __init__(self, uuid, name):
        self.id = id
        self.name = name
        self.nodeList = []
        self.instanceList = []
        self.detect = DetectionManager()
        
    def addNode(self, nodeList):
        for node in nodeList :
            self.detect.pollingRegister(self.id, node)
        self.nodeList.extend(nodeList)
        
    def deleteNode(self, nodeName):
        self.detect.pollingCancel(self.id, nodeName)
        self.nodeList.remove(nodeName)
    
    def getNode(self):
        nodeStr = ','.join(self.nodeList)
        return nodeStr
     