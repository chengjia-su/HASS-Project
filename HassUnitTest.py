from collections import Counter
from prettytable import PrettyTable
from datetime import datetime
import xmlrpclib

from Recovery import Recovery
from Recovery import Cluster


environment_node = ["testNode1", "testNode2", "testNode3", "testNode4"]
listen_port = str(61209)

#----------------------------Test Data-------------------------
correct_auth = "http://user:pdclab@127.0.0.1:"+listen_port
no_auth = "http://127.0.0.1:"+listen_port
wrong_auth = "http://auth:fail@127.0.0.1:"+listen_port

cluster_name = "testCluster"

correct_nodeList = ["testNode1", "testNode4"]
duplicate_nodeList = ["testNode1", "testNode3"]
wrong_nodeList = ["testNode4", "testNode5"]
correct_nodeName = "testNode1"
wrong_nodeName = "testNode5"
wrong_clusterId = "1a2b3c4d-5678-9101-2b3c-zxcvb987654a"

test_instanceId = "0e4011a4-3128-4674-ab16-dd1b7ecc126e"
duplicate_instanceId = "0e4011a4-3128-4674-ab16-dd1b7ecc126e"
wrong_instanceId = "1a2b3c4d-5678-9101-2b3c-zxcvb987654a"
#--------------------------------------------------------------

class ShowResult():
    def __init__(self):
        self.OK = '\033[92m'+"PASS!"+'\033[0m'
        self.ERROR = '\033[91m'+"FAIL!"+'\033[0m'
    def ok(self, case, time):
        
        print case+"("+str(time.microseconds)+"ms) : "+self.OK
    def error(self, case):
        print case+"(execution time:"+str(time.microseconds)+"ms) : "+self.ERROR
        
        
class TestClientAuth():

    def __init__(self):
        self.printer = ShowResult()
        self.clientUrl = "127.0.0.1:"+listen_port
        self.case_counter = 0
        self.pass_case = 0
        self.fail_case = 0
        
    def test_correctAuth(self):
        case = "Authenticate client with correct username and password"
        self.case_counter += 1
        start_time = datetime.now()
        server = xmlrpclib.ServerProxy(correct_auth)
        try:
            resp = server.test_auth_response()
            exec_time = datetime.now() - start_time
            if resp == "auth success" :
                self.pass_case += 1
                self.printer.ok(case, exec_time)
            else :
                self.fail_case += 1
                self.printer.error(case, exec_time)
                
        except xmlrpclib.ProtocolError:
            exec_time = datetime.now() - start_time
            self.fail_case += 1
            self.printer.error(case, exec_time)
            
    def test_wrongAuth(self):
        case = "Authenticate client with wrong username and password"
        self.case_counter += 1
        start_time = datetime.now()
        server = xmlrpclib.ServerProxy(wrong_auth)
        
        try:
            server.test_auth_response()
            exec_time = datetime.now() - start_time
            self.fail_case += 1
            self.printer.error(case, exec_time)
        except xmlrpclib.ProtocolError:
            exec_time = datetime.now() - start_time
            self.pass_case += 1
            self.printer.ok(case, exec_time)
            
    def test_withoutAuth(self):
        case = "Authenticate client without username and password"
        self.case_counter += 1
        start_time = datetime.now()
        server = xmlrpclib.ServerProxy(no_auth)

        try:
            server.test_auth_response()
            exec_time = datetime.now() - start_time
            self.fail_case += 1
            self.printer.error(case, exec_time)
        except xmlrpclib.ProtocolError:
            exec_time = datetime.now() - start_time
            self.pass_case += 1
            self.printer.ok(case, exec_time)
            
            

    
class TestCluster():

    def __init__(self):
        self.printer = ShowResult()
        self.case_counter = 0
        self.pass_case = 0
        self.fail_case = 0
        
    def test_create(self):
        case = "Create HA cluster"
        self.case_counter += 1
        testRM = Recovery(test = True, hostList = environment_node)
        
        start_time = datetime.now()
        result = testRM.createCluster(cluster_name)
        exec_time = datetime.now() - start_time
        if result["code"] == "0":
            self.pass_case += 1
            self.printer.ok(case, exec_time)
        else:
            self.fail_case += 1
            self.printer.error(case, exec_time)
            
    def test_delete_correctId(self):
        case = "Delete HA cluster with correct uuid"
        self.case_counter += 1
        testRM = Recovery(test = True, hostList = environment_node)
        test_clusterId = testRM.createCluster(cluster_name)["clusterId"]
        
        start_time = datetime.now()
        result = testRM.deleteCluster(test_clusterId)
        exec_time = datetime.now() - start_time
        if result["code"] == "0":
            self.pass_case += 1
            self.printer.ok(case, exec_time)
        else:
            self.fail_case += 1
            self.printer.error(case, exec_time)
            
    def test_delete_wrongId(self):
        case = "Delete HA cluster with wrong uuid"
        self.case_counter += 1
        testRM = Recovery(test = True, hostList = environment_node)
        test_clusterId = testRM.createCluster(cluster_name)["clusterId"]
        
        start_time = datetime.now()
        result = testRM.deleteCluster(wrong_clusterId)
        exec_time = datetime.now() - start_time
        if result["code"] == "1":
            self.pass_case += 1
            self.printer.ok(case, exec_time)
        else:
            self.fail_case += 1
            self.printer.error(case, exec_time)
    
    def test_read(self):
        case = "Show HA cluster"
        self.case_counter += 1
        testRM = Recovery(test = True, hostList = environment_node)
        test_clusterId = testRM.createCluster(cluster_name)["clusterId"]
        
        start_time = datetime.now()
        result = testRM.listCluster()
        exec_time = datetime.now() - start_time
        if len(result) != 1 :
            self.fail_case += 1
            self.printer.error(case, exec_time)
        else:
            if result[0][0] == test_clusterId and result[0][1] == cluster_name:
                self.pass_case += 1
                self.printer.ok(case, exec_time)
            else:
                self.fail_case += 1
                self.printer.error(case, exec_time)

class TestNode():

    def __init__(self):
        self.printer = ShowResult()
        self.case_counter = 0
        self.pass_case = 0
        self.fail_case = 0
        
    def test_add_correctList(self):
        case = "Add nodes to HA cluster with correct node list"
        self.case_counter += 1
        testRM = Recovery(test = True, hostList = environment_node)
        test_clusterId = testRM.createCluster(cluster_name)["clusterId"]
        
        start_time = datetime.now()
        result = testRM.addNode(test_clusterId, correct_nodeList)
        exec_time = datetime.now() - start_time
        if result["code"] == "0":
            self.pass_case += 1
            self.printer.ok(case, exec_time)
        else:
            self.fail_case += 1
            self.printer.error(case, exec_time)
            
    def test_add_wrongClusterId(self):
        case = "Add nodes to HA cluster with wrong cluster ID"
        self.case_counter += 1
        testRM = Recovery(test = True, hostList = environment_node)
        test_clusterId = testRM.createCluster(cluster_name)["clusterId"]
        
        start_time = datetime.now()
        result = testRM.addNode(wrong_clusterId, correct_nodeList)
        exec_time = datetime.now() - start_time
        if result["code"] == "1":
            self.pass_case += 1
            self.printer.ok(case, exec_time)
        else:
            self.fail_case += 1
            self.printer.error(case, exec_time)
            
    def test_add_duplicateList(self):
        case = "Add nodes to HA cluster with duplicate node list"
        self.case_counter += 1
        testRM = Recovery(test = True, hostList = environment_node)
        test_clusterId = testRM.createCluster(cluster_name)["clusterId"]
        testRM.addNode(test_clusterId, correct_nodeList)
        
        start_time = datetime.now()
        result = testRM.addNode(test_clusterId, duplicate_nodeList)
        exec_time = datetime.now() - start_time
        if result["code"] == "1":
            self.pass_case += 1
            self.printer.ok(case, exec_time)
        else:
            self.fail_case += 1
            self.printer.error(case, exec_time)
            
    def test_add_wrongList(self):
        case = "Add nodes to HA cluster with wrong node list"
        self.case_counter += 1
        testRM = Recovery(test = True, hostList = environment_node)
        test_clusterId = testRM.createCluster(cluster_name)["clusterId"]
        
        start_time = datetime.now()
        result = testRM.addNode(test_clusterId, wrong_nodeList)
        exec_time = datetime.now() - start_time
        if result["code"] == "1":
            self.pass_case += 1
            self.printer.ok(case, exec_time)
        else:
            self.fail_case += 1
            self.printer.error(case, exec_time)
            
    def test_delete_correct(self):
        case = "Delete node from HA cluster"
        self.case_counter += 1
        testRM = Recovery(test = True, hostList = environment_node)
        test_clusterId = testRM.createCluster(cluster_name)["clusterId"]
        testRM.addNode(test_clusterId, correct_nodeList)        
        
        start_time = datetime.now()
        result = testRM.deleteNode(test_clusterId, correct_nodeName)
        exec_time = datetime.now() - start_time
        if result["code"] == "0":
            self.pass_case += 1
            self.printer.ok(case, exec_time)
        else:
            self.fail_case += 1
            self.printer.error(case, exec_time)
            
    def test_delete_wrongClusterId(self):
        case = "Delete node from HA cluster with wrong cluster uuid"
        self.case_counter += 1
        testRM = Recovery(test = True, hostList = environment_node)
        test_clusterId = testRM.createCluster(cluster_name)["clusterId"]
        testRM.addNode(test_clusterId, correct_nodeList)        
        
        start_time = datetime.now()
        result = testRM.deleteNode(wrong_clusterId, correct_nodeName)
        exec_time = datetime.now() - start_time
        if result["code"] == "1":
            self.pass_case += 1
            self.printer.ok(case, exec_time)
        else:
            self.fail_case += 1
            self.printer.error(case, exec_time)

    def test_delete_wrongNodeName(self):
        case = "Delete node from HA cluster with wrong node name"
        self.case_counter += 1
        testRM = Recovery(test = True, hostList = environment_node)
        test_clusterId = testRM.createCluster(cluster_name)["clusterId"]
        testRM.addNode(test_clusterId, correct_nodeList)        
        
        start_time = datetime.now()
        result = testRM.deleteNode(test_clusterId, wrong_nodeName)
        exec_time = datetime.now() - start_time
        if result["code"] == "1":
            self.pass_case += 1
            self.printer.ok(case, exec_time)
        else:
            self.fail_case += 1
            self.printer.error(case, exec_time)
    
    def test_read_correct(self):
        case = "Show node list from HA cluster"
        self.case_counter += 1
        testRM = Recovery(test = True, hostList = environment_node)
        test_clusterId = testRM.createCluster(cluster_name)["clusterId"]
        testRM.addNode(test_clusterId, correct_nodeList)        
        
        start_time = datetime.now()
        result = testRM.listNode(test_clusterId)
        exec_time = datetime.now() - start_time
        
        resultList = result["nodeList"].split(",")
        if Counter(resultList) != Counter(correct_nodeList):
            self.fail_case += 1
            self.printer.error(case, exec_time)
        else :
            if result["code"] == "0":
                self.pass_case += 1
                self.printer.ok(case, exec_time)
            else:
                self.fail_case += 1
                self.printer.error(case, exec_time)
                
    def test_read_wrongClusterId(self):
        case = "Show node list from HA cluster with wrong cluster uuid"
        self.case_counter += 1
        testRM = Recovery(test = True, hostList = environment_node)
        test_clusterId = testRM.createCluster(cluster_name)["clusterId"]
        testRM.addNode(test_clusterId, correct_nodeList)        
        
        start_time = datetime.now()
        result = testRM.listNode(wrong_clusterId)
        exec_time = datetime.now() - start_time
        if result["code"] == "1":
            self.pass_case += 1
            self.printer.ok(case, exec_time)
        else:
            self.fail_case += 1
            self.printer.error(case, exec_time)
'''
class TestInstance():

    def __init__(self):
        
    def test_create(self):
    
    def test_delete(self):
'''    
def main():
    def percentage(part, whole):
        result = 100 * float(part)/float(whole)
        return str(result)+"%"
    
    print "Test Start!"
    print "------------------------------------------------------------------------------------"
    auth_tester = TestClientAuth()
    print "[HAaaS-TC-01]"
    auth_tester.test_correctAuth()
    auth_tester.test_wrongAuth()
    auth_tester.test_withoutAuth()
    print "------------------------------------------------------------------------------------"
    cluster_tester = TestCluster()
    print "[HAaaS-TC-02]"
    cluster_tester.test_create()
    print "------------------------------------------------------------------------------------"
    print "[HAaaS-TC-03]"
    cluster_tester.test_delete_correctId()
    cluster_tester.test_delete_wrongId()
    print "------------------------------------------------------------------------------------"
    print "[HAaaS-TC-04]"
    cluster_tester.test_read()
    
    
    node_tester = TestNode()
    print "------------------------------------------------------------------------------------"
    print "[HAaaS-TC-05]"
    node_tester.test_add_correctList()
    node_tester.test_add_wrongClusterId()
    node_tester.test_add_duplicateList()
    node_tester.test_add_wrongList()
    print "------------------------------------------------------------------------------------"
    print "[HAaaS-TC-06]"
    node_tester.test_delete_correct()
    node_tester.test_delete_wrongClusterId()
    node_tester.test_delete_wrongNodeName()
    print "------------------------------------------------------------------------------------"
    print "[HAaaS-TC-07]"
    node_tester.test_read_correct()
    node_tester.test_read_wrongClusterId()
    print "------------------------------------------------------------------------------------"
    print "Test Finish!"

    total_case = auth_tester.case_counter + cluster_tester.case_counter + node_tester.case_counter
    pass_case = auth_tester.pass_case + cluster_tester.pass_case + node_tester.pass_case
    fail_case = auth_tester.fail_case + cluster_tester.fail_case + node_tester.fail_case
    
    reportTable = PrettyTable()
    reportTable.field_names = ["Total Case", "Pass Case", "Fail Case", "Pass Rate"]
    reportTable.add_row([total_case, pass_case, fail_case, percentage(pass_case, total_case)])
    print reportTable

if __name__ == "__main__":
    main()
    