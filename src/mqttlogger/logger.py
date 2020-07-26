import paho.mqtt.client as mqtt
import sqlite3, argparse, time, threading, bottle, os.path, bottle.ext.sqlite
from http.server import HTTPServer, BaseHTTPRequestHandler

class Database():
    def __init__(self, args):
        self.conn = sqlite3.connect(args.database)
        if args:
            c = self.conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT UNIQUE, value TEXT)''')
            if args.broker:
                c.execute('''INSERT OR REPLACE INTO config VALUES ('broker', ?)''', (args.broker,))
            c.execute('''CREATE TABLE IF NOT EXISTS topics (id INTEGER PRIMARY KEY, topic TEXT UNIQUE)''')
            c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, timestamp INTEGER, topic_id INTEGER, payload BLOB, qos INTEGER, retain INTEGER, FOREIGN KEY(topic_id) REFERENCES topics(id))''')
            if args.clear:
                c.execute('''DROP TABLE subscriptions''')
            c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (topic TEXT UNIQUE)''')
            for topic in args.topic or []:
                c.execute('''INSERT OR IGNORE INTO subscriptions VALUES (?)''', (topic,))
            self.conn.commit()

    def config(self, key):
        c = self.conn.cursor()
        c.execute('''SELECT value FROM config WHERE key=?''', (key,))
        res = c.fetchone()
        if res:
            return res[0]
        return res

    def store(self, msg):
        try: 
            c = self.conn.cursor()
            c.execute('''INSERT OR IGNORE INTO topics (topic) VALUES(?)''', (msg.topic,))
            c.execute('''SELECT id FROM topics WHERE topic=?''', (msg.topic,))
            topic_id = c.fetchone()[0]
            if msg.retain:
                c.execute('''SELECT payload, qos, retain from MESSAGES WHERE topic_id=? ORDER BY id DESC LIMIT 1''', (topic_id,))
                res = c.fetchone()
                if res and res[0] == msg.payload and res[1] == msg.qos and res[2] == msg.retain:
                    print("Skipping duplicate retained message for topic ", msg.topic)
                    return
            c.execute('''INSERT INTO messages (timestamp, topic_id, payload, qos, retain) VALUES(?,?,?,?,?)''', (int(time.time()), topic_id, msg.payload, msg.qos, msg.retain))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def subscriptions(self):
        c = self.conn.cursor()
        c.execute('''SELECT topic FROM subscriptions''')
        return [topic[0] for topic in c.fetchall()]

class MQTTLogger():

    """Logger for MQTT messages."""

    @staticmethod
    def on_message_cb(client, userdata, msg):
        print(msg.topic+": " + str(msg.payload))
        userdata.db.store(msg)

    def __init__(self, args):

        self.db = Database(args)

        self.client = mqtt.Client(userdata=self)
        self.client.on_message = MQTTLogger.on_message_cb
        broker = self.db.config('broker')
        if not broker:
            raise ValueError('Broker address not in database and not specified on command line')
        self.client.connect(broker)
        for topic in self.db.subscriptions():
            print(topic)
            self.client.subscribe(topic)

    def loop_forever(self):
        self.client.loop_forever()

class WebServer(threading.Thread):
    
    def __init__(self, args, logger):
        super(WebServer,self).__init__()
        self.args = args
        self.logger = logger
        self.app = bottle.Bottle()
        plugin = bottle.ext.sqlite.Plugin(dbfile=args.database)
        self.app.install(plugin)
        bottle.TEMPLATE_PATH = [os.path.join(os.path.dirname(__import__(__name__).__file__),'views')]
        self.app.route('/', callback=self.render_index)

    def run(self):
        self.app.run(host='', port=self.args.port)

    def render_index(self, db):
        c = db.execute('''SELECT timestamp, topic, payload from messages INNER JOIN topics ON messages.topic_id = topics.id ORDER by messages.id DESC LIMIT 100''')
        return bottle.template('messages', messages=c.fetchall())
