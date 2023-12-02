from . import Partition, Event
import pandas as pd
from typing import Set, List, Dict

class Leap:
    def __init__(self, partition_map: Dict[int, Partition], all_processes: Set[int], partition_ids = []) -> None:
        self.partitions_ids: Set[int] = set(partition_ids)
        self.processes: Set[int] = set()
        self.all_processes = all_processes
        self.partition_map = partition_map
        self.is_complete: bool = False
        self.calc_processes()

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

    def add_partition(self, partition_id: int) -> None:
        self.partitions_ids.add(partition_id)
        self.processes = self.processes.union(self.partition_map[partition_id].processes)
        self.calc_is_complete()

    def partition_will_expand(self, partition_id: int) -> bool:
        # returns true if partition encompass processes that aren't in the leap
        diff = self.partition_map[partition_id].processes.difference(self.processes)
        return len(diff) > 0
    
    def absorb_leap(self, leap: 'Leap') -> None:
        # merges leap into this leap
        self.partitions_ids = self.partitions_ids.union(leap.partitions_ids)
        self.processes = self.processes.union(leap.processes)
        self.calc_is_complete()
    

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
            leap = Leap(partition_ids)
            self.leaps.append(leap)

    def leap_distance(self, partition: Partition, leap_id: int) -> float:
        # calculates the incoming/outgoing leap distance
        # TODO: implement this
        pass

    def much_smaller(self, incoming: int, outgoing: int) -> bool:
        # to calculate incoming << outgoing from the paper's psudo-code
        return incoming < (outgoing / 10)
    
    def will_expand(self, partition: Partition, leap: Leap) -> bool:
        # returns true if partition encompass processes that aren't in the leap
        return leap.partition_will_expand(partition.partition_id)
    
    def absorb_partition(self, parent: Partition, child: Partition, parent_leap_id: int) -> None:
        # child partition is merged into parent partition
        parent.parents = parent.parents.union(child.parents)
        parent.children = parent.children.union(child.children)
        parent.events = parent.event_list.union(child.events)
        for event in child.event_list:
            event.partition = parent
        
        child_leap_id = child.distance
        self.leaps[child_leap_id].remove_partition(child.partition_id)
        self.leaps[parent_leap_id].calc_processes()
        self.partition_map.pop(child.partition_id)
        

    def absorb_next_leap(self, leap_id: int) -> None:
        # merges leap_id + 1 into leap_id
        self.leaps[leap_id].absorb_leap(self.leaps[leap_id + 1])
        self.leaps.pop(leap_id + 1)

    def merge_partition_to_leap(self, partition: Partition, leap_to_id: int, leap_from_id: int) -> None:
        # merges partition into leap
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
                for partition_id in leap.partitions_ids:
                    p = self.partition_map[partition_id]
                    incoming = self.leap_distance(p, k - 1)
                    outgoing = self.leap_distance(p, k + 1)
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






    