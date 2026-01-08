"""
ShadowKey Phase 3 - Login Dialog
Multi-user authentication dialog with registration and login.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Tuple
from data_storage import DataStorage
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(0)
except Exception:
    pass


class LoginDialog:
    """Login and registration dialog for multi-user authentication."""
    
    def __init__(self, parent, db: DataStorage, min_password_length: int = 4):
        """
        Initialize login dialog.
        
        Args:
            parent: Parent Tk window
            db: DataStorage instance
            min_password_length: Minimum password length required
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("ShadowKey - Login")
        self.dialog.geometry("400x350")
        self.dialog.configure(bg='#2c3e50')
        self.dialog.resizable(False, False)
        
        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.db = db
        self.min_password_length = min_password_length
        self.user_id: Optional[int] = None
        self.username: Optional[str] = None
        
        self._create_widgets()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (350 // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create login dialog widgets."""
        # Title
        title = tk.Label(
            self.dialog,
            text="🔐 ShadowKey Phase 3",
            bg='#2c3e50',
            fg='#ecf0f1',
            font=('Arial', 18, 'bold')
        )
        title.pack(pady=20)
        
        subtitle = tk.Label(
            self.dialog,
            text="Behavioral Authentication System",
            bg='#2c3e50',
            fg='#95a5a6',
            font=('Arial', 10)
        )
        subtitle.pack(pady=(0, 30))
        
        # Login frame
        login_frame = tk.Frame(self.dialog, bg='#34495e', padx=30, pady=30)
        login_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Username
        tk.Label(
            login_frame,
            text="Username:",
            bg='#34495e',
            fg='#ecf0f1',
            font=('Arial', 10, 'bold')
        ).pack(anchor='w', pady=(0, 5))
        
        self.username_entry = tk.Entry(
            login_frame,
            font=('Arial', 11),
            bg='#ecf0f1',
            relief=tk.FLAT
        )
        self.username_entry.pack(fill=tk.X, pady=(0, 15))
        self.username_entry.focus()
        
        # Password
        tk.Label(
            login_frame,
            text="Password:",
            bg='#34495e',
            fg='#ecf0f1',
            font=('Arial', 10, 'bold')
        ).pack(anchor='w', pady=(0, 5))
        
        self.password_entry = tk.Entry(
            login_frame,
            font=('Arial', 11),
            bg='#ecf0f1',
            show='●',
            relief=tk.FLAT
        )
        self.password_entry.pack(fill=tk.X, pady=(0, 20))
        
        # Bind Enter key to login
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self._login())
        
        # Buttons
        btn_frame = tk.Frame(login_frame, bg='#34495e')
        btn_frame.pack(fill=tk.X)
        
        self.login_btn = tk.Button(
            btn_frame,
            text="Login",
            command=self._login,
            bg='#27ae60',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        )
        self.login_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        self.register_btn = tk.Button(
            btn_frame,
            text="Register",
            command=self._register,
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        )
        self.register_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
    
    def _login(self):
        """Handle login attempt."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror(
                "Invalid Input",
                "Please enter both username and password.",
                parent=self.dialog
            )
            return
        
        # Authenticate
        user_id = self.db.authenticate_user(username, password)
        
        if user_id:
            self.user_id = user_id
            self.username = username
            self.dialog.destroy()
        else:
            messagebox.showerror(
                "Login Failed",
                "Invalid username or password.",
                parent=self.dialog
            )
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()
    
    def _register(self):
        """Handle registration attempt."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror(
                "Invalid Input",
                "Please enter both username and password.",
                parent=self.dialog
            )
            return
        
        # Validate password length
        if len(password) < self.min_password_length:
            messagebox.showerror(
                "Invalid Password",
                f"Password must be at least {self.min_password_length} characters.",
                parent=self.dialog
            )
            return
        
        # Check if username exists
        existing_user = self.db.get_user_by_username(username)
        if existing_user:
            messagebox.showerror(
                "Username Taken",
                f"Username '{username}' already exists. Please choose another.",
                parent=self.dialog
            )
            return
        
        # Create user
        try:
            user_id = self.db.create_user(username, password)
            self.user_id = user_id
            self.username = username
            
            messagebox.showinfo(
                "Registration Successful",
                f"Welcome, {username}!\nYour account has been created.",
                parent=self.dialog
            )
            
            self.dialog.destroy()
        
        except Exception as e:
            messagebox.showerror(
                "Registration Failed",
                f"Failed to create account:\n{str(e)}",
                parent=self.dialog
            )
    
    def show(self) -> Tuple[Optional[int], Optional[str]]:
        """
        Show dialog and wait for user to login/register.
        
        Returns:
            Tuple of (user_id, username) or (None, None) if canceled
        """
        self.dialog.wait_window()
        return self.user_id, self.username
