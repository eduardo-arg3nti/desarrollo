import sqlite3
import os
import logging
from database.setup_database import setup_database

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_database():
    """Fix the database structure by recreating it with the correct schema."""
    db_path = 'gestion_patrimonial.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    # Create backup
    backup_path = f"{db_path}.backup"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"Created database backup: {backup_path}")
    except Exception as e:
        logger.error(f"Failed to create database backup: {str(e)}")
        return False
    
    # Try to fix the database
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if proveedores table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='proveedores'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Check if it has the correct structure
            cursor.execute("PRAGMA table_info(proveedores)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # If table exists but doesn't have 'nombre' column, recreate it
            if 'nombre' not in column_names:
                logger.info("Fixing proveedores table structure")
                
                # Get existing data if possible
                try:
                    cursor.execute("SELECT * FROM proveedores")
                    existing_data = cursor.fetchall()
                    logger.info(f"Backed up {len(existing_data)} supplier records")
                except:
                    existing_data = []
                    logger.warning("Could not retrieve existing supplier data")
                
                # Drop and recreate the table
                cursor.execute("DROP TABLE proveedores")
                cursor.execute('''
                CREATE TABLE proveedores (
                    id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    direccion TEXT,
                    telefono TEXT,
                    email TEXT,
                    contacto TEXT
                )
                ''')
                
                # Try to restore data if possible
                if existing_data and len(existing_data) > 0:
                    # Map old columns to new columns based on position
                    # This is a best-effort approach
                    for record in existing_data:
                        try:
                            # Assume first field is id, second is name/nombre
                            cursor.execute(
                                "INSERT INTO proveedores (id_proveedor, nombre) VALUES (?, ?)",
                                (record[0], record[1] if len(record) > 1 else "Proveedor sin nombre")
                            )
                        except Exception as e:
                            logger.error(f"Error restoring supplier record: {str(e)}")
                
                logger.info("Proveedores table fixed successfully")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        # Run the full database setup to ensure all tables are correct
        setup_database(db_path)
        
        logger.info("Database structure fixed successfully")
        return True
    except Exception as e:
        logger.error(f"Error fixing database: {str(e)}")
        return False

if __name__ == "__main__":
    # Create database directory if it doesn't exist
    os.makedirs('database', exist_ok=True)
    
    # Make sure the setup_database module is available
    if not os.path.exists('database/setup_database.py'):
        logger.error("setup_database.py not found in the database directory")
        exit(1)
    
    success = fix_database()
    if success:
        print("Database structure fixed successfully!")
        print("You can now run the application again.")
    else:
        print("Error fixing database structure. Check the logs for details.")
        print("A backup of your database was created before attempting fixes.")