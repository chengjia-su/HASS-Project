import xmlrpclib
import ConfigParser
import argparse

from prettytable import PrettyTable

class bcolors:
    OK = '\033[92m'
    ERROR = '\033[91m'
    END = '\033[0m'
    
def main():

    config = ConfigParser.RawConfigParser()
    config.read('hass.conf')
    authUrl = "http://"+config.get("rpc", "rpc_username")+":"+config.get("rpc", "rpc_password")+"@127.0.0.1:"+config.get("rpc", "rpc_bind_port")
    server = xmlrpclib.ServerProxy(authUrl)

    parser = argparse.ArgumentParser(description='Openstack high availability software service(HASS)')
    subparsers = parser.add_subparsers(help='functions of HASS', dest='command')
    
    parser_cluster_create = subparsers.add_parser('cluster-create', help='Create a HA cluster')
    parser_cluster_create.add_argument("-n", "--name", help="HA cluster name", required=True)
    parser_cluster_create.add_argument("-c", "--nodes", help="Computing nodes you want to add to cluster. Use ',' to separate nodes name")

    parser_cluster_delete = subparsers.add_parser('cluster-delete', help='Delete a HA cluster')
    parser_cluster_delete.add_argument("-i", "--uuid", help="Cluster uuid you want to delete", required=True)
    
    parser_cluster_list = subparsers.add_parser('cluster-list', help='List all HA cluster')
    
    parser_node_add = subparsers.add_parser('node-add', help='Add computing node to HA cluster')
    parser_node_add.add_argument("-i", "--uuid", help="HA cluster uuid", required=True)
    parser_node_add.add_argument("-c", "--nodes", help="Computing nodes you want to add to cluster. Use ',' to separate nodes name", required=True)
    
    parser_node_delete = subparsers.add_parser('node-delete', help='Delete computing node from HA cluster')
    parser_node_delete.add_argument("-i", "--uuid", help="HA cluster uuid", required=True)
    parser_node_delete.add_argument("-c", "--node", help="A computing node you want to delete from cluster.", required=True)
    
    parser_node_list = subparsers.add_parser('node-list', help='List all computing nodes of Ha cluster')
    parser_node_list.add_argument("-i", "--uuid", help="HA cluster uuid", required=True)
    
    parser_instance_add = subparsers.add_parser('instance-add', help='Protect instance and add instance into HA cluster')
    parser_instance_add.add_argument("-i", "--uuid", help="HA cluster uuid", required=True)
    parser_instance_add.add_argument("-v", "--vmid", help="The ID of the instance you wand to protect", required=True)
    
    parser_instance_delete = subparsers.add_parser('instance-delete', help='remove instance protection')
    parser_instance_delete.add_argument("-i", "--uuid", help="HA cluster uuid", required=True)
    parser_instance_delete.add_argument("-v", "--vmid", help="The ID of the instance you wand to remove protection", required=True)
    
    parser_instance_list = subparsers.add_parser('instance-list', help='List all instances of Ha cluster')
    parser_instance_list.add_argument("-i", "--uuid", help="HA cluster uuid", required=True)
    
    args = parser.parse_args()
    
    if args.command == "cluster-create" :
        if args.nodes != None:
            result = server.createCluster(args.name, args.nodes.strip().split(",")).split(";")
        else:
            result = server.createCluster(args.name, []).split(";")
        print showResult(result)
    
    elif args.command == "cluster-delete" :
        result = server.deleteCluster(args.uuid).split(";")
        print showResult(result)
        
    elif args.command == "cluster-list" :
        result = server.listCluster()
        table = PrettyTable(['UUID', 'Name'])
        for (uuid, name) in result :
            table.add_row([uuid, name])
        print table
        
    elif args.command == "node-add" :
        result = server.addNode(args.uuid, args.nodes.strip().split(",")).split(";")
        print showResult(result)
        
    elif args.command == "node-delete" :
        result = server.deleteNode(args.uuid, args.node).split(";")
        print showResult(result)
        
    elif args.command == "node-list" :
        result = server.listNode(args.uuid)
        if result.split(";")[0] == '0' :
            print "Cluster uuid : " + args.uuid
            table = PrettyTable(["Count","Nodes of HA Cluster"])
            counter = 0
            for node in result.split(";")[1].split(",") :
                counter = counter + 1
                if node != '':
                    table.add_row([str(counter),node])
            print table
        else :
            print result
            
    elif args.command == "instance-add" :
        result = server.addInstance(args.uuid, args.vmid).split(";")
        print showResult(result)
        
    elif args.command == "instance-delete" :
        result = server.deleteInstance(args.uuid, args.vmid).split(";")
        print showResult(result)
        
    elif args.command == "instance-list" :
        result = server.listInstance(args.uuid)
        if result.split(";")[0] == '0' :
            print "Cluster uuid : " + args.uuid
            table = PrettyTable(["Count","Below Host", "Instance ID"])
            counter = 0
            for vmInfo in result.split(";")[1].split(",") :
                counter = counter + 1
                if vmInfo != '':
                    vm = vmInfo.split(":")
                    table.add_row([str(counter), vm[0], vm[1]])
            print table
        else :
            print result
            
def showResult(result):
    if result[0] == '0' :
        return bcolors.OK + "[Success] " + bcolors.END + result[1]
    else :
        return bcolors.ERROR + "[Error] " + bcolors.END +result[1]
    
if __name__ == "__main__":
    main()