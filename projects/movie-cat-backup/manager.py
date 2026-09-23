# -*- coding: utf-8 -*-
from application import app
from www import *
import click


##web server
@app.cli.command("runserver")
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=5000)
def runserver(host, port):
    app.run(host=host, port=port)


@app.cli.command("create_all")
def create_all():
    from application import db
    from common.models.user import User
    db.create_all()


def main():
    app.cli.main()


if __name__ == "__main__":
    try:
        import sys

        sys.exit(main())
    except Exception as e:
        import traceback

        traceback.print_exc()
