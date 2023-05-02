import os, sys, sqlite3, json, hashlib, base64
from datetime import datetime


def ospf_db_init( in_string, out_dir ):

    deserialized_json = json.loads( in_string )
    unix_timestamp = int(deserialized_json['updated'])
    db_timestamp = datetime.utcfromtimestamp(unix_timestamp).strftime('%Y-%m-%d_%H-%M')
    db_path = db_timestamp + ".db"

    if os.path.isfile( db_path ):
        print("\ninitialization has already taken place\nremove db to re-initialize\n")
        exit(1)

    conn = sqlite3.connect( db_path )
    c = conn.cursor()
    query = 'CREATE TABLE IF NOT EXISTS misc(field_0 TEXT, field_1 TEXT, field_2 TEXT, field_3 TEXT)'
    c.execute(query)
    query = 'INSERT OR IGNORE INTO misc(field_0, field_1) VALUES(?,?)'
    c.execute(query, ( "db_timestamp", db_timestamp, ))
    # each ospf node gets its table hashed to make comparisons quicker
    query = 'CREATE TABLE IF NOT EXISTS hashes(node TEXT, hash TEXT)'
    c.execute(query)
    # any node advertising default route goes into this table (as well as its own)
    query = 'CREATE TABLE IF NOT EXISTS default_routes(node TEXT, metric INTEGER, metric2 INTEGER, via TEXT)'
    c.execute(query)
    conn.commit()

    total_routes = 0
    routers = deserialized_json['areas']['0.0.0.0']['routers']
    for ospf_node in routers:
        print("Adding OSPF node:", ospf_node)
        # Every node gets its own table
        table_name = str("node_" + ospf_node.replace(".", "_")) # make the name friendly for sqlite tablename
        query = 'CREATE TABLE IF NOT EXISTS {}(IP TEXT, metric INTEGER, metric2 INTEGER, router BOOLEAN DEFAULT 0, network BOOLEAN DEFAULT 0, stubnet BOOLEAN DEFAULT 0, external BOOLEAN DEFAULT 0, via TEXT)'.format(table_name)
        c.execute(query)

        for route_type in ["router", "network", "stubnet"]:
            if route_type in deserialized_json['areas']['0.0.0.0']['routers'][ospf_node]['links']: 
                for route in deserialized_json['areas']['0.0.0.0']['routers'][ospf_node]['links'][route_type]:
                    print("Adding route:", route )
                    router_id = str( route['id'] )
                    route_metric = int( route['metric'] )
                    query = 'INSERT OR IGNORE INTO {0}(IP, metric, {1}) VALUES(?,?,?)'.format( table_name, route_type )
                    c.execute(query, ( router_id, route_metric, True ))
                    total_routes += 1

        # "external" route type gets special treatment
        if "external" in deserialized_json['areas']['0.0.0.0']['routers'][ospf_node]['links']:
            for external in deserialized_json['areas']['0.0.0.0']['routers'][ospf_node]['links']['external']:              
                print("Adding route:", external)
                query = 'INSERT OR IGNORE INTO {}(IP, metric, metric2, external, via) VALUES(?,?,?,?,?);'.format(table_name)               
                external_id = str(external['id'])

                try:
                    external_metric = int(external['metric'])
                except:
                    external_metric = None
                try:
                    external_metric2 = int(external['metric2'])
                except:
                    external_metric2 = None
                try:
                    external_via = str(external['via'])
                except:
                    external_via = None

                c.execute(query, ( external_id, external_metric, external_metric2, True, external_via ))

                total_routes += 1

                if external_id == "0.0.0.0/0":
                    query = 'INSERT OR IGNORE INTO default_routes(node, metric, metric2, via) VALUES(?,?,?,?);'
                    c.execute(query, ( ospf_node, external_metric, external_metric2, external_via, ))
                    print("Adding default route:", external_id)



    query = 'INSERT OR IGNORE INTO misc(field_0, field_1) VALUES(?,?);'
    c.execute(query, ("total_routes", total_routes, ))
    
    conn.commit()


    '''
    Here we make a hash table which stores a unique signature
    for each OSPF node's (sorted) routing table. The idea here
    is to put a bit of computation in up-front (here, at ingest)
    and later compare nodes' routing tables by hashes, to save
    computation cost when queries are run to find differences 
    between routing tables; only tables whose hashes _do not_
    align will need to be enumerated. Overkill? maybe... fun
    to make? you betcha
    '''
    query = 'SELECT name FROM sqlite_schema WHERE type = "table" AND name LIKE "node_%"'
    node_tables = c.execute( query )
    node_tables = node_tables.fetchall()
    total_ospf_node_count = 0 # just a convenient place to grab this metric
    for node_table in node_tables:
        total_ospf_node_count += 1
        query = 'SELECT * FROM {} ORDER BY IP ASC, metric ASC'.format( node_table[0] )
        node = str( node_table[0] )
        node = node.replace("node_", "")
        node = node.replace("_", ".")    
        rows = c.execute(query)
        rows = rows.fetchall()
        node_routes = ""
        for row in rows:
            node_routes += (str(row[0]) + str(row[1]))
        node_hash = hashlib.sha256(node_routes.encode('utf-8')).hexdigest()
        query = 'INSERT OR IGNORE INTO hashes(node, hash) VALUES(?,?)'
        c.execute(query, ( node, node_hash, ))
 
    conn.commit()

    if conn:
        conn.close()

    print("\n\nInitialization complete\n")
    print("Database timestamp:", db_timestamp, "\n")
    print("Total nodes participating in OSPF:", total_ospf_node_count, "\n")
    print("Total routes in OSPF table:", total_routes, "\n\n" )


