import asyncio
import numpy as np


class Message:
    """ Base class for all messages """
    BROADCAST = []

    def __init__(self, sender, msg_type='Base', data=None, receivers=BROADCAST):
        self.sender_id = sender.name
        self.sender_position = sender.position
        self.transmission_range = sender.comm_range
        self.receiver_list = receivers
        self.msg_type = msg_type
        self._data = data

    def valid_receiver(self, receiver_id):
        return self.receiver_list == Message.BROADCAST or receiver_id in self.receiver_list

    def reachable_receiver(self, receiver):
        d = float(np.linalg.norm(np.array(self.sender_position)-np.array(receiver.position)))
        return d <= self.transmission_range and d <= receiver.comm_range

    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = value


class WiFi:
    """ Simulate wireless communication in the world """

    def __init__(self):
        self.msg_queue = asyncio.Queue()

    async def send_message(self, msg):
        if not isinstance(msg, Message):
            raise TypeError(f"Attempted to send something that isn't a message: {type(msg)}")
        await self.msg_queue.put(msg)

    async def update(self, robot_list):
        while not self.msg_queue.empty():
            try:
                msg = self.msg_queue.get_nowait()
            except asyncio.QueueEmpty:
                # Shouldn't happen since not empty is the loop conditional
                break

            async with asyncio.TaskGroup() as tg:
                for robot_sprite in robot_list:
                    if robot_sprite.name == msg.sender_id:
                        # Don't echo back to the sender
                        continue
                    if msg.reachable_receiver(robot_sprite):
                        tg.create_task(robot_sprite.rcv_msg(msg))