import xmlrpclib
import ConfigParser
import argparse

from prettytable import PrettyTable

def main():

    config = ConfigParser.RawConfigParser()
    config.read('hass.conf')
    authSuccessUrl = "http://"+config.get("rpc", "rpc_username")+":"+config.get("rpc", "rpc_password")+"@127.0.0.1:"+config.get("rpc", "rpc_bind_port")
    server = xmlrpclib.ServerProxy(authSuccessUrl)

    parser = argparse.ArgumentParser(description='Openstack high availability software service(HASS)')
    subparsers = parser.add_subparsers(help='functions of HASS')
    
    parser_create_cluster = subparsers.add_parser('create-cluster', help='Create a HA cluster')
    parser_create_cluster.add_argument("-n", "--name", type=string, help="HA cluster name")
    parser_create_cluster.add_argument("-c", "--nodes", type=string, help="Computing nodes you want to add to cluster. Use ',' to separate nodes name")

    parser_delete_cluster = subparsers.add_parser('delete-cluster', help='Delete a HA cluster')
    parser_delete_cluster.add_argument("-i", "--uuid", type=string, help="Cluster uuid you want to delete")
    
    parser_list_cluster = subparsers.add_parser('list-cluster', help='List all HA cluster')
    
    args = parser.parse_args()
    
    
    if args.subparser_name == "create-cluster" :
        result = server.createCluster(args.name, args.nodes.strip().split(","))
        code, message = result.split(";")
        print message
    
    elif args.subparser_name == "delete-cluster" :
        server.createCluster(args.uuid)
        code, message = result.split(";")
        print message
        
    elif args.subparser_name == "list-cluster" :
        result = server.listCluster()
        table = PrettyTable(['UUID', 'Name', 'Node'])
        for uuid, cluster in mydic.iteritems() :
            nodes = '\n'.join(cluster.nodeList)
            table.add_row(["uuid", "cluster.name", nodes])
        
if __name__ == "__main__":
    main()