#!/usr/bin/env python

import xmlrpclib
import ConfigParser
import argparse

from prettytable import PrettyTable

def main():

    config = ConfigParser.RawConfigParser()
    config.read('hass.conf')
    authUrl = "http://"+config.get("rpc", "rpc_username")+":"+config.get("rpc", "rpc_password")+"@127.0.0.1:"+config.get("rpc", "rpc_bind_port")
    server = xmlrpclib.ServerProxy(authUrl)

    parser = argparse.ArgumentParser(description='Openstack high availability software service(HASS)')
    subparsers = parser.add_subparsers(help='functions of HASS', dest='command')
    
    parser_create_cluster = subparsers.add_parser('cluster-create', help='Create a HA cluster')
    parser_create_cluster.add_argument("-n", "--name", help="HA cluster name")
    parser_create_cluster.add_argument("-c", "--nodes", help="Computing nodes you want to add to cluster. Use ',' to separate nodes name")

    parser_delete_cluster = subparsers.add_parser('cluster-delete', help='Delete a HA cluster')
    parser_delete_cluster.add_argument("-i", "--uuid", help="Cluster uuid you want to delete")
    
    parser_list_cluster = subparsers.add_parser('cluster-list', help='List all HA cluster')
    
    args = parser.parse_args()
    
    if args.command == "cluster-create" :
        result = server.createCluster(args.name, args.nodes.strip().split(","))
        print result
    
    elif args.command == "cluster-delete" :
        result = server.deleteCluster(args.uuid)
        print result
        
    elif args.command == "cluster-list" :
        result = server.listCluster()
        table = PrettyTable(['UUID', 'Name'])
        for (uuid, name) in result :
            table.add_row([uuid, name])
        print table
if __name__ == "__main__":
    main()