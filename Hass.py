#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

config = ConfigParser.RawConfigParser()
config.read('hass.conf')

log_level = logging.getLevelName(config.get("log", "level"))
logFilename=config.get("log", "location")
dir = os.path.dirname(logFilename)
if not os.path.exists(dir):
    os.makedirs(dir)
logging.basicConfig(filename=logFilename,level=log_level, format="%(asctime)s [%(levelname)s] : %(message)s")
recovery = Recovery()

class RequestHandler(SimpleXMLRPCRequestHandler):
#Handle RPC request from remote user, and suport access authenticate. 
#
#   HTTP basic access authentication are encoded with Base64 in transit, but not
#   encrypted or hashed in any way. Authentication field contain authentication
#   method, username and password combined into a string. If request not contain
#   authentication header or contain not correct username and password, it will
#   return 401 error code. Otherwise, handle request and return response.

    def __init__(self, request, client_address, server):
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
        
    def createCluster(self, name, nodeList):
        createCluster_result = recovery.createCluster(name).split(";")
        if createCluster_result[0] == 0:
            addNode_result = recovery.addNode(createCluster_result[1], nodeList).split(";")
            if addNode_result[0] == 0:
                try:
                    db = AccessDB()
                    data = {"cluster_uuid":createCluster_result[1], "cluster_name":name}
                    db.writeDB("ha_cluster", data)
                    return "0;Create HA cluster and add computing node success, cluster uuid is %s" % createCluster_result[1]
                except:
                    return "2;System failed, please wait a minute and try again."
            else:
                return addNode_result[0]+";"+addNode_result[1]
        else:
            return createCluster_result[0]+";"+createCluster_result[1]

    def deleteCluster(self, uuid):
        result = recovery.deleteCluster(uuid)
        return result
        
    def addNode(self, clusterId, nodeList):
        result = recovery.addNode(clusterId, nodeList).split(";")
        if result[0] == 0:
            try:
                db = AccessDB()
                for node in nodeList:
                    data = {"node_name": node,"below_cluster":clusterId}
                    db.writeDB("ha_node", data)
            except:
                return "2;System failed, please wait a minute and try again."
        return result
    
    def deleteNode(self, clusterId, nodename):
        
    #def showCluster(self, uuid):
        
    #def setDetector(self):


       
class AcessDB(object):

    def __init__ (self):
        import MySQLdb, MySQLdb.cursors
        try:
            self.dbconn = MySQLdb.connect(  host = config.get("mysql", "mysql_ip"),
                                        user = config.get("mysql", "mysql_username"),
                                        passwd = config.get("mysql", "mysql_password"),
                                        db = "hass",
                                    )
        except MySQLdb.Error, e:
            logging.error("Hass AccessDB - connect to database failed (MySQL Error: %s)", str(e))
            print "MySQL Error: %s" % str(e)
            sys.exit(1)

        self.db = self.dbconn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
        try:
            self.db.execute("SET sql_notes = 0;")
            self.db.execute("""
                            CREATE TABLE IF NOT EXISTS ha_cluster 
                            (
                            cluster_uuid char(36),
                            cluster_name char(18),
                            PRIMARY KEY(cluster_uuid)
                            );
                            """)
            self.db.execute("""
                            CREATE TABLE IF NOT EXISTS ha_node 
                            (
                            node_id MEDIUMINT NOT NULL AUTO_INCREMENT,
                            node_name char(18),
                            below_cluster char(36),
                            PRIMARY KEY(node_id),
                            FOREIGN KEY(below_cluster)
                                REFERENCES ha_cluster(cluster_uuid)
                                ON DELETE CASCADE
                            );
                            """)
        except MySQLdb.Error, e:
            logging.error("Hass AccessDB - Read data failed (MySQL Error: %s)", str(e))
            print "MySQL Error: %s" % str(e)
            
    def readDB(self):
        self.db.execute("SELECT * FROM ha_cluster;")
        ha_cluster_date = self.db.fetchall()
        for cluster in ha_cluster_date:
            nodeList = []
            self.db.execute("SELECT * FROM ha_node WHERE below_cluster = "+cluster["cluster_uuid"])
            ha_node_date = self.db.fetchall()
            for node in ha_node_date:
                nodeList.append(node[node_name])
            newCluster = Cluster(uuid = cluster["cluster_uuid"], name = cluster["cluster_name"])
            recovery.clusterList[cluster["cluster_uuid"]] = newCluster
            recovery.addNode(cluster["cluster_uuid"], nodeList)
            
    def writeDB(self, dbname, data):
        if dbname == "ha_cluster":
            format = "INSERT INTO ha_cluster (cluster_uuid,cluster_name) VALUES (%(uuid)s, %(name)s);"
        else:
            format = "INSERT INTO ha_node (node_name,below_cluster) VALUES (%(name)s, %(cluster)s);"
        try:
            cursor.execute(format, data)
        except:
            logging.error("Hass AccessDB - write data to DB Failed (MySQL Error: %s)", str(e))
            print "MySQL Error: %s" % str(e)
            raise
    
    def closeDB(self):
        self.db.close()
        self.dbconn.close()
    
def main():
    
    server = SimpleXMLRPCServer(('',int(config.get("rpc", "rpc_bind_port"))), requestHandler=RequestHandler, allow_none = True)
    server.register_introspection_functions()
    server.register_multicall_functions()
    server.register_instance(Hass(), allow_dotted_names=True)
    try:
        pre_running = AcessDB()
        pre_running.readDB()
    finally:
        pre_running.closeDB()
    
    
    print "Server ready"
    try:
        server.serve_forever()
    except:
        sys.exit(1)
    
    
if __name__ == "__main__":
    main()