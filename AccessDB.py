#!/usr/bin/python
"""
Connect to database, create table, write data to database and read data from database
"""

import logging
import ConfigParser
from Recovery import Cluster
import MySQLdb, MySQLdb.cursors

import * from HassException

config = ConfigParser.RawConfigParser()
config.read('hass.conf')

class AccessDB(object):

    def __init__ (self):
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
            
    def createTable(self):
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
            self.closeDB()
            logging.error("Hass AccessDB - Create Table failed (MySQL Error: %s)", str(e))
            print "MySQL Error: %s" % str(e)
            sys.exit(1)
            
    def readDB(self, recovery):
        
        try:
            self.db.execute("SELECT * FROM ha_cluster;")
            ha_cluster_date = self.db.fetchall()
            for cluster in ha_cluster_date:
                nodeList = []
                self.db.execute("SELECT * FROM ha_node WHERE below_cluster = '%s'" % cluster["cluster_uuid"])
                ha_node_date = self.db.fetchall()
                for node in ha_node_date:
                    nodeList.append(node["node_name"])
                uuid = cluster["cluster_uuid"][:8]+"-"+cluster["cluster_uuid"][8:12]+"-"+cluster["cluster_uuid"][12:16]+"-"+cluster["cluster_uuid"][16:20]+"-"+cluster["cluster_uuid"][20:]
                newCluster = Cluster(uuid = uuid, name = cluster["cluster_name"])
                recovery.clusterList[uuid] = newCluster
                recovery.addNode(uuid, nodeList, write_db=False)
                
        except MySQLdb.Error, e:
            self.closeDB()
            logging.error("Hass AccessDB - Read data failed (MySQL Error: %s)", str(e))
            print "MySQL Error: %s" % str(e)
            sys.exit(1)
            
    def writeDB(self, dbname, data):
        if dbname == "ha_cluster":
            format = "INSERT INTO ha_cluster (cluster_uuid,cluster_name) VALUES (%(cluster_uuid)s, %(cluster_name)s);"
        else:
            format = "INSERT INTO ha_node (node_name,below_cluster) VALUES (%(node_name)s, %(below_cluster)s);"
        try:
            self.db.execute(format, data)
            self.dbconn.commit()
        except Exception as e:
            logging.error("Hass AccessDB - write data to DB Failed (MySQL Error: %s)", str(e))
            print "MySQL Error: %s" % str(e)
            raise
    
    def deleteData(self, sql, data):
        self.db.execute(sql, data)
        self.dbconn.commit()
    
    def closeDB(self):
        self.db.close()
        self.dbconn.close()