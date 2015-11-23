import unittest
import xmlrpclib
import datetime
import ConfigParser
from Recovery import Recovery
from Recovery import Cluster
import ConfigParser
config = ConfigParser.RawConfigParser()
config.read('hass.conf')

class HassTest(unittest.TestCase):
    def setUp(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('hass.conf')
        self.noAuthUrl = "http://127.0.0.1:"+self.config.get("rpc", "rpc_bind_port")
        self.authFailedUrl = "http://auth:failed@127.0.0.1:"+self.config.get("rpc", "rpc_bind_port")
        self.authSuccessUrl = "http://"+self.config.get("rpc", "rpc_username")+":"+self.config.get("rpc", "rpc_password")+"@127.0.0.1:"+self.config.get("rpc", "rpc_bind_port")
        self.clusterName = "TestCluster-%s" % datetime.datetime.now().strftime("%Y/%m/%d-%H:%M")
        self.trueNodeList = ["compute1", "compute2"]        
        
    def test_noAuthHeader (self):
        server = xmlrpclib.ServerProxy(self.noAuthUrl)
        with self.assertRaises(xmlrpclib.ProtocolError):
            server.createCluster(self.clusterName, self.trueNodeList)
            
    def test_authFailed (self):
        server = xmlrpclib.ServerProxy(self.authFailedUrl)
        with self.assertRaises(xmlrpclib.ProtocolError):
            server.createCluster(self.clusterName, self.trueNodeList)
            
    def test_createClusterSuccess(self):
        server = xmlrpclib.ServerProxy(self.authSuccessUrl)
        self.assertEqual(server.createCluster(self.clusterName, self.trueNodeList).split(";")[0], "0")
    
    def tearDown(self):
        import MySQLdb        
        dbconn = MySQLdb.connect(  host = config.get("mysql", "mysql_ip"),
                                        user = config.get("mysql", "mysql_username"),
                                        passwd = config.get("mysql", "mysql_password"),
                                        db = "hass",
                                )
        db = dbconn.cursor()
        db.execute("DELETE FROM ha_node;")
        db.execute("DELETE FROM ha_cluster;")
        
class RecoveryCreateClusterTest(unittest.TestCase):

    def setUp(self):
        Recovery.clusterList = {}
        self.recovery = Recovery()
        self.trueNodeList = ["compute1", "compute2"]
        self.falseNodeList = ["compute426", "compute321"]
        self.clusterName = "TestCluster-%s" % datetime.datetime.now().strftime("%Y/%m/%d-%H:%M")
        self.uuid = self.recovery.createCluster(self.clusterName).split(";")[1]
    
    def test_addNode_Success(self):
        self.assertEqual(self.recovery.addNode(self.uuid, self.trueNodeList).split(";")[0], "0")
    
    def test_addNode_WrongId(self):
        self.assertEqual(self.recovery.addNode("123456789", self.trueNodeList).split(";")[0], "1")
    
    def test_addNode_WrongNodeList(self):
        self.assertEqual(self.recovery.addNode(self.uuid, self.falseNodeList).split(";")[0], "1")
    
    def tearDown(self):
        import MySQLdb
        Recovery.clusterList = {}
        dbconn = MySQLdb.connect(  host = config.get("mysql", "mysql_ip"),
                                        user = config.get("mysql", "mysql_username"),
                                        passwd = config.get("mysql", "mysql_password"),
                                        db = "hass",
                                )
        db = dbconn.cursor()
        db.execute("DELETE FROM ha_node;")
        db.execute("DELETE FROM ha_cluster;")

class RecoveryDeleteClusterTest(unittest.TestCase):
    def setUp(self):
        Recovery.clusterList = {}
        self.recovery = Recovery()
        self.clusterName = "TestCluster-%s" % datetime.datetime.now().strftime("%Y/%m/%d-%H:%M")
        self.uuid = self.recovery.createCluster(self.clusterName).split(";")[1]
    
    def test_deleteCluster_Sucess(self):
        self.assertEqual(self.recovery.deleteCluster(self.uuid).split(";")[0], "0")
        
    def test_deleteCluster_Exception(self):
        self.assertEqual(self.recovery.deleteCluster("123456789").split(";")[0], "1")
        
if __name__ == '__main__':
    testHass = unittest.TestLoader().loadTestsFromTestCase(HassTest)
    testRecoveryCreateCluster = unittest.TestLoader().loadTestsFromTestCase(RecoveryCreateClusterTest)
    testRecoveryDeleteCluster = unittest.TestLoader().loadTestsFromTestCase(RecoveryDeleteClusterTest)
    
    unittest.TextTestRunner(verbosity=2).run(testRecoveryCreateCluster)
    unittest.TextTestRunner(verbosity=2).run(testRecoveryDeleteCluster)
    unittest.TextTestRunner(verbosity=2).run(testHass)