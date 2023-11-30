from .event import Event

class Partition:
    def __init__(self, partition_id, event_list : list[Event]):
        self.partition_id = partition_id
        self.event_list = event_list
        for event in self.event_list:
            event.add_partition(self)
        self.parents = []
        self.children = []

        # variables for leap
        self.distance = 0

        # Variables for Tarjan's algorithm
        self.visited = False
        self.index = -1
        self.low_link = -1
      
    def initialize_for_tarjan(self):
        self.visited = False
        self.index = -1
        self.low_link = -1

    def __eq__(self, other):
        return self.partition_id == other.partition_id

    def __ne__(self, other):
        return self.partition_id != other.partition_id
    
    def merge_partition(self, other):
        self.event_list.extend(other.event_list)
        self.get_parents()
        self.get_children()
        for event in self.event_list:
            event.add_partition(self)
        return self

    def add_event(self, e):
        self.event_list.append(e)
        e.add_partition(self)
    
    def get_parents(self):
        self.parents = set()
        for event in self.event_list:
            if event.prev_event != None and event.prev_event.partition != self:
                self.parents.add(event.prev_event.partition.partition_id)
        
        return self.parents

    def get_children(self): 
        self.children = set()
        for event in self.event_list:
            if event.next_event != None and event.next_event.partition != self:
                self.children.add(event.next_event.partition.partition_id)
        return self.children
      
    def get_first_event(self):
        return self.event_list[0]

    @staticmethod
    def tarjan_strongly_connected(graph):
        """ Tarjan's Algorithm for finding strongly connected components
        Parameters
        ----------
        graph : dict
            Dictionary of partition_id -> Partition
        Returns
        -------
        components : list
            List of strongly connected components
        """
        index = 0
        stack = []
        components = []
        visited = set()

        def strong_connect(partition):
            nonlocal index, stack, components, visited

            partition.index = index
            partition.low_link = index
            index += 1

            stack.append(partition)
            visited.add(partition.partition_id)

            for child_id in partition.get_children():
                if child_id not in visited:
                    child = graph[child_id]
                    strong_connect(child)
                    partition.low_link = min(partition.low_link, child.low_link)
                elif graph[child_id] in stack:
                    partition.low_link = min(partition.low_link, graph[child_id].index)

            if partition.low_link == partition.index:
                component = []
                while stack:
                    top = stack.pop()
                    component.append(top.partition_id)
                    if top == partition:
                        break
                components.append(component)

        for _,partition in graph.items():
            partition.initialize_for_tarjan()
        
        for partition_id, partition in graph.items():
            if partition_id not in visited:
                strong_connect(partition)

        return components

    @staticmethod
    def merge_strongly_connected_components(graph, components):
        """ Merge strongly connected components into one partition
        Parameters
        ----------
        graph : dict
            Dictionary of partition_id -> Partition
        components : list
            List of strongly connected components
        Returns
        -------
        merged_graph : dict
            Dictionary of partition_id -> Partition
        """
        # Note that the original graph is also modified since merge_partition is inplace so one 
        # should not use the original graph after calling this function
        merged_graph = {}
        for component in components:
            merged_graph[component[0]] = graph[component[0]]
            if len(component) > 1:
                for partition_id in component[1:]:
                    merged_graph[component[0]].merge_partition(graph[partition_id])
        return merged_graph