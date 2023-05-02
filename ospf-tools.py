
import sys, os
from ospf_db_init import ospf_db_init
from ospf_compare import ospf_compare
  

out_dir = "./" # database snapshots will be saved here
route_changes_db = out_dir + "route_changes.db"
color_green = '\033[01;32m'
color_yellow = '\033[01;33m'
color_orange = '\033[33m'
color_red = '\033[01;31m'
color_default = '\x1b[0m'


try:
    arg_1 = str(sys.argv[1])
except:
    arg_1 = None
try:
    arg_2 = str(sys.argv[2])
except:
    arg_2 = None 
try:
    arg_3 = str(sys.argv[3])
except:
    arg_3 = None 


usage_instructions = "\nospf-tools options:\n\n--init: initialize database (pipe serialized JSON into it)\n\"curl http://api.dns.record/api/endpoint | ospf-tools --init\"\n\n--compare: show changes between databases\n\"ospf-tools --compare /path/to/earlier-db /path/to/later-db\"\n\n"


if arg_1 in ["-i", "--init"]:      
    in_string = sys.stdin.read()
    ospf_db_init( in_string, out_dir )

elif arg_1 in ["-c", "--compare"]:
    db1_path = arg_2
    db2_path = arg_3
    ospf_compare( db1_path, db2_path, route_changes_db, color_green, color_yellow, color_orange, color_red, color_default )

else:
    print( usage_instructions )
