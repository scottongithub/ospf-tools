import os, sqlite3, shutil, hashlib, base64


def ospf_compare( db1_path, db2_path, route_changes_db, color_green, color_yellow, color_orange, color_red, color_default ):

    added_nodes = []
    removed_nodes = []
    updated_nodes = []

    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    # db_1 is the earlier snapshot, db_2 is later
    query = 'ATTACH DATABASE ? AS db_1;'
    c.execute(query, ( db1_path, ))
    query = 'ATTACH DATABASE ? AS db_2;'
    c.execute(query, ( db2_path, ))

    ''' 
    Ospf node exists in db_1 but not in db_2? add to 'removed_nodes'  
    Also a convenient place to check hashes and mark nodes 
    if they don't align. Marked nodes will have tables checked
    against each other later on. The idea with this is to save a 
    bit of compute by only comparing tables that have changed
    '''
    rows_db_1 = c.execute('SELECT * FROM db_1.hashes')
    rows_db_1 = rows_db_1.fetchall()
    for row_db_1 in rows_db_1:
        IP = row_db_1[0]
        db_1_node_hash = row_db_1[1]
        query = 'SELECT hash FROM db_2.hashes WHERE node = ?;'
        db_2_node_hash = c.execute(query, ( IP, ))
        db_2_node_hash = db_2_node_hash.fetchall() 
        if len( db_2_node_hash ) == 0:
            removed_nodes.append( IP )

        elif db_1_node_hash != db_2_node_hash[0][0]:
            updated_nodes.append( IP )

    ''' 
    Ospf node exists in db_2 but not in db_1? add to 'added_nodes'  
    '''
    rows_db_2 = c.execute('SELECT * FROM db_2.hashes')
    rows_db_2 = rows_db_2.fetchall()
    for row_db_2 in rows_db_2:
        IP = row_db_2[0]
        db_2_node_hash = row_db_2[1]
        query = 'SELECT hash FROM db_1.hashes WHERE node = ?;'
        db_1_node_hash = c.execute(query, (IP,))
        db_1_node_hash = db_1_node_hash.fetchall() 
        if len(db_1_node_hash) == 0:
            added_nodes.append(IP)


    db_2_timestamp = c.execute('SELECT field_1 FROM db_2.misc WHERE field_0 = "db_timestamp"')
    db_2_timestamp = db_2_timestamp.fetchall()
    total_ospf_nodes = c.execute('SELECT COUNT(*) FROM db_2.hashes')
    total_ospf_nodes = total_ospf_nodes.fetchall()
    total_routes = c.execute('SELECT field_1 FROM db_2.misc WHERE field_0 = "total_routes"')
    total_routes = total_routes.fetchall()
    query = 'SELECT node, metric, metric2, via FROM db_2.default_routes;'
    default_routes = c.execute(query)
    default_routes = default_routes.fetchall()
    db_1_timestamp = c.execute('SELECT field_1 FROM db_1.misc WHERE field_0 = "db_timestamp"')
    db_1_timestamp = db_1_timestamp.fetchall()


    print(color_orange + "\n\nCurrent OSPF db timestamp:\n" + color_default + db_2_timestamp[0][0])
    print(color_orange, "\nTotal nodes participating in OSPF:", color_default)
    print(total_ospf_nodes[0][0])
    print(color_orange, "\nTotal routes:", color_default)
    print(total_routes[0][0])
    print(color_orange, "\nNodes advertising default route: ", color_default)
    for row in default_routes:
        if row[3] == None:
            print(row[0], "  metric:", row[1], "  metric2:", row[2])
        else:
            print(row[0], "  metric:", row[1], "  metric2:", row[2], " via:", row[3])
    print(color_orange + "\n\nChanges to the OSPF table since " + db_1_timestamp[0][0] + ":" + color_default)
    print(color_green, "\nAdded nodes: ", color_default)
    print(added_nodes)
    print(color_red, "\nRemoved nodes: ", color_default)
    print(removed_nodes)
    print(color_yellow, "\nUpdated nodes: ", color_default)

    rc_conn = sqlite3.connect( route_changes_db )
    rc = rc_conn.cursor()

    query = 'CREATE TABLE IF NOT EXISTS ospf_nodes(node_ip TEXT, route TEXT, status TEXT, time_stamp TEXT)'
    rc.execute(query)

    for updated_node in updated_nodes:
        node_route_table = "node_" + updated_node.replace(".", "_")
        query = 'SELECT * FROM db_2.{0} EXCEPT SELECT * FROM db_1.{1} ORDER BY IP ASC'.format(node_route_table, node_route_table)
        added_routes = c.execute(query)
        added_routes = added_routes.fetchall()
        query = 'SELECT * FROM db_1.{0} EXCEPT SELECT * FROM db_2.{1} ORDER BY IP ASC'.format(node_route_table, node_route_table)
        removed_routes = c.execute(query)
        removed_routes = removed_routes.fetchall()
        
        print("\n" + updated_node + ":")
        for added_route in added_routes:
            print(color_green + "+", added_route[0], "metric", added_route[1], color_default ) 
            query = 'INSERT OR IGNORE INTO ospf_nodes(node_ip, route, status, time_stamp) VALUES(?,?,?,?)'
            rc.execute(query, ( updated_node, added_route[0], "UP", db_2_timestamp[0][0], ))
        for removed_route in removed_routes:
            print(color_red + "-", removed_route[0], "metric", removed_route[1], color_default )  
            query = 'INSERT OR IGNORE INTO ospf_nodes(node_ip, route, status, time_stamp) VALUES(?,?,?,?)'
            rc.execute(query, ( updated_node, removed_route[0], "DOWN", db_2_timestamp[0][0], ))
    rc_conn.commit()


    if conn:
        conn.close()

    if rc_conn:
        rc_conn.close()
