from .event import Event

class Partition:
    def __init__(self, partition_id, event_list : list[Event]):
        self.partition_id = partition_id
        self.event_list = event_list
        for event in self.event_list:
            event.add_partition(self)
        self.parents = []
        self.children = []

    def __eq__(self, other):
        return self.partition_id == other.partition_id

    def __ne__(self, other):
        return self.partition_id != other.partition_id

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