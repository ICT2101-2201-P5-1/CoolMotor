import telnetlib
HOST = "192.168.43.174"
PORT = 80

def sendCommands(commands):
    tn = telnetlib.Telnet(HOST,PORT)
    print(commands)
    print("Writing data")
    tn.write(commands)
    print("DISCONNECT")

def receiveData():
    tn = telnetlib.Telnet(HOST,PORT)
    print("Writing data")
    tn.write(b'RECEIVING')
    print("Reading data")
    data = tn.read_until(b'END').decode("utf-8") 
    print(data)
    start = data.find("d=") + len("d=")
    end = data.find("s=")
    distance= data[start:end]

    start = data.find("s=") + len("s=")
    end = data.find(" END")
    speed = data[start:end]

    print(distance)
    
    print("DISCONNECT")
    return data[2], distance, speed







    
