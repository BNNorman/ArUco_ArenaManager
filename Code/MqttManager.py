"""
MqttManager.py

a class to encapsulate MQTT handling

mqttc=MqttManager.MQTT()

mqttc.setCallback(which,target_function)

mqttc.publish(topic,payload)

mosquitto_sub -h 192.168.1.105 -t "pixelbot"
mosquitto_pub -h 192.168.1.105 -t "pixelbot" -m "hey"

logging will be setup by the Arena/Game manager

"""

import paho.mqtt.client as paho
import sys
import time
import logging

from config import settings

class MQTT():


    def __init__(self,broker=settings.MQTT_BROKER,user=settings.MQTT_USER,password=settings.MQTT_PASS, defaultTopic=settings.MQTT_DEFAULT_TOPIC):

        self.mqttc=paho.Client()
        self.topicCallbacks={}      # [topic]=callback
        self.user=user
        self.password=password
        self.broker=broker
        self.defaultTopic=defaultTopic
                
        # connect to the mqtt broker
        self.connectToBroker()
        


    def __del__(self):
        self.mqttc.loop_stop()
  

    #####################################
    #
    # on_connect() callback from MQTT broker
    #
    def on_connect(self,mqttc, obj, flags, rc):

        if rc==0:
            self.brokerConnected=True
            logging.info(f"on_connect(): callback ok, subscribing to Topic: {self.defaultTopic}")
            self.mqttc.subscribe(self.defaultTopic, 0)
        else:
            self.brokerConnected=False
            logging.info(f"on_connect(): callback error rc={rc}")


    #####################################
    #
    # subscribe(topic,callback)
    #
    # subscribes to the topic and sets the callback
    # function
    def subscribe(self,topic,callback):
        if not self.brokerConnected: 
            try:
                self.connectToBroker()
            except Exception as e:
                logging.error(f"subscribe: broker not connected {e}")
                return    
        
        if not callable(callback):
            logging.error(f"subscribe: callback is not callable.")
            return
            
        self.topicCallbacks[topic]=callback
        
        logging.info(f"Subscribe: topic {topic} added.")
            
        self.mqttc.subscribe(topic, 0)
        return True

    def unsubscribe(self,topic):
        try:
            del self.topicCallbacks[topic]
            logging.info(f"Unsubscribe: callback for topic {topic} removed")
        except:
            pass
        

    def publishPayload(self,topic,payload):
        '''
        meant to be called by user
        :param topic:
        :param payload:
        :return:
        '''

        logging.info(f"publishPayload: publish to topic {topic} payload {payload}")
        self.mqttc.publish(topic,payload)

    ################################
    #
    # on_message() MQTT broker callback
    #
    # redirects to any alternative callback set by users
    #
    def on_message(self,mqttc, obj, msg):
        """
        try to call a topic callback before the default on_message
        """
        topic=msg.topic
        payload=msg.payload.decode("utf-8")
        
        logging.info(f"on_message: topic {topic} payload {payload}")
        
        try:
            func=self.topicCallbacks[topic]
            func(topic,payload)
        except:
            logging.warning(f"No callback registered for topic {topic}")
        


    ################################
    #
    # on_subscribe() MQTT Broker callback
    #
    # information only
    #
    def on_subscribe(self,mqttc,obj,mid,granted_qos):
        global logging
        logging.info(f"on_subscribe(): Subscribed to {mqttc.msg.topic} qos {granted_qos} with mid=%s",str(mid))


    ################################
    #
    # connectToBroker
    #
    #
    def connectToBroker(self):

        self.brokerConnected=False

        logging.info("connectToBroker(): Trying to connect to the MQTT broker")

        # on_message calls may be redirected
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_subscribe = self.on_subscribe
        self.mqttc.on_message = self.on_message

        # use authentication?
        if self.user is not None:
            logging.info("connectToBroker(): using MQTT authentication")
            self.mqttc.username_pw_set(username=self.user, password=self.password)
        else:
            logging.info("main(): not using MQTT autentication")

        # terminate if the connection takes too long
        # on_connect sets a global flag brokerConnected
        startConnect = time.time()
        self.mqttc.loop_start()	# runs in the background, reconnects if needed
        self.mqttc.connect(self.broker, keepalive=settings.MQTT_KEEP_ALIVE)

        while not self.brokerConnected:
            # "connected" callback may take some time
            if (time.time() - startConnect) > settings.MQTT_CONNECT_TIMEOUT:
                logging.error(f"connectToBroker(): broker on_connect time out {settings.MQTT_CONNECT_TIMEOUT}")
                return False

        logging.info(f"connectToBroker(): Connected to MQTT broker after {time.time()-startConnect} s")
        return True

if __name__ == "__main__":
    def hello_callback(topic,payload):
        print(f"hello_callback: topic {topic} payload {payload}")
    
    def position_callback(topic,payload):
        print(f"position_callback: topic {topic} payload {payload}")    
    
    myMqtt=MQTT()
    
    myMqtt.subscribe("pixelbot/hello",hello_callback)
    myMqtt.subscribe("pixelbot/position",position_callback)
    
    myMqtt.publishPayload("pixelbot/hello","Hello there")
    myMqtt.publishPayload("pixelbot/position","where am i?")

    
    print("Waiting for callbacks")
    time.sleep(10)
    print("finished")
    
    
    
    
    
