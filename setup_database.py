import sqlite3
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_database(db_path):
    """Create all necessary tables in the database if they don't exist."""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Create categorias table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT
        )
        ''')
        
        # Create familias table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS familias (
            id_familia INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_familia TEXT NOT NULL
        )
        ''')
        
        # Create subfamilias table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subfamilias (
            id_subfamilia INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            id_familia INTEGER,
            FOREIGN KEY (id_familia) REFERENCES familias (id_familia)
        )
        ''')
        
        # Create marcas table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS marcas (
            id_marca INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_marca TEXT NOT NULL
        )
        ''')
        
        # Create proveedores table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            direccion TEXT,
            telefono TEXT,
            email TEXT,
            contacto TEXT
        )
        ''')
        
        # Create agentes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS agentes (
            id_agente INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            legajo TEXT,
            departamento TEXT
        )
        ''')
        
        # Create articulos table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS articulos (
            id_articulo INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            id_categoria INTEGER,
            id_marca INTEGER,
            id_proveedor INTEGER,
            precio REAL,
            FOREIGN KEY (id_categoria) REFERENCES categorias (id_categoria),
            FOREIGN KEY (id_marca) REFERENCES marcas (id_marca),
            FOREIGN KEY (id_proveedor) REFERENCES proveedores (id_proveedor)
        )
        ''')
        
        # Create numeros_patrimonio table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS numeros_patrimonio (
            id_patrimonio INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_patrimonio TEXT NOT NULL,
            id_articulo INTEGER,
            id_agente INTEGER,
            fecha_asignacion TEXT,
            estado TEXT,
            FOREIGN KEY (id_articulo) REFERENCES articulos (id_articulo),
            FOREIGN KEY (id_agente) REFERENCES agentes (id_agente)
        )
        ''')
        
        # Create stock table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock (
            id_stock INTEGER PRIMARY KEY AUTOINCREMENT,
            id_articulo INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            ubicacion TEXT,
            fecha_ingreso TEXT,
            notas TEXT,
            FOREIGN KEY (id_articulo) REFERENCES articulos (id_articulo)
        )
        ''')
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info(f"Database setup completed successfully: {db_path}")
        return True
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        return False

if __name__ == "__main__":
    db_path = 'gestion_patrimonial.db'
    if os.path.exists(db_path):
        logger.warning(f"Database already exists: {db_path}")
        choice = input("Do you want to continue and update the database structure? (y/n): ")
        if choice.lower() != 'y':
            logger.info("Database setup cancelled.")
            exit()
    
    success = setup_database(db_path)
    if success:
        print("Database setup completed successfully!")
    else:
        print("Error setting up database. Check the logs for details.")