"""This module will read data from database, update data according environment, 
and read configuration file in the beginning. It is a service that listen to user
request and support authentication by HTTP portocal basic access authentication.

Parameters:
    config - this is the configuration file object

Returns:
    The module will return string as reponse according request. """

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from base64 import b64decode
import ConfigParser
import logging
import os
import sys

from Recovery import Recovery
from Recovery import Cluster
from AcessDB import AcessDB

# Declare the configure file here. if you want to change configure file name, please modify scond line.
config = ConfigParser.RawConfigParser()
config.read('hass.conf')

# Set log file here. if you want to change log format, please modify sixth line.
log_level = logging.getLevelName(config.get("log", "level"))
logFilename=config.get("log", "location")
dir = os.path.dirname(logFilename)
if not os.path.exists(dir):
    os.makedirs(dir)
logging.basicConfig(filename=logFilename,level=log_level, format="%(asctime)s [%(levelname)s] : %(message)s")

# Declare Recovery class. You need to ensure that there is only one object. So I declare it as global variable.
recovery = Recovery()

# Declare database access class. When it initialize, connecting database and creating table. You need to ensure new it just one times.
db = AcessDB()

class RequestHandler(SimpleXMLRPCRequestHandler):
#   Handle RPC request from remote user, and suport access authenticate. 
#
#   HTTP basic access authentication are encoded with Base64 in transit, but not
#   encrypted or hashed in any way. Authentication field contain authentication
#   method, username and password combined into a string. If request not contain
#   authentication header or contain not correct username and password, it will
#   return 401 error code. Otherwise, handle request and return response.

    def __init__(self, request, client_address, server):
    # initialize rpc server and get client ip address. call parent initial method.
        rpc_paths = ('/RPC2',)
        self.clientip = client_address[0]
        SimpleXMLRPCRequestHandler.__init__(self, request, client_address, server)
        
    def authenticate(self, headers):
    # split authentication header, decode with Base64 and check username and password
        auth = headers.get('Authorization')
        try:
            (basic, encoded) = headers.get('Authorization').split(' ')
        except:
            logging.info("Hass RequestHandler - No authentication header, request from %s", self.clientip)
            return False
        else:
            (basic, encoded) = headers.get('Authorization').split(' ')
            assert basic == 'Basic', 'Only basic authentication supported'
            encodedByteString = encoded.encode()
            decodedBytes = b64decode(encodedByteString)
            decodedString = decodedBytes.decode()
            (username, password) = decodedString.split(':')
            config = ConfigParser.RawConfigParser()
            config.read('hass.conf')
            if username == config.get("rpc", "rpc_username") and password == config.get("rpc", "rpc_password"):                
                return True
            else:
                logging.info("Hass RequestHandler - Authentication failed, request from %s", self.clientip)
                return False

    def parse_request(self):
    # parser request, get authentication header and send to authenticate().
        if SimpleXMLRPCRequestHandler.parse_request(self):
            if self.authenticate(self.headers):
                logging.info("Hass RequestHandler - Authentication success, request from %s", self.clientip)
                return True
            else:
                self.send_error(401, 'Authentication failed')
                return False
        else:
            logging.info("Hass RequestHandler - Authentication failed, request from %s", self.clientip)
            return False
        

class Hass (object):
#   The SimpleRPCServer class
#   Declare method here, and client can call it directly. 

    def createCluster(self, name, nodeList):
        createCluster_result = recovery.createCluster(name).split(";")
        if createCluster_result[0] == "0":
            addNode_result = recovery.addNode(createCluster_result[1], nodeList).split(";")
            try:
                db_uuid = createCluster_result[1].replace("-","")
                data = {"cluster_uuid":db_uuid, "cluster_name":name}
                db.writeDB("ha_cluster", data)
            except:
                logging.error("Hass Hass - Access database failed.")
                return "1;Access database failed, please wait a minute and try again."
            if addNode_result[0] == "0":
                try:
                    for node in nodeList:
                        data = {"node_name": node,"below_cluster":db_uuid}
                        db.writeDB("ha_node", data)
                    return "0;Create HA cluster and add computing node success, cluster uuid is %s" % createCluster_result[1]
                except:
                    logging.error("Hass Hass - Access database failed.")
                    return "1;Access database failed, please wait a minute and try again."
            else:
                return "0;The cluster is created.(uuid = "+createCluster_result[1]+") But,"+ addNode_result[1]
        else:
            return createCluster_result[0]+";"+createCluster_result[1]

    def deleteCluster(self, uuid):
        result = recovery.deleteCluster(uuid)
        db_uuid = uuid.replace("-","")
        db.deleteData("DELETE FROM ha_cluster WHERE cluster_uuid = %s", db_uuid)
        return result
    
    def listCluster(self):
        result = recovery.listCluster()
        return result
    
    def addNode(self, clusterId, nodeList):
        result = recovery.addNode(clusterId, nodeList).split(";")
        if result[0] == "0":
            try:
                for node in nodeList:
                    db_uuid = clusterId.replace("-", "")
                    data = {"node_name": node,"below_cluster":db_uuid}
                    db.writeDB("ha_node", data)
            except:
                return "2;System failed, please wait a minute and try again."
        return result[0]+";"+result[1]
    
    def deleteNode(self, clusterId, nodename):
        result = recovery.deleteNode(clusterId, nodename)
        db_uuid = clusterId.replace("-", "")
        db.deleteData("DELETE FROM ha_node WHERE node_name = %s && below_cluster = %s", (nodename, db_uuid))
        return result
        
    def listNode(self, clusterId) :
        result = recovery.listNode(clusterId)
        return result
    
    #def addInstance(self, clusterId, instanceId)
        

    
def main():
    
    server = SimpleXMLRPCServer(('',int(config.get("rpc", "rpc_bind_port"))), requestHandler=RequestHandler, allow_none = True)
    server.register_introspection_functions()
    server.register_multicall_functions()
    server.register_instance(Hass(), allow_dotted_names=True)
    try:
        db.readDB()
    except:
        print "Access Database Failed"
    
    print "Server ready"
    try:
        server.serve_forever()
    except:
        sys.exit(1)
    finally:
        db.closeDB()
    
if __name__ == "__main__":
    main()