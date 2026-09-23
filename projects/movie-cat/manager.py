# -*- coding: utf-8 -*-
from application import app, db
from www import *
import click
from jobs.launcher import runJob

##web server
@app.cli.command( "runserver" )
@click.option( '--host',default='0.0.0.0' )
@click.option( '--port',default=5000 )
def runserver( host,port ):
    app.run( host = host,port = port,debug = True )


##create_table
@app.cli.command( "create_all" )
def create_all():
    db.create_all()


##runjob
@app.cli.command( "runjob",context_settings = dict( ignore_unknown_options=True ) )
@click.argument( 'args',nargs = -1,type = click.UNPROCESSED )
def runjob( args ):
    '''
    调度Job，如 python manager.py runjob -m movie -a list
    '''
    runJob( list( args ) )


def main():
    app.cli.main()

if __name__ == "__main__":
    try:
        import sys
        sys.exit( main() )
    except Exception as e:
        import traceback
        traceback.print_exc()
