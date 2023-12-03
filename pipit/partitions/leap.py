from . import Partition, Event
import pandas as pd
from typing import Set, List, Dict
import networkx as nx
import pygraphviz as pgv
from networkx.drawing.nx_agraph import graphviz_layout

class Leap:
    def __init__(self, partition_map: Dict[int, Partition], all_processes: Set[int], partition_ids = []) -> None:
        self.partitions_ids: Set[int] = set(partition_ids)
        self.processes: Set[int] = set()
        self.all_processes = all_processes
        self.partition_map = partition_map
        self.is_complete: bool = False
        self.calc_processes()
        self.min_event_start: float = float('inf')
        self.max_event_end: float = 0
        self.__calc_min_max_time()

    def calc_processes(self) -> None:
        self.processes.clear()
        for p_id in self.partitions_ids:
            p = self.partition_map[p_id]
            self.processes = self.processes.union(p.processes)
        self.calc_is_complete()
    
    def calc_is_complete(self) -> None:
        self.is_complete = (self.processes == self.all_processes)
    
    def remove_partition(self, partition_id: int) -> None:
        self.partitions_ids.remove(partition_id)
        self.calc_processes()
        self.__calc_min_max_time()

    def add_partition(self, partition_id: int) -> None:
        self.partitions_ids.add(partition_id)
        self.processes = self.processes.union(self.partition_map[partition_id].processes)
        self.calc_is_complete()
        self.min_event_start = min(self.min_event_start, self.partition_map[partition_id].min_event_start)
        self.max_event_end = max(self.max_event_end, self.partition_map[partition_id].max_event_end)

    def partition_will_expand(self, partition_id: int) -> bool:
        # returns true if partition encompass processes that aren't in the leap
        diff = self.partition_map[partition_id].processes.difference(self.processes)
        return len(diff) > 0
    
    def absorb_leap(self, leap: 'Leap') -> None:
        # merges leap into this leap
        self.partitions_ids = self.partitions_ids.union(leap.partitions_ids)
        self.processes = self.processes.union(leap.processes)
        self.calc_is_complete()
        self.min_event_start = min(self.min_event_start, leap.min_event_start)
        self.max_event_end = max(self.max_event_end, leap.max_event_end)

    def __calc_min_max_time(self) -> None:
        if len(self.partitions_ids) > 0:
            self.min_event_start = min([self.partition_map[p_id].min_event_start for p_id in self.partitions_ids])
            self.max_event_end = max([self.partition_map[p_id].max_event_end for p_id in self.partitions_ids])

    
    
        self.complete: bool = False
    
    def get_event(self, partition_id: int, event_id: int) -> Event:
        return self.partition_map[partition_id].event_dict[event_id]

    def is_leap_empty(self) -> bool:
        return len(self.partitions_ids) == 0

    def __create_send_dag(self, verify = False):
        def get_next_nonrecv_edge(next_event):
            recv_chain = []
            while next_event is not None and next_event.event_id in event_dict.keys():
                node2 = (next_event.get_partition().partition_id, next_event.event_id)
                if next_event.event_name != "MpiRecv":
                    return node2, recv_chain
                else:
                    recv_chain.append(node2)
                    next_event = next_event.get_next_event()
            return None, recv_chain
    
        # Get all events in the leap
        event_dict = {}
        for partition_id in self.partitions_ids:
            partition = self.partition_map[partition_id]
            event_dict.update(partition.get_events())
    
        # Create a DAG using only the MpiSend events
        #recv_nodes = set()

        full_dag_nodes = []
        full_dag_edges = pd.DataFrame(columns=['Node1', 'Node2'])

        send_dag_nodes = []
        send_dag_edges = pd.DataFrame(columns=['Node1', 'Node2'])
        recv_chains = {}
    
        for event_id, event in event_dict.items():
            # Add the node and corresponding edges to the full dag
            node1 = (event.get_partition().partition_id, event.event_id)
            full_dag_nodes.append(node1)
            next_event = event.get_next_event()
            matching_event = event.get_matching_event()
            if next_event is not None and next_event.event_id in event_dict.keys():
                full_dag_edges.loc[len(full_dag_edges.index)] = [node1, (next_event.get_partition().partition_id, next_event.event_id)]
            # Consider matching event for non-recv events only to create a DAG
            if event.event_name != "MpiRecv" and matching_event is not None and matching_event.event_id in event_dict.keys():
                full_dag_edges.loc[len(full_dag_edges.index)] = [node1, (matching_event.get_partition().partition_id, matching_event.event_id)]

            # Now, we want to create a DAG using only the MpiSend events
            if event.event_name == "MpiRecv":
                # We just want to keep track of Recv Events
                # recv_nodes.add(node1)
                continue

            # Non Recv Events
            send_dag_nodes.append(node1)
    
            # Traverse the next event until you find a non-recv event
            next_event = event.get_next_event()
            node2, recv_chain = get_next_nonrecv_edge(next_event)
            if node2 is not None:
                send_dag_edges.loc[len(send_dag_edges.index)] = [node1, node2]
                recv_chains[node2] = recv_chain
    
            # Traverse the next starting from the matching event until you find a non-recv event
            next_event = event.get_matching_event()
            node2, recv_chain = get_next_nonrecv_edge(next_event)
            if node2 is not None:
                send_dag_edges.loc[len(send_dag_edges.index)] = [node1, node2]
                recv_chains[node2] = recv_chain

        #recv_nodes_validation = set()
        for node in full_dag_nodes:
            if node not in recv_chains.keys():
                recv_chains[node] = []
        #    elif verify:
        #        for recv_node in recv_chains[node]:
        #            recv_nodes_validation.add(recv_node)
        
        #if verify:
        #    assert(recv_nodes == recv_nodes_validation)
        #    print (f"Recv Nodes Coverage Verified")
    
        return send_dag_nodes, send_dag_edges, recv_chains, full_dag_nodes, full_dag_edges

    def stride(self, verify = False):
        """ Computes the send dag and using network x assigns a stride to each node """
        def longest_distance_from_source(graph):
            # Perform topological sort
            top_order = list(nx.topological_sort(graph))

            # Initialize longest distances for each vertex
            longest_distances = {node: float('-inf') for node in graph.nodes}

            # The distance from a source to itself is 0
            for source in graph.nodes:
                longest_distances[source] = 0

            # Update longest distances for each vertex
            for node in top_order:
                for neighbor in graph.neighbors(node):
                    if longest_distances[node] + 1 > longest_distances[neighbor]:
                        longest_distances[neighbor] = longest_distances[node] + 1

            return longest_distances
            
        def longest_distance_from_source_full_dag(graph):
            # Perform topological sort
            top_order = list(nx.topological_sort(graph))

            # Initialize longest distances for each vertex
            longest_distances = {node: float('-inf') for node in graph.nodes}

            # The distance from a source to itself is 0
            for source in graph.nodes:
                longest_distances[source] = 0

            # Update longest distances for each vertex
            for node in top_order:
                parition_id, event_id = node
                event = self.get_event(parition_id, event_id)
                for neighbor in graph.neighbors(node):
                    if event.event_name == "MpiRecv":
                        if longest_distances[node] > longest_distances[neighbor]:
                            longest_distances[neighbor] = longest_distances[node]
                    else:
                        if longest_distances[node] + 1 > longest_distances[neighbor]:
                            longest_distances[neighbor] = longest_distances[node] + 1

            return longest_distances

        send_dag_nodes, send_dag_edges, recv_chains, full_dag_nodes, full_dag_edges = self.__create_send_dag(verify=verify)

        send_dag = nx.DiGraph()
        send_dag.add_nodes_from(send_dag_nodes)
        send_dag.add_edges_from(send_dag_edges.to_records(index=False))

        send_strides = longest_distance_from_source(send_dag)

        full_dag = nx.DiGraph()
        full_dag.add_nodes_from(full_dag_nodes)
        full_dag.add_edges_from(full_dag_edges.to_records(index=False))

        try:
            cycle = nx.find_cycle(full_dag, orientation='original')
        except nx.exception.NetworkXNoCycle:
            print("No cycle found.")
        else:
            print("Cycle found:", cycle)

        strides = longest_distance_from_source_full_dag(full_dag)

        send_strides_df = pd.DataFrame([(k[0], k[1], self.get_event(k[0], k[1]).event_name, recv_chains[k], v) for k, v in send_strides.items()], 
                               columns=['PartitionId', 'EventId', 'EventName', 'RecvChain', 'Stride'])

        strides_df = pd.DataFrame([(k[0], k[1], self.get_event(k[0], k[1]).event_name, recv_chains[k], v) for k, v in strides.items()], 
                               columns=['PartitionId', 'EventId', 'EventName', 'RecvChain', 'Stride'])
        # Now, we need to add MPIRecv back and assign strides to them

        #if verify:
        #    # Verify next node relations in recv chain
        #    for index, row in send_strides.iterrows():
        #        chain_verification = True
        #        next_node_id = row["EventId"]
        #        for node in row["RecvChain"]:
        #            current_node_event = leap.get_event(node[0], node[1])
        #            node_next_event = current_node_event.get_next_event()

        #            if (node_next_event.event_id != next_node_id):
        #                chain_verification = False
        #                print (f"Failed - {node} -> {next_node_id}")

        #            next_node_id = node[1]

        #    if chain_verification:
        #      print (f"Recv Chains Verified for next node relations") 

        return send_strides_df, strides_df


class Partition_DAG:
    # class to house Partition DAG
    # Not yet concrete, but need to start somewhere
    def __init__(self, root_partitions: [], partition_dict: Dict[int, Partition], all_processes: Set[int]) -> None:
        self.roots: Set[Partition] = set(root_partitions)
        self.df = pd.DataFrame(columns=['Partition ID', 'Distance'])
        self.partition_map: Dict[int, Partition] = {}
        self.all_processes = all_processes
        self.partition_map = partition_dict
    
    def create_dag(self) -> None:
        def create_dag_helper(node: Partition) -> None:
            print('node', node.partition_id)
            if node.partition_id not in self.df['Partition ID'].values.tolist():
                # self.partition_map[node.partition_id] = node
                # row = {'Partition ID': node.partition_id, 'Distance': 0}
                # self.df = self.df.append(row, ignore_index=True)
                self.df.loc[len(self.df.index)] = [node.partition_id, 0]
                # print('added', node.partition_id)
                for c in node.get_children():
                    # print()
                    p = self.partition_map[c]
                    # print(self.partition_map)
                    # print('child', p)
                    create_dag_helper(p)
        for p in self.roots:
            # print(self.roots)
            # print(p)
            # print(p.partition_id)
            create_dag_helper(p)

        

    def calculate_distance(self) -> None:
        # calculates the distance of each partition to root and updates the df
        def calc_distance_helper(node: Partition):
            # calculating distance for this node
            dist = 0
            parent_ids = node.get_parents()
            if len(parent_ids) != 0:
                for parent_id in parent_ids:
                    parent = self.partition_map[parent_id]
                    dist = max(parent.distance, dist)
                dist += 1
                print(dist)
            dist = max(node.distance, dist)
            node.distance = dist
            # self.df.at[self.df['Partition ID'] == node.partition_id]['Distance'] = dist
            index = self.df[self.df['Partition ID'] == node.partition_id].index[0]
            self.df.at[index, 'Distance'] = dist
        
            # calculating distance for child nodes
            for child_id in node.get_children():
                child_node = self.partition_map[child_id]
                # print('child node', child_node)
                calc_distance_helper(child_node)
        
        for root in self.roots:
            calc_distance_helper(root)

    def create_leaps(self) -> None:
        # creates leap partitions
        # assumes that distance has been calculated

        self.leaps: List[Leap] = []
        max_distance = int(self.df['Distance'].max())
        for i in range(max_distance + 1):
            partition_ids = self.df[self.df['Distance'] == i]['Partition ID'].values.tolist()
            leap = Leap(self.partition_map, self.all_processes, partition_ids)
            self.leaps.append(leap)

    def leap_distance(self, partition: Partition, leap_id: int, incoming: bool) -> float:
        # calculates the incoming/outgoing leap distance
        # TODO: implement this
        print(leap_id, len(self.leaps))
        if leap_id < 0 or leap_id >= len(self.leaps):
            return float('inf')
        if incoming:
            return partition.min_event_start - self.leaps[leap_id].max_event_end
        else:
            return self.leaps[leap_id].min_event_start - partition.max_event_end

    def much_smaller(self, incoming: int, outgoing: int) -> bool:
        # to calculate incoming << outgoing from the paper's psudo-code
        return incoming < (outgoing / 10)
    
    def will_expand(self, partition_id: int, leap: Leap) -> bool:
        # returns true if partition encompass processes that aren't in the leap
        return leap.partition_will_expand(partition_id)
    
    def absorb_partition(self, parent: Partition, child_id: int, parent_leap_id: int) -> None:
        # child partition is merged into parent partition
        print('absorbing partition', child_id, 'into partition', parent.partition_id)
        child = self.partition_map[child_id]

        child_parents = child.get_parents()
        child_children = child.get_children()
        child_leap_id = child.distance

        parent.merge_partition(child)

        for p in child_parents:
            p = self.partition_map[p]
            p.get_children()
        for c in child_children: 
            c = self.partition_map[c]
            c.get_parents()
        
        self.leaps[child_leap_id].remove_partition(child.partition_id)
        self.leaps[parent_leap_id].calc_processes()
        self.partition_map.pop(child.partition_id)
        

    def absorb_next_leap(self, leap_id: int) -> None:
        # merges leap_id + 1 into leap_id
        print('absorbing next leap', leap_id, leap_id + 1, len(self.leaps))
        self.leaps[leap_id].absorb_leap(self.leaps[leap_id + 1])
        self.leaps.pop(leap_id + 1)

    def merge_partition_to_leap(self, partition: Partition, leap_to_id: int, leap_from_id: int) -> None:
        # merges partition into leap
        print('merging partition', partition.partition_id, 'to leap', leap_to_id)
        self.leaps[leap_to_id].add_partition(partition.partition_id)
        self.leaps[leap_from_id].remove_partition(partition.partition_id)


        

    def complete_leaps(self, force_merge: bool):
        # the algorithm from the paper to "Complete leaps through merging paritions"
        all_leaps = self.leaps
        k = 0
        while k < len(all_leaps):
            leap = all_leaps[k]
            changed = True
            while changed and not leap.is_complete:
                changed = False
                as_list = list(leap.partitions_ids)
                for partition_id in as_list:
                    p = self.partition_map[partition_id]
                    incoming = self.leap_distance(p, k - 1, incoming = True)
                    outgoing = self.leap_distance(p, k + 1, incoming = False)
                    if self.much_smaller(incoming, outgoing):
                        self.merge_partition_to_leap(p, k - 1, k)
                        changed = True
                    else:
                        for c in p.children:
                            if self.will_expand(c, leap):
                                self.absorb_partition(p, c, k)
                                changed = True
            if not leap.is_complete and force_merge:
                self.absorb_next_leap(k)
            else:
                k = k + 1






    