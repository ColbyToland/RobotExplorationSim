"""
Messages passed by robots
"""

from WiFi import Message


class OccupancyGridMessage(Message):
    TYPE = "Occupancy Grid"
    def __init__(self, sender, bot_name=None, oc_grid=None, timestamp=None, receivers=Message.BROADCAST):
        super().__init__(sender, msg_type = OccupancyGridMessage.TYPE, receivers=receivers)
        self.bot_name = bot_name
        self.bot_map = oc_grid
        self.timestamp = timestamp

    @property
    def data(self):
        return (self.bot_name, {'map': self.bot_map, 'timestamp': self.timestamp})
    
    @data.setter
    def data(self, value):
        self.bot_name = value[0]
        self.bot_map = value[1]['map']
        self.timestamp = value[1]['timestamp']