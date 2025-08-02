class settings():
    STREAMING=False # set to True to enable Flask streaming

    #MQTT_BROKER = 'localhost' # home PiNAS device
    MQTT_BROKER='ns349814.ip-178-32-221.eu'
    #MQTT_USER =   None    # might be brian
    MQTT_USER = "cleverlittleboxes"
    #MQTT_PASS = None        # 
    MQTT_PASS="Boxing-Clever-Marmoset!"

    MQTT_CONNECT_TIMEOUT=10
    MQTT_KEEP_ALIVE=60

    MQTT_COMMAND_TOPIC="lb/command/" # everything
    MQTT_LOCATION_TOPIC="pixelbot/loc"


    VIDEO_RES=[(640,480),(1920,1080),(1280,720)]

    VIDEO_WIDTH,VIDEO_HEIGHT=VIDEO_RES[2]

    CALIBRATION_MARKER=49	    # marker to use for calibration
    CALIBRATION_SIZE_MM=52		# mm side size on paper
    CALIBRATION_PERIM_MM=4*52

    BW_THRESHOLD=190

    baseId=0
    pixelBots={
    baseId:("Agent Orange","CLB-da3371"), 
    baseId+1: ("Alloys Boys","CLB-d3343a"),
    baseId+2:("Blue Steel","CLB-1cea51"),
    baseId+3:("Colonel White","CLB-0f9b77"),
    baseId+4:("Doctor Black","CLB-2c7e79"),
    baseId+5:("Green Hoops","CLB-08ae9a"),
    baseId+6:("Mr Green","CLB-cf3b1f"),
    baseId+7:("Old Red","CLB-c23d87"),
    baseId+8:("Sunshine","CLB-c09546"),
    baseId+9:("Violet Redwheels","CLB-1df4e3"),
	baseId+20:("Deep Purple","CLB-E661640843492631"),
	baseId+21:("Goldilocks","CLB-E66164084320A62E"),
	baseId+22:("Nobody","CLB-E66164084367842E")
    }


    INITIAL_SCALE_FACTOR=1.2 # empirically determined - works best with the ball 

    #INITIAL_DP_MM=90/25.4   # dots per mm of the video image
    BALL_DIA_MM=120
    BALL_TOLERANCE=0.2

    # 
    PIXELBOTS=[0,1,2,3,4,5,6,7,8,9,20,21]
    # assuming equal teams
    TEAM0_BASES=[40,41,42,43]
    TEAM1_BASES=[44,45,46,47]
    NUM_TEAM_BASES=len(TEAM0_BASES)
    ALL_BASES=2*NUM_TEAM_BASES
    NUM_PLAYERS_PER_TEAM=len(TEAM0_BASES)
    TEAM0_COLOUR="red"
    TEAM1_COLOUR="blue"
