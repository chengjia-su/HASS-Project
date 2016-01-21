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
        result = {"code": "0", "clusterId":newClusterUuid, "message":""}
        return result
            
    def deleteCluster(self, uuid):
        code = ""
        message = ""
        try:
            del Recovery.clusterList[uuid]
            logging.info("Recovery Recovery - The cluster %s is deleted." % uuid)
            code = "0"
            message = "The cluster %s is deleted." % uuid
        except:
            logging.info("Recovery Recovery - The cluster is not found (uuid = %s)." % uuid)
            code = "1"
            message = "The cluster is not found (uuid = %s)." % uuid
        finally:
            result = {"code": code, "clusterId":uuid, "message":message}
            return result
        
    def listCluster(self):
        result = []
        for uuid, cluster in Recovery.clusterList.iteritems() :
            result.append((uuid, cluster.name))
        return result
        
    def addNode(self, clusterId, nodeList):
        code = ""
        message = ""
        notMatchNode = [nodeName for nodeName in nodeList if nodeName not in self.hostList]
        if not notMatchNode:
            try:
                Recovery.clusterList[clusterId].addNode(nodeList)
                logging.info("Recovery Recovery - The node %s is added to cluster." % ', '.join(str(node) for node in nodeList))
                self.hostList = [nodeName for nodeName in self.hostList if nodeName not in nodeList]
                code = "0"
                message = "The node %s is added to cluster." % ', '.join(str(node) for node in nodeList)
            except:
                logging.info("Recovery Recovery - The cluster is not found (uuid = %s)." % clusterId)
                code = "1"
                message = "The cluster is not found (uuid = %s)." % clusterId
            finally:
                result = {"code":code, "clusterId":clusterId, "message":message}
                return result
        else:
            logging.info("Recovery Recovery - The node is not found (name = %s)." % ', '.join(str(node) for node in notMatchNode))
            message = "The node is not found (name = %s)." % ', '.join(str(node) for node in notMatchNode)
            code = "1"
            result = {"code":code, "clusterId":clusterId, "message":message}
            return result
            
    def deleteNode(self, clusterId, nodeName):
        code = ""
        message = ""
        try:
            Recovery.clusterList[clusterId].deleteNode(nodeName)
            logging.info("Recovery Recovery - The node %s is deleted from cluster." % nodeName)
            code = "0"
            message = "The node %s is deleted from cluster." % nodeName
        except:
            logging.info("Recovery Recovery - Delete node from cluster failed. The cluster is not found. (uuid = %s)" % clusterId)
            code = "1"
            message = "Delete node from cluster failed. The cluster is not found. (uuid = %s)" % clusterId
        finally:
            result = {"code": code, "clusterId":clusterId, "message":message}
            return result

    def listNode(self, clusterId):
        code = ""
        message = ""
        try:
            nodeList = Recovery.clusterList[clusterId].getNode()
            code = "0"
            message = "Success"
        except:
            code = "1"
            message = "The cluster is not found. (uuid = %s)" % clusterId
        finally:
            result = {"code": code, "nodeList":nodeList, "message":message}
            return result
            
    def addInstance(self, clusterId, instanceId):
        code = ""
        message = ""
        if [instance for instance in Recovery.clusterList[clusterId].instanceList if instance[0]==id] != [] :
            logging.info("Recovery Recovery - The instance %s already be protected." % instanceId)
            code = "1"
            message = "The instance %s already be protected." % instanceId
        elif self.novaClient.volumes.get_server_volumes(instanceId) == [] :
            logging.info("Recovery Recovery - The instance %s can not be protected. (No volume)" % instanceId)
            code = "1"
            message = "The instance %s can not be protected. (No volume)" % instanceId
        else:
            vm = self.novaClient.servers.get(instanceId)
            host = getattr(vm,"OS-EXT-SRV-ATTR:host")
            if host in Recovery.clusterList[clusterId].nodeList :
                Recovery.clusterList[clusterId].addInstance(instanceId, host)
                code = "0"
                message = "The instance %s is protected." % instanceId
            else:
                from Schedule import Schedule
                try:
                    target_host = Schedule.default(Recovery.clusterList[clusterId].nodeList)
                    vm.live_migrate(host = target_host)
                    Recovery.clusterList[clusterId].addInstance(instanceId, host)
                    code = "0"
                    message = "The instance %s is migrated to host:%s and protected." % (instanceId, target_host)
                except:
                    code = "1"
                    message = "The instance %s can not be protected. (Migrate to HA cluster failed)" % instanceId
        result = {"code": code, "clusterId":clusterId, "message":message}
        return result
        
    def deleteInstance(self, clusterId, instanceId):
        code = ""
        message = ""
        try:
            instance = [instance for instance in Recovery.clusterList[clusterId].instanceList if instance[0]==id]
        except:
            logging.info("Recovery Recovery - Delete node from cluster failed. The cluster is not found. (uuid = %s)" % clusterId)
            code = "1"
            message = "Delete node from cluster failed. The cluster is not found. (uuid = %s)" % clusterId
        if instance==[] :
            logging.info("Recovery Recovery - The instance %s is not found." % instanceId)
            code = "1"
            message = "The instance %s is not found." % instanceId
        else :
            Recovery.clusterList[clusterId].deleteNode(instance[0])
            logging.info("Recovery Recovery - The instance %s is not protected." % instanceId)
            code = "0"
            message = "The node %s is deleted from cluster." % nodeName
        
        result = {"code": code, "clusterId":clusterId, "message":message}
        return result
        
    def recoveryNode(self, clusterId, nodeName):
        print clusterId
        print nodeName
        
        Recovery.clusterList[clusterId].deleteNode(nodeName)
        for instance in Recovery.clusterList[clusterId].instanceList
            instanceId, belowNode = instance
            if belowNode == nodeName:
                try:
                    self.evacuate(instanceId, Recovery.clusterList[clusterId].nodeList)
                    logging.info("Recovery Recovery - The instance %s evacuate success" % instanceId)
                except:
                    logging.error("Recovery Recovery - The instance %s evacuate failed" % instanceId)
    
    def _evacuate(self, instanceId, nodeList):
        from Schedule import Schedule
        instance = self.novaClient.servers.get(instanceId)
        target_host = Schedule.default(nodeList)
        try:
            instance.evacuate(host = target_host)
        except:
            raise
    
class Cluster(object):

    def __init__(self, uuid, name):
        self.id = uuid
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
    
    def addInstance(self, id, node):
        self.instanceList.append((id, node))
        
    def deleteInstance(self, instance):
        self.instanceList.remove(instance)
        