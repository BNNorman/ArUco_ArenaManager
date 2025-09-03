import serial

ser = serial.Serial(
    port='/dev/ttyACM0',
    baudrate=9600,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.SEVENBITS
)


program="""pythonish
begin
println "Active.txt is running"
dist=0
angle=0
forever
  busy=dist+angle
  if angle!=0
    red
    turn angle
    angle=0
  if dist!=0
    yellow
    move dist nowait
    while @moving==1
      if @distance<100
        ang=@random-6
        ang=10*ang
        turn ang
        move 100
    dist=0
  if busy>0
    green
    send 1
  else
    magenta
end
exit
"""

def sendPythonish():
    ser.write(program.encode("utf-8"))
    print("Restart the bot to load the program")

    
sendPythonish()

