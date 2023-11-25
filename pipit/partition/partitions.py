# Class to store individual events and info on their matching events
class Event:
    def __init__(self, event_type, event_id, time, process, matching_id):
        self.event_type = event_type
        self.event_id = event_id
        self.event_time = time
        self.process = process
        self.matching_event_id = matching_id

        # Lamport Ordering information per event
        self.prev_event = None
        self.next_event = None

        # For now just assumed that there is one matching event
        self.matching_event = None

        self.partition = None
    
    def add_next(self, e):
        self.next_event = e
    
    def add_prev(self, e):
        self.prev_event = e

    def add_matching(self, e):
        self.matching_event = e

    def add_partition(self, p):
        self.partition = p

class Partition:
    @staticmethod
    def createSingleEventPartition(event_type, event_id, time, process, matching_id):
        return Partition([Event(event_type, event_id, time, process, matching_id)])

    def __init__(self, event_list : list[Event]):
        for event in event_list:
            event.add_partition(self)
        self.parents = []
        self.children = []

    def add_event(self, e):
        self.event_list.append(e)
        e.add_partition(self)
    
    def get_parents(self):
        for event in event_list:
            if event.prev_event != None:
                self.parents.append(event.prev_event)
        
        return self.parents

    def get_children(self): 
        for event in event_list:
            if event.next_event != None:
                self.children.append(event.next_event)
        return self.children
      
    def get_first_event(self):
        return self.event_list[0]

    
      
        
