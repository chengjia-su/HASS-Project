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
        nodeInfo = {"id":id, "node":node, "thread":PollingThread(self.config.get("detection","polling_interval"), self.config.get("detection","polling_threshold"), id, node, int(self.config.get("detection","polling_port")))}
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
    def __init__(self, interval, threshold, clusterId, node, port):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.threshold = int(threshold)
        self.interval = float(interval)
        self.clusterId = clusterId
        self.node = node
        self.count = 0
        self.port = port
        from Recovery import Recovery
        self.recovery = Recovery()
        
        self.exit = True
        
    def run(self):
        while self.exit:
            while self.count < self.threshold :
                try:
                    print "sock connect"
                    self.sock.connect((self.node, self.port))
                    break
                except:
                    print "sock fail"
                    self.count = self.count + 1
                    time.sleep(self.interval)

            while self.count < self.threshold :
                try:
                    line = "polling request"
                    self.sock.sendall(line)
                    print "send request"
                    data, addr = self.sock.recvfrom(1024)
                    if dara == "OK":
                        self.count = 0
                    elif "error" in data :
                        self.count = self.count + 1
                        print "no ACK"
                        time.sleep(self.interval)
                    elif not data:
                        self.count = self.count + 1
                        print "no data"
                        time.sleep(self.interval)
                    else:
                        print "Receive:"+data
                        break
                except:
                    print "sock fail"
                    self.count = self.count + 1
                    time.sleep(self.interval)
                    
            if ("error" in data) and (self.count >= self.threshold):
                time.sleep(self.interval*10)
                line = "polling request"
                self.sock.sendall(line)
                data, addr = self.sock.recvfrom(1024)
                    if dara == "OK":
                        self.count = 0
                
            if self.count >= self.threshold :
                config = ConfigParser.RawConfigParser()
                config.read('hass.conf')
                logging.error("DetectionManager PollingThread - The %s below cluster : %s is down" % (self.node, self.clusterId))
                self.recovery.recoveryNode(self.clusterId, self.node)
                break
                
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