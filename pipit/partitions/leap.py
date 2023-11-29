from . import Partition, Event
import pandas as pd

class Leap:
    def __init__(self) -> None:
        self.partitions = set(Partition)

class Partition_DAG:
    # class to house Partition DAG
    # Not yet concrete, but need to start somewhere
    def __init__(self, partitions: []) -> None:
        self.roots = set(partitions)
        self.df = pd.DataFrame(columns=['Partition', 'Distance', 'Processes Involved'])

    def calculate_distance(self) -> None:
        # calculates the distance of each partition to root and updates the df
        def calc_distance_helper(node: Partition):
            # calculating distance for this node
            dist = 0
            if len(node.parents) != 0:
                for parent in node.parents:
                    dist = max(parent.distance, dist)
                dist += 1
            dist = max(node.distance, dist)
            node.distance = dist
            self.df[self.df['Partition'] == node]['Distance'] = dist
        
            # calculating distance for child nodes
            for child_node in node.children:
                calc_distance_helper(child_node)
        
        for root in self.roots:
            calc_distance_helper(root)

    def create_leaps(self) -> None:
        # creates leap partitions
        # assumes that distance has been calculated

        self.leaps = []
        max_distance = self.df['Distance'].max()
        for i in range(max_distance):
            partitions = self.df[self.df['Distance'] == i]['Partition'].values.tolist()
            leap = Leap(partitions)
            self.leaps.append(leap)




    