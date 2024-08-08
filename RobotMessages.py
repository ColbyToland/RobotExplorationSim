"""
Messages passed by robots
"""

import arcade
from typing import Optional

from WiFi import Message, ReceiverList


type OccupancyGridMessageData = tuple[str, dict]

class OccupancyGridMessage(Message):
    TYPE = "Occupancy Grid"
    def __init__(self, sender: arcade.Sprite, bot_name: Optional[str]=None, oc_grid: Optional[object]=None, timestamp: Optional[int]=None, receivers: ReceiverList=Message.BROADCAST):
        super().__init__(sender, msg_type = OccupancyGridMessage.TYPE, receivers=receivers)
        self.bot_name = bot_name
        self.bot_map = oc_grid
        self.timestamp = timestamp

    @property
    def data(self) -> OccupancyGridMessageData:
        return (self.bot_name, {'map': self.bot_map, 'timestamp': self.timestamp})
    
    @data.setter
    def data(self, value: OccupancyGridMessageData):
        self.bot_name = value[0]
        self.bot_map = value[1]['map']
        self.timestamp = value[1]['timestamp']