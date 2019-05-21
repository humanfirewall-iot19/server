import sqlite3


class FaceIdentifiersDB:
    def __init__(self, dbname="face_feature_db.sqlite", ):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

    def connect(self):
        self._setup_rel()

    def close(self):
        self.conn.commit()
        self.conn.close()

    def _setup_rel(self):
        stmt = "CREATE TABLE IF NOT EXISTS faceRel (original_id text, discriminant_id text)"
        self.conn.execute(stmt)
        self.conn.commit()

    def add_discrimant(self, original_id, discriminant_id):
        self.delete_discrimant(discriminant_id)
        stmt = "INSERT INTO faceRel (original_id,discriminant_id) VALUES (?,?)"
        args = (original_id, discriminant_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_original_by_discriminant(self, discriminant_id):
        stmt = "SELECT DISTINCT original_id FROM faceRel where discriminant_id = (?)"
        args = (discriminant_id)
        cursor = self.conn.execute(stmt, args).fetchone()
        if cursor is None:
            return None
        return cursor[0]

    def delete_discrimant(self, discriminant_id):
        stmt = "DELETE FROM faceRel WHERE discriminant_id = (?) "
        args = (discriminant_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_original_id(self, original_id):
        stmt = "DELETE FROM faceRel WHERE original_id = (?) "
        args = (original_id)
        self.conn.execute(stmt, args)
        self.conn.commit()