
class settings():
    STREAMING=False # set to True to enable Flask streaming




    VIDEO_RES=[(640,480),(1920,1080),(1280,720),(1280,960)]

    VIDEO_WIDTH,VIDEO_HEIGHT=VIDEO_RES[1]

    CALIBRATION_MARKER=49	    # marker to use for calibration
    CALIBRATION_SIZE_MM=54		# mm side size on paper

    HOMEBASE_SIDELEN_MM=54      # used to check if bot has got to the base


    BW_THRESHOLD=190 # not using thresholding now

    baseId=0
    allKnownBots={
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
    baseId+20:("Goldilocks","CLB-E66164084320A62E"),
	baseId+21:("Deep Purple","CLB-E661640843492631"),
	baseId+22:("Nobody","CLB-E66164084367842E")
    }

    BOUNDARY_MARGIN=100 # used to define arena rect

    INITIAL_SCALE_FACTOR=1.2 # empirically determined - works best with the ball 

    BALL_DIA_MM=120
    BALL_TOLERANCE=0.04 # %

    # setup for pixelbot teams
    # assuming equal sized teams and bases
   
    TEAM0_BOTS=[0,1,2,20]
    TEAM1_BOTS=[7,8,9,21]
    
    NUM_BOTS=1 # set this to len(TEAM0_BOTS+TEAM1_BOTS) when all bots are present
    
    TEAM0_BASES=[40,41,42,43]
    TEAM1_BASES=[44,45,46,47]
    PAIRINGS={0:40,1:41,2:42,20:43,7:44,8:45,9:46,21:47}
    
    
    TEAM0_COLOUR="R"
    TEAM1_COLOUR="B"
