import sqlite3
from sqlite3 import Error

def connect_db(db_name):
    con = None
    try:
        con = sqlite3.connect(db_name)
    except Error as e:
        print(e)
    return con

def create_videoTable(con, create_sql_statement):
    try:
        c = con.cursor()
        c.execute(create_sql_statement)
    except Error as e:
        print(e)

def get_all_videos(con):
    try:
        cur = con.cursor()
        cur.execute("SELECT * from videos")
        rows = cur.fetchall()
        return rows
    except Error as e:
        print(e)
        return []

#Be sure to sanitize all SQL requests
def insert_video(con, video_id, url, comments, transcript, upload_date, channel):
    sql = ''' INSERT INTO videos(video_id,url,comments,transcript,upload_date,channel)
                 VALUES(?,?,?,?,?,?) '''
    cur = con.cursor()
    cur.execute(sql, (video_id, url, comments, transcript, upload_date, channel))
    return cur.lastrowid

def main():
    db_name = 'videoInfo.db'
    video_Table_Statement = """ CREATE TABLE IF NOT EXISTS videos (
                                            video_id text PRIMARY KEY,
                                            url text NOT NULL,
                                            comments text NOT NULL,
                                            transcript text NOT NULL,
                                            upload_date text NOT NULL,
                                            channel text NOT NULL
                                        ); """



