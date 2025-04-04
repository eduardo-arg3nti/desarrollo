import os
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime
import sqlite3

# Import database modules
from database.setup_database import setup_database
from database.database_manager import DatabaseManager

# Import UI modules
from ui.categories_tab import create_categories_tab
from ui.families_tab import create_families_tab
from ui.subfamilies_tab import create_subfamilies_tab
from ui.articles_tab import create_articles_tab
from ui.patrimony_tab import create_patrimony_tab
from ui.agents_tab import create_agents_tab
from ui.brands_tab import create_brands_tab
from ui.suppliers_tab import create_suppliers_tab
from ui.stock_tab import create_stock_tab
from ui.serial_numbers_tab import create_serial_numbers_tab

class GestionPatrimonialApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión Patrimonial")
        self.root.geometry("1200x700")
        
        # Set up logging with more detailed configuration
        self.setup_logging()
        
        # Setup database tables if they don't exist
        db_path = 'gestion_patrimonial.db'  # Changed from 'gestion_empresa.db'
        try:
            setup_database(db_path)
            self.logger.info("Database setup completed")
        except Exception as e:
            self.logger.error(f"Error setting up database: {str(e)}")
            messagebox.showerror("Error", f"Error al configurar la base de datos: {str(e)}")
        
        # Initialize database connection
        self.db_manager = DatabaseManager(db_path)
        
        # Share the logger with the database manager
        self.db_manager.logger = self.logger
        
        # Add enhanced debugging to DatabaseManager
        self.enhance_database_manager()
        
        # Log database structure for debugging
        self.log_database_structure(db_path)
        
        # Create main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs with enhanced error handling
        try:
            self.logger.info("Creating categories tab")
            create_categories_tab(self)
            
            self.logger.info("Creating families tab")
            create_families_tab(self)
            
            self.logger.info("Creating subfamilies tab")
            create_subfamilies_tab(self)
            
            self.logger.info("Creating articles tab")
            create_articles_tab(self)
            
            self.logger.info("Creating patrimony tab")
            create_patrimony_tab(self)
            
            self.logger.info("Creating agents tab")
            create_agents_tab(self)
            
            self.logger.info("Creating brands tab")
            create_brands_tab(self)
            
            self.logger.info("Creating suppliers tab")
            create_suppliers_tab(self)
            
            self.logger.info("Creating stock tab")
            create_stock_tab(self)
            
            self.logger.info("Creating serial numbers tab")
            create_serial_numbers_tab(self)
            
        except Exception as e:
            self.logger.error(f"Error creating tabs: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"Error al crear pestañas: {str(e)}")
        
        # In the __init__ method, after creating all tabs:
        
        # Debug treeviews after 1 second
        self.root.after(1000, self.debug_treeviews)
        
        self.logger.info("Application started")
    
    def setup_logging(self):
        """Set up logging configuration with more detailed settings."""
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Set up logger
        self.logger = logging.getLogger('gestion_patrimonial')
        self.logger.setLevel(logging.DEBUG)  # Changed to DEBUG for more detailed logs
        
        # Create file handler
        log_file = f"logs/app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Changed to DEBUG
        
        # Create formatter with more details
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Add console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def enhance_database_manager(self):
        """Add enhanced debugging to DatabaseManager."""
        original_execute_query = self.db_manager.execute_query
        
        def enhanced_execute_query(self, query, params=None, is_select=True):
            """Enhanced execute_query with better error reporting."""
            try:
                self.logger.debug(f"Executing query: {query}")
                if params:
                    self.logger.debug(f"With parameters: {params}")
                result = original_execute_query(query, params, is_select)
                if result is None and is_select:
                    self.logger.warning("Query returned None result")
                return result
            except Exception as e:
                self.logger.error(f"Error in execute_query: {str(e)}", exc_info=True)
                raise
        
        # Replace the method
        import types
        self.db_manager.execute_query = types.MethodType(enhanced_execute_query, self.db_manager)
    
    def add_delete_record_method(self):
        """Add delete_record method to DatabaseManager if it doesn't exist."""
        if not hasattr(self.db_manager, 'delete_record'):
            def delete_record(self, table, condition):
                """Delete records from a table based on a condition."""
                try:
                    query = f"DELETE FROM {table} WHERE {condition}"
                    self.execute_query(query, is_select=False)
                    return True
                except Exception as e:
                    logging.error(f"Error deleting record: {str(e)}")
                    return False
            
            # Add the method to the DatabaseManager instance
            import types
            self.db_manager.delete_record = types.MethodType(delete_record, self.db_manager)
    
    def log_database_structure(self, db_path):
        """Log the structure of all database tables for debugging."""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get list of all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            if not tables:
                self.logger.error("No tables found in the database!")
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                self.logger.info(f"Table: {table_name}, Columns: {column_names}")
                
                # Count records in each table
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                self.logger.info(f"Table {table_name} has {count} records")
            
            conn.close()
        except Exception as e:
            self.logger.error(f"Error logging database structure: {str(e)}")

    def debug_treeviews(self):
        """Debug function to check the content of all treeviews."""
        try:
            self.logger.debug("Checking all treeviews...")
            
            # Check categories treeview
            if hasattr(self, 'categories_tree'):
                items = self.categories_tree.get_children()
                self.logger.debug(f"Categories treeview has {len(items)} items")
                if len(items) == 0:
                    self.logger.warning("Categories treeview is empty - checking database")
                    categories = self.db_manager.execute_query("SELECT COUNT(*) FROM categorias")
                    if categories and categories[0][0] > 0:
                        self.logger.error(f"Database has {categories[0][0]} categories but treeview is empty!")
            else:
                self.logger.warning("Categories treeview not found")
            
            # Check families treeview
            if hasattr(self, 'families_tree'):
                items = self.families_tree.get_children()
                self.logger.debug(f"Families treeview has {len(items)} items")
                if len(items) == 0:
                    self.logger.warning("Families treeview is empty - checking database")
                    families = self.db_manager.execute_query("SELECT COUNT(*) FROM familias")
                    if families and families[0][0] > 0:
                        self.logger.error(f"Database has {families[0][0]} families but treeview is empty!")
            else:
                self.logger.warning("Families treeview not found")
            
            # Check subfamilies treeview
            if hasattr(self, 'subfamilies_tree'):
                items = self.subfamilies_tree.get_children()
                self.logger.debug(f"Subfamilies treeview has {len(items)} items")
                if len(items) == 0:
                    self.logger.warning("Subfamilies treeview is empty - checking database")
                    subfamilies = self.db_manager.execute_query("SELECT COUNT(*) FROM subfamilias")
                    if subfamilies and subfamilies[0][0] > 0:
                        self.logger.error(f"Database has {subfamilies[0][0]} subfamilies but treeview is empty!")
            else:
                self.logger.warning("Subfamilies treeview not found")
            
                # Add more detailed debugging for subfamilies
                if items:
                    self.logger.debug("Subfamilies treeview items:")
                    for item in items:
                        values = self.subfamilies_tree.item(item, 'values')
                        self.logger.debug(f"  Item: {values}")
                else:
                    self.logger.debug("Subfamilies treeview is empty")
            
            # Check articles treeview
            if hasattr(self, 'articles_tree'):
                items = self.articles_tree.get_children()
                self.logger.debug(f"Articles treeview has {len(items)} items")
            
            # Check brands treeview
            if hasattr(self, 'brands_tree'):
                items = self.brands_tree.get_children()
                self.logger.debug(f"Brands treeview has {len(items)} items")
            
            # Check suppliers treeview
            if hasattr(self, 'suppliers_tree'):
                items = self.suppliers_tree.get_children()
                self.logger.debug(f"Suppliers treeview has {len(items)} items")
            
            # Check agents treeview
            if hasattr(self, 'agents_tree'):
                items = self.agents_tree.get_children()
                self.logger.debug(f"Agents treeview has {len(items)} items")
            
        except Exception as e:
            self.logger.error(f"Error in debug_treeviews: {str(e)}", exc_info=True)

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = GestionPatrimonialApp(root)
    root.mainloop()