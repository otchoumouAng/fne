import mysql.connector
from mysql.connector import Error
import getpass
import bcrypt

def create_database(cursor, db_name):
    """Crée la base de données si elle n'existe pas."""
    try:
        cursor.execute(f"CREATE DATABASE {db_name} DEFAULT CHARACTER SET 'utf8mb4'")
        print(f"Base de données '{db_name}' créée avec succès.")
    except Error as e:
        if e.errno == 1007: # Can't create database; database exists
            print(f"La base de données '{db_name}' existe déjà.")
        else:
            raise

def create_tables(cursor):
    """Crée les tables du projet."""
    TABLES = {}

    TABLES['roles'] = (
        "CREATE TABLE `roles` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `name` VARCHAR(50) NOT NULL UNIQUE COMMENT 'Ex: Admin, Comptable, Vendeur'"
        ") ENGINE=InnoDB")

    TABLES['users'] = (
        "CREATE TABLE `users` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `username` VARCHAR(100) NOT NULL UNIQUE,"
        "  `password_hash` VARCHAR(255) NOT NULL,"
        "  `full_name` VARCHAR(255),"
        "  `role_id` INT NOT NULL,"
        "  `is_active` BOOLEAN DEFAULT TRUE,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`)"
        ") ENGINE=InnoDB")

    TABLES['company_info'] = (
        "CREATE TABLE `company_info` ("
        "    `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "    `name` VARCHAR(255) NOT NULL,"
        "    `address` TEXT,"
        "    `phone` VARCHAR(50),"
        "    `email` VARCHAR(100),"
        "    `tax_id` VARCHAR(100) COMMENT 'N° de contribuable',"
        "    `fne_api_key` VARCHAR(255) COMMENT 'Clé d''API pour FNE'"
        ") ENGINE=InnoDB")

    TABLES['clients'] = (
        "CREATE TABLE `clients` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `name` VARCHAR(255) NOT NULL,"
        "  `address` TEXT,"
        "  `email` VARCHAR(100),"
        "  `phone` VARCHAR(50),"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ") ENGINE=InnoDB")

    TABLES['products'] = (
        "CREATE TABLE `products` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `name` VARCHAR(255) NOT NULL,"
        "  `description` TEXT,"
        "  `unit_price` DECIMAL(15, 2) NOT NULL,"
        "  `tax_rate` DECIMAL(5, 2) DEFAULT 18.00 COMMENT 'Taux de TVA en pourcentage'"
        ") ENGINE=InnoDB")

    TABLES['invoices'] = (
        "CREATE TABLE `invoices` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `client_id` INT NOT NULL,"
        "  `user_id` INT NOT NULL,"
        "  `document_type` ENUM('sale', 'refund', 'purchase') NOT NULL,"
        "  `issue_date` DATE NOT NULL,"
        "  `due_date` DATE,"
        "  `total_amount` DECIMAL(15, 2) NOT NULL,"
        "  `status` ENUM('draft', 'certified', 'paid', 'partially_paid', 'cancelled') NOT NULL DEFAULT 'draft',"
        "  `fne_status` ENUM('pending', 'success', 'failed') DEFAULT 'pending',"
        "  `fne_nim` VARCHAR(255) NULL,"
        "  `fne_qr_code` TEXT NULL,"
        "  `fne_error_message` TEXT NULL,"
        "  `original_invoice_id` INT NULL,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`client_id`) REFERENCES `clients`(`id`),"
        "  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),"
        "  FOREIGN KEY (`original_invoice_id`) REFERENCES `invoices`(`id`)"
        ") ENGINE=InnoDB")

    TABLES['invoice_items'] = (
        "CREATE TABLE `invoice_items` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `invoice_id` INT NOT NULL,"
        "  `product_id` INT NOT NULL,"
        "  `description` VARCHAR(255) NOT NULL,"
        "  `quantity` DECIMAL(10, 2) NOT NULL,"
        "  `unit_price` DECIMAL(15, 2) NOT NULL,"
        "  `tax_rate` DECIMAL(5, 2) NOT NULL,"
        "  FOREIGN KEY (`invoice_id`) REFERENCES `invoices`(`id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)"
        ") ENGINE=InnoDB")

    TABLES['payments'] = (
        "CREATE TABLE `payments` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `invoice_id` INT NOT NULL,"
        "  `payment_date` DATE NOT NULL,"
        "  `amount` DECIMAL(15, 2) NOT NULL,"
        "  `payment_method` VARCHAR(50),"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`invoice_id`) REFERENCES `invoices`(`id`)"
        ") ENGINE=InnoDB")

    print("Création des tables...")
    for table_name in TABLES:
        table_sql = TABLES[table_name]
        try:
            print(f"  - Création de la table '{table_name}'... ", end='')
            cursor.execute(table_sql)
            print("OK")
        except Error as e:
            if e.errno == 1050: # Table already exists
                print("déjà existante.")
            else:
                print(f"ERREUR: {e}")
                raise

def insert_initial_data(cursor):
    """Insère les données initiales (rôles et admin)."""
    print("\nInsertion des données initiales...")

    # --- Rôles ---
    roles = [('Admin',), ('Comptable',), ('Vendeur',)]
    try:
        cursor.executemany("INSERT INTO roles (name) VALUES (%s)", roles)
        print("  - Rôles insérés.")
    except Error as e:
        if e.errno == 1062: # Duplicate entry
            print("  - Les rôles semblent déjà exister.")
        else:
            print(f"ERREUR lors de l'insertion des rôles: {e}")
            raise

    # --- Utilisateur Admin ---
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if cursor.fetchone():
        print("  - L'utilisateur 'admin' existe déjà.")
        return

    print("\n--- Création de l'utilisateur 'admin' ---")
    admin_password = getpass.getpass("  - Veuillez choisir un mot de passe pour l'utilisateur 'admin': ")
    hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())

    cursor.execute("SELECT id FROM roles WHERE name = 'Admin'")
    admin_role_id = cursor.fetchone()
    if not admin_role_id:
        print("ERREUR: Le rôle 'Admin' n'a pas été trouvé.")
        return

    admin_user = ('admin', hashed_password.decode('utf-8'), 'Administrateur Système', admin_role_id[0])
    cursor.execute(
        "INSERT INTO users (username, password_hash, full_name, role_id) VALUES (%s, %s, %s, %s)",
        admin_user
    )
    print("  - Utilisateur 'admin' créé avec succès.")


def main():
    """Fonction principale pour exécuter le script (modifiée pour non-interactif)."""
    try:
        db_host = "127.0.0.1"
        db_user = "root"
        db_password = "password"
        db_name = "s_facture_plus"

        # Connexion au serveur MySQL
        cnx = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password
        )
        cursor = cnx.cursor()

        # Création de la base de données
        create_database(cursor, db_name)

        # Sélection de la base de données
        cursor.execute(f"USE {db_name}")

        # Création des tables et insertion des données
        create_tables(cursor)
        # Pour l'admin, on ne peut pas utiliser getpass, donc on met un mot de passe par défaut "admin"
        print("\n--- Création de l'utilisateur 'admin' avec mot de passe 'admin' ---")
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            hashed_password = bcrypt.hashpw(b'admin', bcrypt.gensalt())
            cursor.execute("SELECT id FROM roles WHERE name = 'Admin'")
            admin_role_id = cursor.fetchone()
            if admin_role_id:
                admin_user = ('admin', hashed_password.decode('utf-8'), 'Administrateur Système', admin_role_id[0])
                cursor.execute(
                    "INSERT INTO users (username, password_hash, full_name, role_id) VALUES (%s, %s, %s, %s)",
                    admin_user
                )
                print("  - Utilisateur 'admin' créé avec succès.")
        else:
            print("  - L'utilisateur 'admin' existe déjà.")


        cnx.commit()
        print("\nConfiguration de la base de données terminée avec succès !")

    except Error as e:
        print(f"\nUne erreur est survenue: {e}")
    finally:
        if 'cnx' in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()
            print("Connexion MySQL fermée.")

if __name__ == '__main__':
    main()
