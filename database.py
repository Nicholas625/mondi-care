import sqlite3
from datetime import datetime
import threading

class Database:
    def __init__(self):
        self.conn = None
        self.local = threading.local()
        self.connect()
        self.create_tables()
    
    def get_connection(self):
        """Get connection for current thread"""
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.local.conn = sqlite3.connect('mondicare.db')
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn
    
    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect('mondicare.db', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        print("✅ Connected to SQLite database")
    
    def create_tables(self):
        """Create all tables"""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                image_path TEXT,
                disease TEXT,
                confidence REAL,
                chemicals TEXT,
                application TEXT,
                safety TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Officers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS officers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                title TEXT,
                district TEXT,
                region TEXT,
                phone TEXT,
                whatsapp TEXT,
                email TEXT,
                expertise TEXT,
                available TEXT,
                languages TEXT,
                office_location TEXT,
                years_experience INTEGER
            )
        ''')
        
        # Shops table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT CHECK(type IN ('physical', 'online')),
                address TEXT,
                phone TEXT,
                whatsapp TEXT,
                website TEXT,
                products TEXT,
                hours TEXT,
                delivery_info TEXT,
                payment_info TEXT
            )
        ''')
        
        self.conn.commit()
        
        # Insert sample data if empty
        self.insert_sample_data()
    
    def insert_sample_data(self):
        """Insert sample officers and shops"""
        cursor = self.conn.cursor()
        
        # Check if officers exist
        cursor.execute("SELECT COUNT(*) FROM officers")
        if cursor.fetchone()[0] == 0:
            officers = [
                ('Irinatwe Nicholas', 'Senior Agricultural Extension Officer', 
                 'Kanaba Subcounty, Kisoro District', 'South Western Uganda',
                 '+256 761116332', '256761116332', 'irinatwenicholas@gmail.com',
                 'Potato diseases, Early & Late Blight specialist', 'Mon-Fri 8am-5pm', 
                 'English, Rukiga, Swahili', 'Kanaba Subcounty HQ', 8),
                
                ('Sarah Mwiza', 'Crop Protection Specialist', 'Nyakabande sub-county', 
                 'South Western Uganda', '+256 776 789012', '256776789012', 
                 'sarahmwiza@gmail.com', 'Fungal diseases, Organic farming', 
                 'Mon-Sat 9am-6pm', 'English, Rufumbira, Rukiga', 
                 'Nyakabande sub-county HQ', 5),
                
                ('Dr. Robert Kato', 'Senior Plant Pathologist', 'Kabale District', 
                 'South Western Uganda', '+256 703 456789', '256703456789', 
                 'robert.kato@agric.go.ug', 'Late blight research, Disease forecasting', 
                 'Mon-Fri 8am-5pm', 'English, Rufumbira, Runyankole', 
                 'Kabale Zonal Agricultural Office', 15),
                
                ('Muto Grace', 'Agricultural Officer', 'Busanza sub-county', 
                 'South Western Uganda', '+256 789 345678', '256789345678', 
                 'mutograce@gmail.com', 'Integrated pest management, Soil health', 
                 'Mon-Fri 8:30am-5pm', 'English, Rukiga, Rufumbira', 
                 'Busanza sub-county HQ', 6)
            ]
            
            cursor.executemany('''
                INSERT INTO officers 
                (name, title, district, region, phone, whatsapp, email, expertise, 
                 available, languages, office_location, years_experience)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', officers)
            self.conn.commit()
            print("✅ Sample officers inserted")
        
        # Check if shops exist
        cursor.execute("SELECT COUNT(*) FROM shops")
        if cursor.fetchone()[0] == 0:
            shops = [
                ('Green Agro Supplies', 'physical', 'Main street, near Centenary Bank',
                 '+256 700 123456', '256700123456', None, 
                 'Mancozeb, Copper fungicide, Ridomil Gold', 
                 'Mon-Sat: 8am-6pm', None, None),
                
                ('AgroNet Online Shop', 'online', None, None, None, 
                 'https://www.smartfarmingug.com/', 'All pesticides, Organic alternatives',
                 None, 'Next day delivery', 'Mobile Money, Credit Card'),
                
                ('Jumia Agro', 'online', None, None, None, 'https://www.jumia.ug', 
                 'Ridomil Gold, Copper oxychloride, Mancozeb', 
                 None, 'Free delivery over 50,000 UGX', 'Mobile Money, Cash on Delivery'),
                
                ('Farmers Hub Uganda', 'online', None, None, None, 'https://ezyagric.com/', 
                 'All farm inputs, Pesticides, Fungicides', 
                 None, '2-3 business days nationwide', 'Mobile Money, Bank Transfer')
            ]
            
            cursor.executemany('''
                INSERT INTO shops 
                (name, type, address, phone, whatsapp, website, products, hours, delivery_info, payment_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', shops)
            self.conn.commit()
            print("✅ Sample shops inserted")
    
    # ================= USER METHODS =================
    
    def create_user(self, username, email, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def get_user_by_username(self, username):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()
    
    def update_last_login(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now(), user_id)
        )
        conn.commit()
    
    # ================= PREDICTION METHODS =================
    
    def save_prediction(self, user_id, image_path, disease, confidence, chemicals, application, safety):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO predictions 
            (user_id, image_path, disease, confidence, chemicals, application, safety)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, image_path, disease, confidence, str(chemicals), application, safety))
        conn.commit()
        return cursor.lastrowid
    
    def get_user_predictions(self, user_id, limit=20):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM predictions WHERE user_id = ? 
            ORDER BY created_at DESC LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()
    
    # ================= OFFICER METHODS =================
    
    def get_all_officers(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM officers ORDER BY name")
        return cursor.fetchall()
    
    def get_officer_by_id(self, officer_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM officers WHERE id = ?", (officer_id,))
        return cursor.fetchone()
    
    # ================= SHOP METHODS =================
    
    def get_all_shops(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shops ORDER BY name")
        return cursor.fetchall()
    
    def close(self):
        if self.conn:
            self.conn.close()

# Create global instance
db = Database()