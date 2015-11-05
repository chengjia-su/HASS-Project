import logging
import ConfigParser
import MySQLdb, MySQLdb.cursors

config = ConfigParser.RawConfigParser()
config.read('hass.conf')

class AcessDB(object):

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
            self.db.execute(format, data)
        except:
            logging.error("Hass AccessDB - write data to DB Failed (MySQL Error: %s)", str(e))
            print "MySQL Error: %s" % str(e)
            raise
    
    def deleteData(self, sql, data):
        self.db.execute(sql, data)
    
    def closeDB(self):
        self.db.close()
        self.dbconn.close()