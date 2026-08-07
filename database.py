import sqlite3
import random

DB_PATH = 'phone_data.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS def_codes
                 (id INTEGER PRIMARY KEY,
                  country_code TEXT,
                  def_code TEXT,
                  operator TEXT,
                  region TEXT,
                  city TEXT,
                  timezone TEXT,
                  lat REAL,
                  lon REAL)''')
    conn.commit()
    
    c.execute('SELECT COUNT(*) FROM def_codes')
    if c.fetchone()[0] == 0:
        operators = ['МТС', 'Билайн', 'Мегафон', 'Tele2', 'Yota']
        regions = ['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань', 
                   'Нижний Новгород', 'Челябинск', 'Омск', 'Самара', 'Ростов-на-Дону']
        timezones = ['UTC+3', 'UTC+4', 'UTC+5', 'UTC+6', 'UTC+7', 'UTC+8', 'UTC+9', 'UTC+10']
        coords = {
            'Москва': (55.7558, 37.6173),
            'Санкт-Петербург': (59.9343, 30.3351),
            'Новосибирск': (55.0084, 82.9357),
            'Екатеринбург': (56.8389, 60.6057),
            'Казань': (55.7887, 49.1221),
            'Нижний Новгород': (56.2965, 43.9361),
            'Челябинск': (55.1644, 61.4368),
            'Омск': (54.9885, 73.3242),
            'Самара': (53.1959, 50.1002),
            'Ростов-на-Дону': (47.2357, 39.7015)
        }
        
        for i in range(100, 999):
            for cc in ['7', '1', '44', '49', '33', '39']:
                def_code = str(i).zfill(3)
                op = random.choice(operators)
                region = random.choice(regions)
                city = region
                tz = random.choice(timezones)
                lat, lon = coords.get(city, (55.0, 37.0))
                c.execute('''INSERT INTO def_codes 
                             (country_code, def_code, operator, region, city, timezone, lat, lon)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (cc, def_code, op, region, city, tz, lat, lon))
        conn.commit()
    conn.close()

def get_phone_info(country_code, def_code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT operator, region, city, timezone, lat, lon 
                 FROM def_codes 
                 WHERE country_code=? AND def_code=?''', 
              (country_code, def_code))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'operator': row[0],
            'region': row[1],
            'city': row[2],
            'timezone': row[3],
            'lat': row[4],
            'lon': row[5]
        }
    return None