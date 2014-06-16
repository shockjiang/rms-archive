
#generate the db file:
#sqlite3 rms.db<../schema.sql
#run this file under web directory
import argparse
import os
import sys
PAR_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not PAR_DIR in sys.path:
    sys.path.append(PAR_DIR)
    #print "add PAR_DIR"
else:
    pass
    #print "PAR_DIR is already in path"

import settings
from web import webconfig
#import private
import sqlite3


def connect_db():
    return sqlite3.connect(os.path.join(PAR_DIR, "web", webconfig.DATABASE))


def reset():
    db = connect_db()
    sql = "delete from hosts where id>0"
    try:
        #db.execute(sql)
        pass
    
    except:
        print "FAILED to remove records in hosts table"
        return
    
    for router in settings.ROUTERS.values():
        try:
            print "add router: %s" %(router.name)
            db.execute("insert into hosts (name, ip, port, username, password, workdir) values (?, ?, ?, ?, ?, ?)" , (router.name, router.ip, router.port, router.username, router.password, router.workdir))
            db.commit()
        except:
            print "FAILED add router: %s" %(router.name)

    db.commit()    
    print "The followings are records in table hosts"
    sql = "select * from hosts where id>0 order by id"
    
    try:
        cur = db.execute(sql)
        temp = cur.fetchall()
        print "There are %d records" %(len(temp))
        for row in temp:
            print row
        
    except:
        print "FAILED to get the records from table host"
        
    db.close()
    
    print "end"

if __name__=="__main__":
    reset()
        