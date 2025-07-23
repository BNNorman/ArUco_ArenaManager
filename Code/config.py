class settings():
    STREAMING=False # set to True to enable Flask streaming

    MQTT_BROKER = 'localhost' # home PiNAS device
    MQTT_USER =   None    # might be brian
    MQTT_PASS = None        # might be Grunge42

    MQTT_CONNECT_TIMEOUT=10
    MQTT_KEEP_ALIVE=60

    MQTT_DEFAULT_TOPIC="pixelbot/#" # everything
    MQTT_LOCATION_TOPIC="pixelbot/loc"

    VIDEO_WIDTH=1920
    VIDEO_HEIGHT=790

    CALIBRATION_MARKER=200	# marker to use for calibration
    CALIBRATION_SIZE=105	# mm size on paper

    BW_MIN_THRESH=60        # B/W threshold min, the lower the better

    # arena markers are not broadcast (for now)
    ARENA_ARUCO_CORNERS=[100,101,102,103]
    ARENA_ARUCO_MARKERS=(104,200) # min,max

    PIXELBOT_ID_RANGE=(10,50) # min max

    # assuming equal teams
    TEAM0_BASES=(104,105,106,107)
    TEAM1_BASES=(108,109,110,111)
    ALL_BASES=TEAM0_BASES+TEAM1_BASES
    NUM_TEAM_BASES=len(ALL_BASES)
    NUM_PLAYERS_PER_TEAM=len(TEAM0_BASES) # should be same as TEAM1
    TEAM1_COLOUR="red" # for pixel ring setting
    TEAM2_COLOUR="blue"
