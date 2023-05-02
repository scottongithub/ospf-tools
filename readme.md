# Overview
ospf-tools is a command-line tool for comparing OSPF changes over time. It currently works only with a specific data source used by NYC Mesh

There are currently two functions: `--init` and `--compare`

The `init` function takes an OSPF database (as serialized JSON) and outputs a sqlite database (snapshot) to the directory specified at the top of `ospf-tools.py` (default is the current directory). The snapshot file is named after the time it was taken e.g. `2023-05-01_23-42.db`.

The `compare` function compares two separate snapshots of the OSPF database and will list the changes as output to console, as well as add any route changes as rows to the database named `route_changes.db`

Metrics collected and output by the compare function, available for export to other apps, are:

* Current OSPF db timestamp
* Total nodes participating in OSPF
* Total routes 
* Nodes advertising default route
* Changes to the OSPF table
  + Added nodes
  + Removed nodes 
  + Updated nodes
  + Default route changes


# Dependencies
Has been tested on Linux. `std-out` output of the compare function is color-coded for the bash terminal.

# Usage

* pull the repo down: `git clone git@github.com:scottongithub/ospf-tools.git` and `cd` into it
* change `out_dir` at the top of `ospf-tools.py` if you'd like to change the database directory

## Init:

`curl http://api.dns.record/api/endpoint | python3 ospf-tools.py --init`
(URI is in Slack)
you should see an echo for each route processed and then a summary:
```
Initialization complete

Database timestamp: 2023-05-01_23-45 

Total nodes participating in OSPF: xxxx

Total routes in OSPF table: xxxxxx
````

## Compare:
`python3 ospf-tools.py --compare /path/to/earlier-db /path/to/later-db`

you should see output summarizing changes between snapshots:

```
Current OSPF db timestamp:
2023-05-01_23-42
 
Total nodes participating in OSPF: 
xxxx
 
Total routes: 
xxxxx
 
Nodes advertising default route:  
a.b.c.d   metric: 1      metric2: None
a.b.c.e   metric: None   metric2: 10000  via: c.d.e.f
c.d.e.f   metric: 1      metric2: None


Changes to the OSPF table since 2023-05-01_23-41:
 
Added nodes:  
[a.b.c.f, a.b.c.e]
 
Removed nodes:  
[w.x.y.z]
 
Updated nodes:  

a.b.c.d:
+ a.b.b.c metric 100 
+ a.b.b.d metric 100 

a.b.c.h:
- b.c.d.e metric 100 
```

In addition to this output to console, a database `route_changes.db` is created (or appended to if it exists) with all routes that have changed between the snapshots







