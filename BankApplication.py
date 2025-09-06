import mysql.connector
import datetime
import random


class BankApplication:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.current_user = None
        self.setup_database()
    
    def connect_db(self):
        """Establish database connection"""
        '''Connect to the database with your credentials'''
        self.conn = mysql.connector.connect(
            host="",
            user="",
            password="",
            database="")
        self.cursor = self.conn.cursor()
    
    def close_db(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def setup_database(self):
        """Create tables if they don't exist"""
        self.connect_db()
        
        # Create customers table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
            custid INT AUTO_INCREMENT PRIMARY KEY,
            accno VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            password VARCHAR(255) NOT NULL,
            dob DATE NOT NULL,
            amount DECIMAL(10,2) DEFAULT 0.00,
            phno VARCHAR(15) NOT NULL
        );

        ''')
        
        # Create transactions table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                tid INT AUTO_INCREMENT PRIMARY KEY,
                date DATETIME NOT NULL,
                accno VARCHAR(20) NOT NULL,
                type ENUM('DEPOSIT','TRANSFER_OUT','TRANSFER_IN','WITHDRAW') NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (accno) REFERENCES customers(accno)
            );

        ''')
        
        self.conn.commit()
        self.close_db()


    def display_menu(self):
        """Display main menu"""
        print("\n" + "="*50)
        print("           WELCOME TO BANK APPLICATION")
        print("="*50)
        
        if not self.current_user:
            print("1. Create Account")
            print("2. Login")
            print("3. Exit")
        else:
            print(f"Logged in as: {self.current_user['name']}")
            print("1. Deposit Money")
            print("2. Transfer Money") 
            print("3. Balance Enquiry")
            print("4. Withdraw Money")
            print("5. Logout")
            print("6. Exit")


    def generate_account_number(self) -> str:
        """Generate unique 10-digit account number"""
        while True:
            accno = str(random.randint(1000000000, 9999999999))
            self.connect_db()
            self.cursor.execute("SELECT accno FROM customers WHERE accno = %s", (accno,))
            if not self.cursor.fetchone():
                self.close_db()
                return accno
            self.close_db()


    def create_account(self):
        """Create new bank account"""
        print("\n=== CREATE NEW ACCOUNT ===")
        
        try:
            name = input("Enter your full name: ").strip()
            if not name:
                print("Name cannot be empty!")
                return
            
            password = input("Create a password: ").strip()
            if len(password) < 4:
                print("Password must be at least 4 characters!")
                return
            
            dob = input("Enter date of birth (YYYY-MM-DD): ").strip()
            try:
                datetime.datetime.strptime(dob, '%Y-%m-%d')
            except ValueError:
                print("Invalid date format! Please use YYYY-MM-DD")
                return
            
            phno = input("Enter phone number: ").strip()
            if not phno.isdigit() or len(phno) != 10:
                print("Phone number must be 10 digits!")
                return
            
            initial_deposit = float(input("Enter initial deposit amount (minimum 500): "))
            if initial_deposit < 500:
                print("Minimum initial deposit is 500!")
                return
            
            accno = self.generate_account_number()
            
            # Insert into database
            self.connect_db()
            self.cursor.execute('INSERT INTO customers (accno, name, password, dob, amount, phno) VALUES (%s, %s, %s, %s, %s, %s)', (accno, name, password, dob, initial_deposit, phno))

            # Record initial deposit transaction
            self.cursor.execute('''
            INSERT INTO transactions (date, accno, type, amount)
            VALUES (%s, %s, %s, %s)
            ''', (datetime.datetime.now(), accno, 'DEPOSIT', initial_deposit))
            
            self.conn.commit()
            self.close_db()
            
            print(f"\n✅ Account created successfully!")
            print(f"Account Number: {accno}")
            print(f"Initial Balance: ₹{initial_deposit:.2f}")
            
        except ValueError:
            print("Invalid amount entered!")
        except Exception as e:
            print(f"Error creating account: {e}")
        
    def login(self) -> bool:
        """User login"""
        print("\n=== LOGIN ===")
        
        try:
            accno = input("Enter account number: ").strip()
            password = input("Enter password: ").strip()
            
            
            
            self.connect_db()
            self.cursor.execute('''
                SELECT custid, accno, name, amount FROM customers 
                WHERE accno = %s AND password = %s
            ''', (accno, password))
            
            user = self.cursor.fetchone()
            self.close_db()
            
            if user:
                self.current_user = {
                    'custid': user[0],
                    'accno': user[1],
                    'name': user[2],
                    'amount': user[3]
                }
                print(f"\n✅ Welcome, {user[2]}!")
                return True
            else:
                print("❌ Invalid account number or password!")
                return False
                
        except Exception as e:
            print(f"Error during login: {e}")
            return False

    def deposit(self):
        """Deposit money to account"""
        if not self.current_user:
            print("Please login first!")
            return
        
        print("\n=== DEPOSIT MONEY ===")
        
        try:
            amount = float(input("Enter deposit amount: "))
            if amount <= 0:
                print("Amount must be positive!")
                return
            
            self.connect_db()
            
            # Update balance
            self.cursor.execute('''
                UPDATE customers SET amount = amount + %s WHERE accno = %s
            ''', (amount, self.current_user['accno']))
            
            # Record transaction
            self.cursor.execute('''
                INSERT INTO transactions (date, accno, type, amount)
                VALUES (%s, %s, %s, %s)
            ''', (datetime.datetime.now(), self.current_user['accno'], 'DEPOSIT', amount))
            
            # Get updated balance
            self.cursor.execute('SELECT amount FROM customers WHERE accno = %s', 
                              (self.current_user['accno'],))
            new_balance = self.cursor.fetchone()[0]
            
            self.conn.commit()
            self.close_db()
            
            self.current_user['amount'] = new_balance
            
            print(f"✅ ₹{amount:.2f} deposited successfully!")
            print(f"Current Balance: ₹{new_balance:.2f}")
            
        except ValueError:
            print("Invalid amount entered!")
        except Exception as e:
            print(f"Error during deposit: {e}")


    def transfer_money(self):
        """Transfer money to another account"""
        if not self.current_user:
            print("Please login first!")
            return
        
        print("\n=== TRANSFER MONEY ===")
        
        try:
            to_accno = input("Enter recipient's account number: ").strip()
            amount = float(input("Enter transfer amount: "))
            
            if to_accno == self.current_user['accno']:
                print("Cannot transfer to same account!")
                return
                
            if amount <= 0:
                print("Amount must be positive!")
                return
            
            
            
            self.connect_db()
            
            # Check if recipient account exists
            self.cursor.execute('SELECT name, amount FROM customers WHERE accno = %s', (to_accno,))
            recipient = self.cursor.fetchone()
            
            if not recipient:
                print("Recipient account not found!")
                self.close_db()
                return
            
            # Check sender balance
            self.cursor.execute('SELECT amount FROM customers WHERE accno = %s', 
                              (self.current_user['accno'],))
            sender_balance = self.cursor.fetchone()[0]
            
            if sender_balance < amount:
                print(f"Insufficient balance! Available: ₹{sender_balance:.2f}")
                self.close_db()
                return
            
            # Perform transfer
            # Debit from sender
            self.cursor.execute('''
                UPDATE customers SET amount = amount - %s WHERE accno = %s
            ''', (amount, self.current_user['accno']))
            
            # Credit to recipient
            self.cursor.execute('''
                UPDATE customers SET amount = amount + %s WHERE accno = %s
            ''', (amount, to_accno))
            
            # Record transactions
            current_time = datetime.datetime.now()
            
            # Sender transaction (debit)
            self.cursor.execute('''
                INSERT INTO transactions (date, accno, type, amount)
                VALUES (%s, %s, %s, %s)
            ''', (current_time, self.current_user['accno'], 'TRANSFER_OUT', amount))
            
            # Recipient transaction (credit)
            self.cursor.execute('''
                INSERT INTO transactions (date, accno, type, amount)
                VALUES (%s, %s, %s, %s)
            ''', (current_time, to_accno, 'TRANSFER_IN', amount))
            
            # Get updated balance
            self.cursor.execute('SELECT amount FROM customers WHERE accno = %s', 
                              (self.current_user['accno'],))
            new_balance = self.cursor.fetchone()[0]
            
            self.conn.commit()
            self.close_db()
            
            self.current_user['amount'] = new_balance
            
            print('\n'+f"✅ ₹{amount:.2f} transferred successfully to {recipient[0]}!")
            print(f"Your Current Balance: ₹{new_balance:.2f}")
            
        except ValueError:
            print("Invalid amount entered!")
        except Exception as e:
            print(f"Error during transfer: {e}")


    def balance_enquiry(self):
        """Check account balance"""
        if self.current_user==None:
            print("Please login first!")
            return
        
        print("\n=== BALANCE ENQUIRY ===")
        
        try:
            self.connect_db()
            self.cursor.execute('select amount from customers where accno=%s',(self.current_user['accno'],))
            balance=self.cursor.fetchone()[0]
            self.close_db()
            
            self.current_user['amount'] = balance
            print('\n'+f"Name of account holder: {self.current_user['name']}")
            print(f"Account number: {self.current_user['accno']}")
            print(f'Balance: {balance}')

        except Exception as e:
            print(f"Error during balance enquiry: {e}")

    def withdraw(self):
        """Withdraw money from account"""
        if not self.current_user:
            print("Please login first!")
            return
        
        print("\n=== WITHDRAW MONEY ===")
        
        try:
            amount = float(input("Enter withdrawal amount: "))
            if amount <= 0:
                print("Amount must be positive!")
                return
            
            self.connect_db()
            
            # Check balance
            self.cursor.execute('SELECT amount FROM customers WHERE accno = %s', 
                              (self.current_user['accno'],))
            balance = self.cursor.fetchone()[0]
            
            if balance < amount:
                print(f"Insufficient balance! Available: ₹{balance:.2f}")
                self.close_db()
                return
            
            # Perform withdrawal
            self.cursor.execute('''
                UPDATE customers SET amount = amount - %s WHERE accno = %s
            ''', (amount, self.current_user['accno']))
            
            # Record transaction
            self.cursor.execute('''
                INSERT INTO transactions (date, accno, type, amount)
                VALUES (%s, %s, %s, %s)
            ''', (datetime.datetime.now(), self.current_user['accno'], 'WITHDRAW', amount))
            
            # Get updated balance
            self.cursor.execute('SELECT amount FROM customers WHERE accno = %s', 
                              (self.current_user['accno'],))
            new_balance = self.cursor.fetchone()[0]
            
            self.conn.commit()  
            self.close_db()
            
            self.current_user['amount'] = new_balance
            
            print(f"✅ ₹{amount:.2f} withdrawn successfully!")
            print(f"Current Balance: ₹{new_balance:.2f}")
            
        except ValueError:
            print("Invalid amount entered!")
        except Exception as e:
            print(f"Error during withdrawal: {e}")


    def logout(self):
        """Logout current user"""
        if self.current_user:
            print(f"Goodbye, {self.current_user['name']}!")
            self.current_user = None
        else:
            print("No user logged in!")

    def run(self):
        """Main application loop"""
        print("🏦 Bank Management System Started!")
        
        while True:
            try:
                self.display_menu()
                choice = input("\nEnter your choice: ").strip()
                
                if self.current_user is None:
                    if choice == '1':
                        self.create_account()
                    elif choice == '2':
                        self.login()
                    elif choice == '3':
                        print("\nThank you for using Bank Application!\n")
                        break
                    else:
                        print("Invalid choice! Please try again.")
                else:
                    if choice == '1':
                        self.deposit()
                    elif choice == '2':
                        self.transfer_money()
                    elif choice == '3':
                        self.balance_enquiry()
                    elif choice == '4':
                        self.withdraw()
                    elif choice == '5':
                        self.logout()
                    elif choice == '6':
                        print("Thank you for using Bank Application!")
                        break
                    else:
                        print("Invalid choice! Please try again.")
                        
            except KeyboardInterrupt:
                print("\n\nApplication interrupted by user.")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")

if __name__ == "__main__":
    app=BankApplication()
    app.run()
