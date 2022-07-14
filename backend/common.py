import os
import sqlite3


# common class that most other classes derive from
# it contains some specific functions related to holding a sqlite connection
# especially in flask in a thread-safe way using flask.g
# https://flask.palletsprojects.com/en/2.1.x/appcontext/
class Common:
    def __init__(self, database, g):
        self.DATABASE = database
        self.g = g

    def close_connection(self):
        db = getattr(self.g, "_database", None)
        if db is not None:
            self.g._database = None
            db.commit()
            db.close()

    def get_db(self):
        self.init_db()
        db = getattr(self.g, "_database", None)
        if db is None:
            db = self.g._database = sqlite3.connect(self.DATABASE)
        return db

    def init_db(self):
        try:
            os.stat(self.DATABASE)
        except FileNotFoundError:
            try:
                conn = sqlite3.connect(self.DATABASE)
                cursor = conn.cursor()
                self.init_data(cursor)
                conn.commit()
                conn.close()
            except Exception:
                print("Error initializing database")

    def init_data(self, cursor):
        pass

    # this method is here so that bond valuation formula is easily changable
    @staticmethod
    def calculate_net_value(quantity, marketPrice, fxRate):
        return quantity * (marketPrice / fxRate)
