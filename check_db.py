import sqlite3
import os

def check_database():
    db_path = 'gestion_empresa.db'
    
    if not os.path.exists(db_path):
        print(f"Error: La base de datos {db_path} no existe")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la tabla familias existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='familias'")
        if cursor.fetchone() is None:
            print("La tabla 'familias' no existe")
            return
        
        # Verificar la estructura de la tabla familias
        cursor.execute("PRAGMA table_info(familias)")
        columns = cursor.fetchall()
        print("\nEstructura de la tabla familias:")
        for col in columns:
            print(f"Columna: {col[1]}, Tipo: {col[2]}")
        
        # Verificar si hay datos en la tabla
        cursor.execute("SELECT * FROM familias")
        rows = cursor.fetchall()
        print(f"\nNúmero de familias en la base de datos: {len(rows)}")
        if rows:
            print("\nPrimeras 5 familias:")
            for row in rows[:5]:
                print(row)
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Error al acceder a la base de datos: {str(e)}")

if __name__ == "__main__":
    check_database() 