class FiccCommon:
    def __init__(self, database, name):
        self.DATABASE = database
        self.NAME = name

    @staticmethod
    def close_connection():
        db = getattr(g, f"_{self.name}_database", None)
        if db is not None:
            db.commit()
            db.close()

    def init_data(cursor):
        pass

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
                app.logger.error("Error initializing database")

    def get_db(self):
        self.init_db()
        db = getattr(g, f"_{self.name}_database", None)
        if db is None:
            db = g._database = sqlite3.connect(self.DATABASE)
        return db
