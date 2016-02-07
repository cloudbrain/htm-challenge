import termios, fcntl, sys, os

from brainsquared.publishers.PikaPublisher import PikaPublisher

host = "localhost"
username = "guest"
pwd = "guest"

user = "brainsquared"
device = "openbci"
metric = "tag"
routing_key = "%s:%s:%s" % (user, device, metric)

pub = PikaPublisher(host, username, pwd)
pub.connect()
pub.register(routing_key)


info =  """Listening for keyboard input. \n
* Press 0 to tag neutral position.
* Press 1 to tag left hand.
* Press 2 to tag right hand.
"""
print info

fd = sys.stdin.fileno()

oldterm = termios.tcgetattr(fd)
newattr = termios.tcgetattr(fd)
newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
termios.tcsetattr(fd, termios.TCSANOW, newattr)

oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

try:
    while 1:
        try:
            tag = {"value": sys.stdin.read(1)}
            print "Got character %s" % tag
            
            pub.publish(routing_key, tag)
        except IOError: pass
finally:
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)