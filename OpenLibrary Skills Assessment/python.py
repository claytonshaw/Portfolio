import pandas as pd
import psycopg2

# Step 1:
# Read the list of books from the CSV file.
df = pd.read_csv('books.csv')

# Step 2:
# Get the number of pages and the first author's name for each book
# using the OpenLibrary API.

class OpenLibraryAPI:
    """
    A simple way to use the OpenLibrary API.
    """
    BASE_URL = "https://openlibrary.org/api"
    HEADERS = {
        "User-Agent": "MyAppName/1.0 (myemail@example.com)"
    }
    
    @staticmethod
    def get_book_details(isbn: str):
        """
        Get book info using its ISBN.
        
        Args:
            isbn (str): The book's ISBN.
        
        Returns:
            dict: Contains "num_pages" and "author_name".
                  Returns None for both if not found.
        """
        import requests
        endpoint = "/books"
        url = f"{OpenLibraryAPI.BASE_URL}{endpoint}"
        params = {
            "bibkeys": f"ISBN:{isbn}",
            "format": "json",
            "jscmd": "data"
        }
        
        try:
            response = requests.get(url, params=params, headers=OpenLibraryAPI.HEADERS)
            response.raise_for_status()
            data = response.json()
            
            key = f"ISBN:{isbn}"
            if key not in data:
                return {"num_pages": None, "author_name": None}
            
            book_info = data[key]
            num_pages = book_info.get("number_of_pages")
            authors = book_info.get("authors", [])
            author_name = authors[0]["name"] if authors else None
            
            return {"num_pages": num_pages, "author_name": author_name}
        except Exception as e:
            print(f"Error getting data for ISBN {isbn}: {e}")
            return {"num_pages": None, "author_name": None}

def enrich_books_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add author name and page count to the book data.
    
    Args:
        df (pd.DataFrame): The book data with an "ISBN" column.
    
    Returns:
        pd.DataFrame: The book data with new columns "AuthorName" and "NumPages".
    """
    author_names = []
    num_pages_list = []
    
    for index, row in df.iterrows():
        isbn = row.get("ISBN")
        if pd.isna(isbn):
            author_names.append(None)
            num_pages_list.append(None)
            continue

        details = OpenLibraryAPI.get_book_details(isbn)
        author_names.append(details.get("author_name"))
        num_pages_list.append(details.get("num_pages"))
    
    df["AuthorName"] = author_names
    df["NumPages"] = num_pages_list
    
    return df

books_df = enrich_books_data(df)

# Step 3:
# Insert the book data into the BookList table in the database.

class DatabaseInterface:
    """
    A simple class to work with a PostgreSQL database.
    """
    def __init__(self, conn_params: dict):
        """
        Initialize with connection settings.
        
        Args:
            conn_params (dict): Settings for the PostgreSQL connection.
        """
        self.conn_params = conn_params
        self.conn = None

    def connect(self):
        """
        Connect to the PostgreSQL database.
        """
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            print("Connected to PostgreSQL database.")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise

    def close(self):
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    def insert_book(self, title: str, isbn: str, num_pages: int, author_name: str):
        """
        Insert a book into the BookList table.
        Skip the book if the ISBN already exists.
        
        Args:
            title (str): The title of the book.
            isbn (str): The book's ISBN.
            num_pages (int): The page count.
            author_name (str): The author's name.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM BookList WHERE ISBN = %s", (isbn,))
            if cursor.fetchone()[0] > 0:
                print(f"ISBN {isbn} already exists. Skipping insert.")
                self.conn.rollback()
                return
            
            insert_sql = """
                INSERT INTO BookList (Title, ISBN, NumPages, AuthorName)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (title, isbn, num_pages, author_name))
            self.conn.commit()
            print(f"Inserted book: {title}")
        except Exception as e:
            print(f"Error inserting book {isbn}: {e}")
            self.conn.rollback()

def load_books_into_db(books_df: pd.DataFrame, db: DatabaseInterface):
    """
    Insert each book from the data into the database.
    
    Args:
        books_df (pd.DataFrame): The book data.
        db (DatabaseInterface): The database interface to use.
    """
    for _, row in books_df.iterrows():
        title = row.get("Title")
        isbn = str(row.get("ISBN"))
        num_pages = row.get("NumPages")
        author_name = row.get("AuthorName")
        
        db.insert_book(title, isbn, num_pages, author_name)

if __name__ == "__main__":
    # Settings for the PostgreSQL database.
    conn_params = {
        "dbname": "database",
        "user": "user",
        "password": "Password",
        "host": "localhost",
        "port": "5432"
    }
    
    db_interface = DatabaseInterface(conn_params)
    
    try:
        db_interface.connect()
        load_books_into_db(books_df, db_interface)
    finally:
        db_interface.close()
