import re
import falcon
import sqlite3

domainOrIp = str()
rootFolder = str()

# Converts row id from and to base 62
class Base62:
    def encode(self, decimal, symbols = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'):
        # Initiate Variables
        self.decimal = decimal
        self.symbols = symbols

        self.Q = None
        self.base = len(self.symbols)
        self.results = str()
    
        while self.Q != 0:
            self.Q = self.decimal // self.base
            self.R = self.decimal % self.base
            self.decimal = self.Q
            self.results += self.symbols[self.R]

        # Reserve String
        return self.results[::-1] 

    def decode(self, string, symbols = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'):
        # Initiate Variables
        self.string = string
        self.symbols = symbols

        self.n = len(self.string)
        self.s = 0
        self.base = len(self.symbols)
    
        for self.char in self.string:
            self.n = self.n - 1
            self.s = self.s + ((int(self.symbols.index(self.char)) * pow(self.base, self.n)))

        return self.s
    
class Database: 

    def __init__(self):
        self.conn = sqlite3.connect('nano.db')

    # Inserts given URL to database
    def Insert(self, url): 
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO URLs(URL) VALUES (?)', (url,))
        self.conn.commit()
        return cursor.lastrowid
  
    # Search for URL
    def Search(self, id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM URLs WHERE rowid=?', (id,))
        self.conn.commit()
        for row in cursor:
            return ['success', row[0]]

# Create a short URL
class create(object):
    def on_post(self, req, resp): 
        try:
            resp.status = falcon.HTTP_200
            self.longURL = req.get_param("long_URL", required=True)
            if re.match('(?:[a-zA-Z]|[0-9].?:[a-zA-Z]|[0-9])', self.longURL):
                db = Database()
                urlID = db.Insert(self.longURL)
                resp.body = "%s%s/%s" % (domainOrIp, rootFolder, Base62().encode(urlID))
                db.close()
            else:
                resp.body = 'Invalid URL'
        except:
            resp.status = falcon.HTTP_400

# Redirect nano URLs to their intended target
class redirect(object):
    def on_get(self, req, resp, shortlink):
        try:
            resp.status = falcon.HTTP_200
            db = Database()
            status, URL = db.Search(str(Base62().decode(shortlink)))
            if status == 'success':
                resp.set_header('Content-Type', 'text/html;')
                resp.body = '<head> <meta http-equiv="refresh" content="0; URL=%s" /></head>' % (URL)
            else:
                resp.body = 'URL does not exist'
            db.close()
        except:
            resp.status = falcon.HTTP_400

def config(path):
    with open(path) as fin:
        for line in fin:
            variable, value = line.rsplit()
            if variable.lower() == 'domain_or_ip':
                global domainOrIp
                domainOrIp = value
            if variable.lower() == 'root_folder':
                global rootFolder
                rootFolder = value
    
config('config')
app = falcon.API()
app.req_options.auto_parse_form_urlencoded = True
app.add_route('/nano/create', create())
app.add_route('/nano/{shortlink}', redirect()) 

