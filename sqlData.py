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
    con = connect_db(db_name)
    if con is not None:
        #create video table
        create_videoTable(con, video_Table_Statement)
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()