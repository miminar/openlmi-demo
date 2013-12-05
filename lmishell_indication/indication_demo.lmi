import sys
import time
import pynotify
import os
import getpass

if not pynotify.init("lmishell_indication"):
    sys.exit(4)

def useradd_notifier(indication, **kwargs):
    sys.stdout.write("new user\n")
    n = pynotify.Notification("New user", "A new user was added to the system")

    if not n.show():
        sys.stdout.write("Failed to send notification")
        sys.exit(5)

listening_port = 65500

sys.stdout.write("== Testing Indication Support in LMIShell ==\n")
sys.stdout.write("This example will start up an indication listener for\n")
sys.stdout.write("the creation of a new user on the system and will print\n")
sys.stdout.write("a message to the console as well as issuing a\n")
sys.stdout.write("notification on the libnotify bus.\n")


# Prompt for the hostname
hostname = raw_input('Hostname: ')
host_uri = "https://%s" % hostname

# Run this script as root and this will use the
# local UNIX socket. Otherwise, modify this line
# to match the system you are connecting to

if os.getuid() == 0 and hostname == 'localhost':
    c = connect(hostname)
else:
    # Prompt for user and password
    user = raw_input('User: ')
    passwd = getpass.getpass("Password: ")
    
    c = connect(host_uri, user, passwd)

if not c:
    sys.stdout.write("Couldn't authenticate\n")
    sys.exit(1)

sys.stdout.write("Starting up indication listener\n")

# First, start up an indication listener
listener = LMIIndicationListener("0.0.0.0", listening_port)
uniquename = listener.add_handler("useradd-XXXXXXXX", useradd_notifier)

sys.stdout.write("useradd handler created, starting listener for %s\n" % uniquename)

res = listener.start()
if not res:
    sys.stdout.write("I'm a poor listener\n")
    sys.exit(2)

sys.stdout.write("listener started, subscribing to indication\n")

# Subscribe to the account creation indication
retval = c.subscribe_indication(
    FilterCreationClassName="CIM_IndicationFilter",
    FilterSystemCreationClassName="CIM_ComputerSystem",
    FilterSourceNamespace="root/cimv2",
    QueryLanguage="DMTF:CQL",
    Query='SELECT * FROM LMI_AccountInstanceCreationIndication WHERE SOURCEINSTANCE ISA LMI_Account',
    Name=uniquename,
    CreationNamespace="root/interop",
    SubscriptionCreationClassName="CIM_IndicationSubscription",
    HandlerCreationClassName="CIM_IndicationHandlerCIMXML",
    HandlerSystemCreationClassName="CIM_ComputerSystem",
    # this is the destination computer, where all the indications will be
    # delivered
    Destination="http://localhost:%d" % (listening_port)
)

if not retval or not retval.rval:
    sys.stdout.write("Failed to register indication: %s\n" % retval.errorstr)
    sys.exit(2)

sys.stdout.write('indication registered\n')

# Loop forever. The listener is running in another thread
while True:
    time.sleep(90)
    pass