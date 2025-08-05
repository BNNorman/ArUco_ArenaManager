"""
MqttManager.py

a class to encapsulate MQTT handling

mqttc=MqttManager.MQTT()

mqttc.setCallback(which,target_function)

mqttc.publish(topic,payload)

mosquitto_sub -h broker -t "pixelbot"
mosquitto_pub -h broker -t "pixelbot" -m "hey"

logging will be setup by the Arena/Game manager

"""

import paho.mqtt.client as paho
import sys
import time
import logging

from config import settings
from mySecrets import MQTT_BROKER,MQTT_USER,MQTT_PASS

logger=logging.getLogger(__name__)

class MQTT():


    def __init__(self,broker=MQTT_BROKER,user=MQTT_USER,password=MQTT_PASS, defaultTopic=settings.MQTT_COMMAND_TOPIC):

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
                logger.error(f"subscribe: broker not connected {e}")
                return    
        
        if not callable(callback):
            logger.error(f"subscribe: callback is not callable.")
            return
            
        self.topicCallbacks[topic]=callback
        
        logger.info(f"Subscribe: topic {topic} added.")
            
        self.mqttc.subscribe(topic, 0)
        return True

    def unsubscribe(self,topic):
        try:
            del self.topicCallbacks[topic]
            logger.info(f"Unsubscribe: callback for topic {topic} removed")
        except:
            pass
        

    def publishPayload(self,topic,payload):
        '''
        meant to be called by user
        :param topic:
        :param payload:
        :return:
        '''

        logger.info(f"publishPayload: publish to topic {topic} payload {payload}")
        try:
            (res,qos)=self.mqttc.publish(topic,payload) # default Qos=1
            logger.info(f"publish returned res {res} qos {qos}")
        except Exception as e:
            logger.warn(f"publish failed exception: {e}")
            
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
            logger.warning(f"No callback registered for topic {topic}")
        


    ################################
    #
    # on_subscribe() MQTT Broker callback
    #
    # information only
    #
    def on_subscribe(self,mqttc,obj,mid,granted_qos):
        logger.info(f"on_subscribe(): Subscribed with mid {mid} granted_qos {granted_qos}")

    def on_publish(self,mqttc,userdata, mid): #, reason_code, properties):
        logger.info("on_publish callback")
    ################################
    #
    # connectToBroker
    #
    #
    def connectToBroker(self):

        self.brokerConnected=False

        logger.info("connectToBroker(): Trying to connect to the MQTT broker")

        # on_message calls may be redirected
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_subscribe = self.on_subscribe
        self.mqttc.on_message = self.on_message
        self.mqttc.on_publish = self.on_publish

        # use authentication?
        if self.user is not None:
            logger.info("connectToBroker(): using MQTT authentication")
            self.mqttc.username_pw_set(username=self.user, password=self.password)
        else:
            logger.info("main(): not using MQTT autentication")

        # terminate if the connection takes too long
        # on_connect sets a global flag brokerConnected
        startConnect = time.time()
        self.mqttc.loop_start()	# runs in the background, reconnects if needed
        self.mqttc.connect(self.broker, keepalive=settings.MQTT_KEEP_ALIVE)

        while not self.brokerConnected:
            # "connected" callback may take some time
            if (time.time() - startConnect) > settings.MQTT_CONNECT_TIMEOUT:
                logger.error(f"connectToBroker(): broker on_connect time out {settings.MQTT_CONNECT_TIMEOUT}")
                return False

        logger.info(f"connectToBroker(): Connected to MQTT broker after {time.time()-startConnect} s")
        return True

if __name__ == "__main__":
    
    # Note this works
    
    logging.basicConfig(filename='MqttManager.log', filemode="w",level=logging.INFO)
    logger.info('Started')

    
    botId=20 # goldilocks
    botName,addr=settings.allKnownBots[botId]
    
    #mosquitto_pub -h mqtt.connectedhumber.org  -t "lb/command/CLB-E66164084320A62E" -P 'i8ew02261TCYdbVSnG1e' -u littleboxes -m
    
    topic="lb/command/CLB-E66164084320A62E"
    
    def subscribe_callback(topic,payload):
        print(f"subscribe command_callback: topic {topic} payload {payload}")
    
    myMqtt=MQTT() # automatically uses user/pass/host from mySecrets.py
    myMqtt.subscribe(topic,subscribe_callback)
    myMqtt.publishPayload(topic,"***MR90")
    myMqtt.publishPayload(topic,"***MF100")

    time.sleep(10)
    print("finished")
    
    
    
    
    
