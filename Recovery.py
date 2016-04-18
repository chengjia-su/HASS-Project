from novaclient import client
from keystoneclient.auth.identity import v2
import logging
import ConfigParser

from Cluster import Cluster
from AccessDB import AccessDB

class Recovery (object):

    def __init__ (self, test=False):
        self.clusterList = {}
        self.config = ConfigParser.RawConfigParser()
        self.config.read('hass.conf')
        self.test = test
        self.novaClient = client.Client(2, self.config.get("openstack", "openstack_admin_account"), self.config.get("openstack", "openstack_admin_password"), self.config.get("openstack", "openstack_admin_account"), "http://controller:5000/v2.0")
        self.haNode = []
        self.db = AccessDB()
        if self.test == False:
            try:
                self.db.createTable()
            except:
                print "Access Database Failed"
                self.db.closeDB()
            try:    
                self.db.readDB(self)
            except:
                print "System initialize Failed"
                self.db.closeDB()
        
    def createCluster(self, clusterName):
        import uuid
        newClusterUuid = str(uuid.uuid4())
        newCluster = Cluster(uuid = newClusterUuid, name = clusterName)
        self.clusterList[newClusterUuid] = newCluster
        result = {"code": "0", "clusterId":newClusterUuid, "message":""}
        
        if self.test==False:
        #Unit test should not access database
            try:
                db_uuid = result["clusterId"].replace("-","")
                data = {"cluster_uuid":db_uuid, "cluster_name":clusterName}
                self.db.writeDB("ha_cluster", data)
            except:
                logging.error("Recovery Recovery - Access database failed.")
                result = {"code": "1", "clusterId":newClusterUuid, "message":"Access database failed, please wait a minute and try again."}
        return result
            
    def deleteCluster(self, uuid):
        code = ""
        message = ""
        try:
            del self.clusterList[uuid]
            logging.info("Recovery Recovery - The cluster %s is deleted." % uuid)
            code = "0"
            message = "The cluster %s is deleted." % uuid
            if self.test==False:
            #Unit test should not access database
                try:
                    db_uuid = uuid.replace("-","")
                    self.db.deleteData("DELETE FROM ha_cluster WHERE cluster_uuid = %s", db_uuid)
                except:
                    logging.error("Recovery Recovery - Access database failed.")
                    code = "1"
                    message = "Access database failed."
        except:
            logging.info("Recovery Recovery - The cluster is not found (uuid = %s)." % uuid)
            code = "1"
            message = "The cluster is not found (uuid = %s)." % uuid
            
        finally:
            result = {"code": code, "clusterId":uuid, "message":message}
            return result
        
    def listCluster(self):
        result = []
        for uuid, cluster in self.clusterList.iteritems() :
            result.append((uuid, cluster.name))
        return result
        
    def addNode(self, clusterId, nodeList, write_db = True, hostList = []):
        code = ""
        message = ""
        #query openstack node list
        if self.test == False:
            hypervisorList = self.novaClient.hypervisors.list() 
            for hypervisor in hypervisorList:
                hostList.append(str(hypervisor.hypervisor_hostname))
        else:
            write_db = False
        notMatchNode = [nodeName for nodeName in nodeList if nodeName not in hostList]
        if not notMatchNode:
            try:
                duplication_node = []
                correct_node = []
                for nodeName in nodeList:
                    if nodeName in self.haNode:
                        duplication_node.append(nodeName)
                    else:
                        correct_node.append(nodeName)

                self.clusterList[clusterId].addNode(correct_node, test = self.test)
                self.haNode.extend(correct_node)

                if duplication_node == []:
                    logging.info("Recovery Recovery - The node %s is added to cluster." % ', '.join(str(node) for node in nodeList))
                    code = "0"
                    message = "The node %s is added to cluster." % ', '.join(str(node) for node in nodeList)
                else:
                    logging.info("Recovery Recovery - overlapping node %s does not add to cluster" % ', '.join(str(node) for node in duplication_node))
                    code = "1"
                    message = "overlapping node %s does not add to cluster" % ', '.join(str(node) for node in duplication_node)
                if write_db == True:
                    try:
                        db_uuid = clusterId.replace("-", "")
                        for node in correct_node:
                            data = {"node_name": node,"below_cluster":db_uuid}
                            self.db.writeDB("ha_node", data)
                    except:
                        logging.error("Recovery Recovery - Access database failed.")
                        code = "1"
                        message = "Access database failed."
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
            if nodeName not in self.clusterList[clusterId].nodeList:
                logging.info("Recovery Recovery - Delete node from cluster failed. The node is not found. (uuid = %s)" % nodeName)
                code = "1"
                message = "Delete node from cluster failed. The node is not found. (uuid = %s)" % nodeName
            else :
                self.clusterList[clusterId].deleteNode(nodeName, test = self.test)
                self.haNode.remove(nodeName)
                logging.info("Recovery Recovery - The node %s is deleted from cluster." % nodeName)
                code = "0"
                message = "The node %s is deleted from cluster." % nodeName
                if self.test == False:
                    try:
                        db_uuid = clusterId.replace("-", "")
                        self.db.deleteData("DELETE FROM ha_node WHERE node_name = %s && below_cluster = %s", (nodeName, db_uuid))
                    except:
                        logging.error("Recovery Recovery - Access database failed.")
                        code = "1"
                        message = "Access database failed."
            

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
            nodeList = self.clusterList[clusterId].getNode()
            code = "0"
            message = "Success"
        except:
            nodeList = ""
            code = "1"
            message = "The cluster is not found. (uuid = %s)" % clusterId
        finally:
            result = {"code": code, "nodeList":nodeList, "message":message}
            return result
            
    def addInstance(self, clusterId, instanceId):
        code = ""
        message = ""
        try:
            test_id = self.clusterList[clusterId].instanceList
        except:
            logging.info("Recovery Recovery - Add the instance to cluster failed. The cluster is not found. (uuid = %s)" % clusterId)
            code = "1"
            message = "Add the instance to cluster failed. The cluster is not found. (uuid = %s)" % clusterId
            result = {"code": code, "clusterId":clusterId, "message":message}
            return result
            
        if [instance for instance in self.clusterList[clusterId].instanceList if instance[0]==instanceId] != [] :
            logging.info("Recovery Recovery - The instance %s is already protected." % instanceId)
            code = "1"
            message = "The instance %s is already protected." % instanceId
        elif self.test == False and self.novaClient.volumes.get_server_volumes(instanceId) == []:
            logging.info("Recovery Recovery - The instance %s can not be protected. (No volume)" % instanceId)
            code = "1"
            message = "The instance %s can not be protected. (No volume)" % instanceId
        else:
            if self.test == False:
                vm = self.novaClient.servers.get(instanceId)
                host = getattr(vm,"OS-EXT-SRV-ATTR:host")
                if host in self.clusterList[clusterId].nodeList:
                    self.clusterList[clusterId].addInstance(instanceId, host)
                    code = "0"
                    message = "The instance %s is protected." % instanceId
                else:
                    from Schedule import Schedule
                    try:
                        target_host = Schedule.default(self.clusterList[clusterId].nodeList)
                        vm.live_migrate(host = target_host)
                        self.clusterList[clusterId].addInstance(instanceId, host)
                        code = "0"
                        message = "The instance %s is migrated to host:%s and protected." % (instanceId, target_host)
                    except:
                        code = "1"
                        message = "The instance %s can not be protected. (Migrate to HA cluster failed)" % instanceId
            else:
                self.clusterList[clusterId].addInstance(instanceId, "testHost")
                code = "0"
                message = "The instance %s is protected." % instanceId
        result = {"code": code, "clusterId":clusterId, "message":message}
        return result
        
    def deleteInstance(self, clusterId, instanceId):
        code = ""
        message = ""
        try:
            instances = [instance for instance in self.clusterList[clusterId].instanceList if instance[0]==instanceId]
        except:
            logging.info("Recovery Recovery - Delete node from cluster failed. The cluster is not found. (uuid = %s)" % clusterId)
            code = "1"
            message = "Delete node from cluster failed. The cluster is not found. (uuid = %s)" % clusterId
            result = {"code": code, "clusterId":clusterId, "message":message}
            return result
        
        if instances==[] :
            logging.info("Recovery Recovery - The instance %s is not found." % instanceId)
            code = "1"
            message = "The instance %s is not found." % instanceId
        else :
            self.clusterList[clusterId].deleteInstance(instances[0])
            logging.info("Recovery Recovery - The instance %s is not protected." % instanceId)
            code = "0"
            message = "The instance %s is deleted from cluster." % instanceId
        
        result = {"code": code, "clusterId":clusterId, "message":message}
        return result
        
    def listInstance(self, clusterId):
        code = ""
        message = ""
        try:
            instanceList = self.clusterList[clusterId].getInstance()
            code = "0"
            message = "Success"
        except:
            code = "1"
            instanceList = ""
            message = "The cluster is not found. (uuid = %s)" % clusterId
        finally:
            result = {"code": code, "instanceList":instanceList, "message":message}
            return result
            
    def recoveryNode(self, clusterId, nodeName):
        print clusterId
        print nodeName

        for instance in self.clusterList[clusterId].instanceList:
            instanceId, belowNode = instance
            if belowNode == nodeName:
                try:
                    self._evacuate(instanceId, self.clusterList[clusterId].nodeList)
                    logging.info("Recovery Recovery - The instance %s evacuate success" % instanceId)
 
                except Exception as e:
                    print e
                    logging.error("Recovery Recovery - The instance %s evacuate failed" % instanceId)
        self.clusterList[clusterId].deleteNode(nodeName)
        db_uuid = clusterId.replace("-", "")
        self.haNode.remove(nodeName)
        self.db.deleteData("DELETE FROM ha_node WHERE node_name = %s && below_cluster = %s", (nodeName, db_uuid))
        
    def _evacuate(self, instanceId, nodeList):
        from Schedule import Schedule
        schedule = Schedule()
        instance = self.novaClient.servers.get(instanceId)
        target_host = schedule.default(nodeList)
        try:
            instance.evacuate(host = target_host)
        except:
            raise
    

        