"""
Your awesome Distance Vector router for CS 168
"""

import sim.api as api
import sim.basics as basics
import sys
import time


# We define infinity as a distance of 16.
INFINITY = 16
EXPIRED = 15
# DEFAULT_TIMER_INTERVAL = 3

class DVRouter (basics.DVRouterBase):
  #NO_LOG = True # Set to True on an instance to disable its logging
  POISON_MODE = True # Can override POISON_MODE here
  #DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing

  def __init__ (self):
    """
    Called when the instance is initialized.

    You probably want to do some additional initialization here.
    """
    self.forward_table = {} # store keys for every host {host: true}

    self.latency_table = {} # store latencies for every host {host: latency}
    self.time_table = {} # store time link created for everey host {host: time}
    self.output_port_table = {} # store port for every host {host: port}

    self.port_table = {} # store port for self
    self.host_table = {} # store host for self
    self.links = {} # store latencies for self

    #self.routing_table = {} store all information {destination_host {port: [latency, time]}}

    self.start_timer()

  def handle_link_up (self, port, latency):
    """
    Called by the framework when a link attached to this Entity goes up.

    The port attached to the link and the link latency are passed in.
    """
    self.links[port] = latency 
    self.port_table[port] = {}
    for destination_host in self.forward_table.keys():
      #print send link up
      self.send(basics.RoutePacket(destination_host, latency_table[destination_host]), port, False)

  def add_to_routing_table(self, destination, latency, port, api.current_time()):
    if len(self.routing_table.items()) > 0:
      if destination_host in self.routing_table.keys():
        del self.routing_table[destination_host]
      self.routing_table[destination_host] = {port: [latency, current_time]}
    else:
      self.routing_table = {destination_host: {port: [latency, current_time]}}  

  def handle_link_down (self, port):
    """
    Called by the framework when a link attached to this Entity does down.

    The port number used by the link is passed in.
    """
    del self.links[port]
    del self.port_table[port]
    for destination_host in self.host_table.keys():
      if self.host_table[destination_host] == port:
        del self.host_table[destination_host]

    for destination_host in self.forward_table:
      if self.output_port_table[destination_host] == port: 
        update_latency = INFINITY
        update_port = port
        for packet_source in self.port_table.keys():
          if (destination_host in self.port_table[packet_source] and self.port_table[packet_source][destination_host] < INFINITY) and (self.links[packet_source] + self.port_table[packet_source][destination_host] < update_latency and self.links[packet_source] + self.port_table[packet_source][destination_host] < INFINITY):
              update_latency = self.links[packet_source] + self.port_table[packet_source][destination_host]
              update_port = packet_source 

        self.forward_table[destination_host] = True 
        self.latency_table[destination_host] = update_latency
        self.time_table[destination_host] = api.current_time()
        self.output_port_table = update_port

        if self.POISON_MODE:
          #print "sent poison mode link down"
          self.send(basics.RoutePacket(destination_host, update_latency), update_port, True)

  def handle_rx (self, packet, port):
    """
    Called by the framework when this Entity receives a packet.

    packet is a Packet (or subclass).
    port is the port number it arrived on.

    You definitely want to fill this in.
    """
    if isinstance(packet, basics.RoutePacket):
      self.handle_route_packet(packet, port)

    elif isinstance(packet, basics.HostDiscoveryPacket):
      self.handle_discovery_packet(packet, port)

    else:
      self.handle_data_packet(packet, port)

  def handle_route_packet(self, packet, port):
      self.port_table[port][packet.destination] = packet.latency
      special_send = False 

      if packet.destination in self.forward_table.keys(): 
        if self.output_port_table[packet.destination] == port: 
          starting_latency = self.latency_table[packet.destination]
          starting_port = self.output_port_table[packet.destination]
          update_latency = self.links[port] + packet.latency
          update_port = port

          for packet_source in self.port_table.keys():
            if packet_source != port and packet.destination in self.port_table[packet_source] and self.port_table[packet_source][packet.destination] < INFINITY:
              if self.links[packet_source] + self.port_table[packet_source][packet.destination] < update_latency:
                update_latency = self.links[packet_source] + self.port_table[packet_source][packet.destination]
                update_port = packet_source 

          if update_latency > INFINITY:
            special_send = True
            update_latency = INFINITY

          if not (update_latency == starting_latency and update_port == starting_port):
            if (update_latency == INFINITY and (self.POISON_MODE or special_send)) or update_latency != INFINITY:
              #print "send infinity update_latency"
              self.send(basics.RoutePacket(packet.destination, update_latency), update_port, True)
          
          self.forward_table[packet.destination] = True
          self.latency_table[packet.destination] = update_latency
          self.output_port_table[packet.destination] = update_port
          self.time_table[packet.destination] = api.current_time()

        else:
          if self.links[port] + packet.latency < self.output_port_table[packet.destination]:
            self.forward_table[packet.destination] = True
            self.latency_table[packet.destination] = self.links[port] + packet.latency
            self.output_port_table[packet.destination] = port
            self.time_table[packet.destination] = api.current_time()

            # print "send handle_route packet for no equal ports"
            self.send(basics.RoutePacket(packet.destination, self.latency_table[packet.destination]), self.output_port_table[packet.destination], True) 
          
          if self.links[port] + self.latency_table[packet.destination] < packet.latency:
            del self.port_table[port][packet.destination]

      else:

        self.forward_table[packet.destination] = True
        self.latency_table[packet.destination] = min(INFINITY, self.links[port] + packet.latency)
        self.output_port_table[packet.destination] = port
        self.time_table[packet.destination] = api.current_time()

        #print "send handle_route packet for no in keys"
        self.send(basics.RoutePacket(packet.destination, self.latency_table[packet.destination]), port, True)

  def handle_discovery_packet(self, packet, port):

      self.forward_table[packet.src] = True
      self.latency_table[packet.destination] = self.links[port] 
      self.output_port_table[packet.destination] = port
      self.time_table[packet.destination] = api.current_time()
      self.host_table[packet.src] = port

      #print "send discovery packet discovery"
      self.send(basics.RoutePacket(packet.src, self.latency_table[packet.destination]), self.output_port_table[packet.destination], True)

  def handle_data_packet(self, packet, port):
      if packet.dst in self.forward_table.keys():
        if self.latency_table[packet.destination]  < INFINITY and self.output_port_table[packet.destination] != port:
          self.send(packet, self.output_port_table[packet.dst], False)

  def handle_timer (self):
    """
    Called periodically.

    When called, your router should send tables to port_table.  It also might
    not be a bad place to check for whether any entries have expired.
    """
    current_time = api.current_time()
    for destination_host in self.forward_table.keys():
      if not destination_host in self.host_table:
        if current_time - self.time_table[packet.destination] >= EXPIRED or self.latency_table[packet.destination] >= INFINITY: 
          if self.output_port_table[packet.destination] in self.port_table:
            del self.port_table[self.output_port_table[packet.destination]][destination_host]
          del self.forward_table[destination_host]
          del self.latency_table[destination_host]
          del self.output_port_table[destination_host]
          del self.time_table[desitnation_host]

    for destination_host in self.forward_table.keys():
      if (self.latency_table[destination_host] == INFINITY and self.POISON_MODE) or self.latency_table[destination_host] != INFINITY:
        self.send(basics.RoutePacket(item, self.latency_table[destination_host]), self.output_port_table[destination_host], True)

