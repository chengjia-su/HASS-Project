import socket
import sys
import threading
import time
import logging
import ConfigParser
import argparse
import xmlrpclib

class DetectionManager():

    def __init__(self) :
        self.config = ConfigParser.RawConfigParser()
        self.config.read('hass.conf')
        self.threadList = []
        
    def pollingRegister(self, id, node):
        nodeInfo = {"id":id, "node":node, "thread":PollingThread(self.config.get("detection","polling_interval"), self.config.get("detection","polling_threshold"), id, node, int(self.config.get("detection","polling_port"), int(self.config.get("detection","wait_restart_threshold")))}
        self.threadList.append(nodeInfo)
        try:
            nodeInfo["thread"].daemon=True
            nodeInfo["thread"].start()
        except (KeyboardInterrupt, SystemExit):
            print '\n! Received keyboard interrupt, quitting threads.\n'
        
    def pollingCancel(self, id, node):
        newthreadList = []
        for nodeInfo in self.threadList:
            if nodeInfo["id"] == id and nodeInfo["node"]==node :                
                try:
                    nodeInfo["thread"].stop()
                except:
                    pass
            else :
                newthreadList.append(nodeInfo)
        self.threadList = newthreadList

class PollingThread(threading.Thread):
    def __init__(self, interval, threshold, clusterId, node, port, restart_threshold):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(0)
        self.threshold = int(threshold)
        self.restart_threshold = int(restart_threshold)
        self.interval = float(interval)
        self.clusterId = clusterId
        self.node = node
        self.count = 0
        self.restart_count = 0
        self.port = port
        
        self.exit = True
        
    def run(self):
        data = ""
        while self.exit:
            #check FM & FA connection
            while self.count < self.threshold and self.exit :
                try:
                    print "["+self.node+"] create socket connection"
                    self.sock.connect((self.node, self.port))
                    break
                except:
                    print "["+self.node+"] connection failed"
                    self.count = self.count + 1
                    time.sleep(self.interval)
            
            #check FA status and service status
            while self.count < self.threshold and self.exit:
                try:
                    line = "polling request"
                    self.sock.sendall(line)
                    #print "["+self.node+"] sent request"
                    data, addr = self.sock.recvfrom(1024)
                    if data == "OK":
                        self.count = 0
                        #print "["+self.node+"] OK" 
                        
                    elif "error" in data :
                        self.restart_count = self.restart_count + 1
                        if self.restart_count >= self.restart_threshold:
                            self.count = self.threshold
                            self.restart_count = 0
                        print "["+self.node+"]service Failed"

                    elif not data:
                        self.count = self.count + 1
                        print "["+self.node+"]no ACK"

                    else:
                        self.count = self.count + 1
                        print "["+self.node+"]Receive:"+data
                        
                    time.sleep(self.interval)
                    
                except:
                    print "["+self.node+"] connection failed"
                    self.count = self.count + 1
                    time.sleep(self.interval)
                
            if self.count >= self.threshold :   #Just double check
                
                #call Recovery by HASS API
                config = ConfigParser.RawConfigParser()
                config.read('hass.conf')
                logging.error("DetectionManager PollingThread - The %s below cluster : %s is down" % (self.node, self.clusterId))
                
                config = ConfigParser.RawConfigParser()
                config.read('hass.conf')
                authUrl = "http://"+config.get("rpc", "rpc_username")+":"+config.get("rpc", "rpc_password")+"@127.0.0.1:"+config.get("rpc", "rpc_bind_port")
                server = xmlrpclib.ServerProxy(authUrl)
                server.recoveryNode(self.clusterId, self.node)
                self.exit = False
                
            else :
                self.count = 0
                time.sleep(self.interval)
                
    def stop(self):
        self.exit = False
            
def main():
    test = DetectionManager()
    while True:
        ch = raw_input("=>")
        if ch == "s":
            test.pollingRegister("test", "compute1")
        elif ch == "k":
            test.pollingCancel("test", "compute1")
    
if __name__ == "__main__":
    main()