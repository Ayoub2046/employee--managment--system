# login.py
from customtkinter import *
from PIL import Image
from tkinter import messagebox
from tkinter import StringVar
import database # Import your refined database module
import cv2
import numpy as np
import os
import pickle
from datetime import datetime
from tkinter import filedialog # New import for file dialog
from PIL import ImageDraw # New import for drawing circular masks

# No more global username/password

# Create a directory to store face data if it doesn't exist
if not os.path.exists('face_data'):
    os.makedirs('face_data')

# Create a directory to store profile images if it doesn't exist
if not os.path.exists('profile_images'):
    os.makedirs('profile_images')

# Global variables for the login frame and its widgets (initially None)
# They will be instantiated and placed within initiate_password_login_flow()
UsernameEntry_right = None 
passwordEntry_right = None
loginButton_right = None
login_frame = None
profile_icon_label = None # Also need to define this globally for updates
default_circular_icon_tk = None # New global to hold the default circular icon

create_user_frame = None # New global for the create user frame
change_password_frame = None # New global for the change password frame

# Helper function to make an image circular
def make_circular_image(image_path_or_pil_image, size=(80, 80)):
    if isinstance(image_path_or_pil_image, str):
        img = Image.open(image_path_or_pil_image).convert("RGBA")
    else: # Assume it's a PIL Image object
        img = image_path_or_pil_image.convert("RGBA")

    img = img.resize(size, Image.LANCZOS)
    
    # Create a circular mask
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    
    # Apply the mask
    circular_img = Image.new('RGBA', size, (0, 0, 0, 0))
    circular_img.paste(img, (0, 0), mask)
    
    return circular_img

def capture_face(username):
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror('Error', 'Could not access camera. Please check if your camera is connected.', parent=root)
            return False

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                cv2.putText(frame, "No face detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            elif len(faces) > 1:
                cv2.putText(frame, "Multiple faces detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    cv2.putText(frame, "Press SPACE to capture", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('Capture Face - Press SPACE to capture, ESC to cancel', frame)
            
            key = cv2.waitKey(1)
            if key == 27:  # ESC key
                cap.release()
                cv2.destroyAllWindows()
                return False
            elif key == 32 and len(faces) == 1:  # SPACE key and exactly one face detected
                x, y, w, h = faces[0]
                face_img = gray[y:y+h, x:x+w]
                face_img = cv2.resize(face_img, (100, 100))
                face_data = {
                    'username': username,
                    'face_data': face_img,
                    'timestamp': datetime.now()
                }
                
                # Save face data
                with open(f'face_data/{username}_face.pkl', 'wb') as f:
                    pickle.dump(face_data, f)
                
                cap.release()
                cv2.destroyAllWindows()
                return True
        
        cap.release()
        cv2.destroyAllWindows()
        return False
        
    except Exception as e:
        print(f"Error during face capture: {str(e)}")
        if 'cap' in locals():
            cap.release()
        cv2.destroyAllWindows()
        messagebox.showerror('Error', f'Face capture error: {str(e)}', parent=root)
        return False

def upload_profile_image_action(username, status_label):
    if not username:
        messagebox.showerror('Error', 'Please enter a username first.', parent=status_label.master)
        return False
    
    file_path = filedialog.askopenfilename(
        title="Select Profile Image",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
    )
    
    if file_path:
        try:
            # Open the image using PIL (Pillow)
            img = Image.open(file_path)
            # Resize it for consistency, e.g., to a common profile picture size
            img = img.resize((150, 150)) # Example size for a profile image
            
            # Save the image to the profile_images directory
            profile_img_path = os.path.join('profile_images', f'{username}_profile.png')
            img.save(profile_img_path)
            
            status_label.configure(text=f"Profile image uploaded for {username}!", text_color='green')
            messagebox.showinfo('Success', f'Profile image saved for {username}!', parent=status_label.master)
            return True
        except Exception as e:
            status_label.configure(text="Profile image upload failed.", text_color='red')
            messagebox.showerror('Error', f'Error uploading profile image: {str(e)}', parent=status_label.master)
            print(f"Error during profile image upload: {str(e)}")
            return False
    else:
        status_label.configure(text="Profile image upload cancelled.", text_color='red')
        messagebox.showinfo('Info', 'Profile image upload cancelled.', parent=status_label.master)
        return False

def verify_face(username):
    if not os.path.exists(f'face_data/{username}_face.pkl'):
        messagebox.showerror('Error', 'No face data found for this user. Please contact administrator.', parent=root)
        return False
        
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror('Error', 'Could not access camera. Please check if your camera is connected.', parent=root)
            return False

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Load stored face data
        with open(f'face_data/{username}_face.pkl', 'rb') as f:
            stored_face = pickle.load(f)
        
        verification_attempts = 0
        max_attempts = 60  # About 6 seconds at 10 FPS for more robust detection
        
        while verification_attempts < max_attempts:
            ret, frame = cap.read()
            if not ret:
                break
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                cv2.putText(frame, "No face detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            elif len(faces) > 1:
                cv2.putText(frame, "Multiple faces detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    face_img = gray[y:y+h, x:x+w]
                    face_img = cv2.resize(face_img, (100, 100))
                    
                    # Compare with stored face
                    diff = cv2.absdiff(face_img, stored_face['face_data'])
                    similarity = 1 - (np.sum(diff) / (100 * 100 * 255))
                    
                    # Display similarity score
                    cv2.putText(frame, f"Similarity: {similarity:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    if similarity > 0.92:  # Increased threshold for stricter matching
                        cap.release()
                        cv2.destroyAllWindows()
                        return True
            
            cv2.imshow('Face Verification - Press ESC to cancel', frame)
            verification_attempts += 1
            
            if cv2.waitKey(1) == 27:  # ESC key
                break
        
        cap.release()
        cv2.destroyAllWindows()
        messagebox.showerror('Error', 'Face verification failed. Please try again.', parent=root)
        return False
        
    except Exception as e:
        print(f"Error during face verification: {str(e)}")
        if 'cap' in locals():
            cap.release()
        cv2.destroyAllWindows()
        messagebox.showerror('Error', f'Face verification error: {str(e)}', parent=root)
        return False

def verify_admin_face_only():
    face_data_dir = 'face_data'
    if not os.path.exists(face_data_dir) or not os.listdir(face_data_dir):
        messagebox.showerror('Error', 'No admin face data found. Please create an admin user with face data.', parent=root)
        return False

    admin_face_files = [f for f in os.listdir(face_data_dir) if f.endswith('_face.pkl')]

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror('Error', 'Could not access camera. Please check if your camera is connected.', parent=root)
        return False

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    detection_attempts = 0
    max_detection_attempts = 60 # ~6 seconds to detect a face initially

    while detection_attempts < max_detection_attempts:
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        cv2.putText(frame, "Looking for admin face...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        if len(faces) == 1:
            x, y, w, h = faces[0]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (100, 100))

            for filename in admin_face_files:
                try:
                    username = filename.replace('_face.pkl', '')
                    if database.get_user_role(username) != 'admin':
                        continue # Only check admin users

                    with open(os.path.join(face_data_dir, filename), 'rb') as f:
                        stored_face_data = pickle.load(f)
                    stored_face_img = stored_face_data['face_data']

                    diff = cv2.absdiff(face_img, stored_face_img)
                    similarity = 1 - (np.sum(diff) / (100 * 100 * 255))

                    if similarity > 0.92: # Increased threshold for stricter matching
                        cap.release()
                        cv2.destroyAllWindows()
                        return username
                except Exception as ex:
                    print(f"Error processing face file {filename}: {ex}")
            
            cv2.putText(frame, "No matching admin face found.", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        elif len(faces) > 1:
            cv2.putText(frame, "Multiple faces detected", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow('Face Recognition Login', frame)
        
        if cv2.waitKey(1) == 27:  # ESC key
            break
        detection_attempts += 1
    
    cap.release()
    cv2.destroyAllWindows()
    return None # No matching admin face found or cancelled

def login_with_password():
    username = UsernameEntry_right.get()
    password = passwordEntry_right.get()

    if username == '' or password == '':
        messagebox.showerror('Error', 'All fields are required', parent=login_frame)
        return
    elif database.verify_user(username, password):
        user_role = database.get_user_role(username)
        messagebox.showinfo('Success', f'Login is successful! Role: {user_role}', parent=login_frame)
        print(f"Logged in as {username} with role: {user_role}")
        login_frame.destroy()
        root.destroy()
        import ems
    else:
        messagebox.showerror('Error', 'Wrong username or password', parent=login_frame)

def initiate_password_login_flow():
    # Hide initial choice buttons
    hide_all_main_buttons()
    
    # Define and place the new login frame on the right side
    global login_frame
    login_frame = CTkFrame(master=root, width=350, height=350, fg_color="#FFFFFF", corner_radius=15, border_width=2, border_color="#E0E0E0")
    login_frame.place(relx=0.75, rely=0.5, anchor=CENTER)

    # Function to close this login frame and show initial buttons
    def close_password_login_frame():
        login_frame.destroy()
        show_all_main_buttons()
        # Re-bind the root's return key to pass, to prevent unintended calls
        root.bind('<Return>', lambda event: None) # Make sure root's enter key is passive

    # Add a close button to the login frame
    close_button = CTkButton(master=login_frame, text="X", 
                             command=close_password_login_frame,
                             width=30, height=30, 
                             font=('arial', 14, 'bold'),
                             fg_color="transparent", text_color="#666666",
                             hover_color="#F0F0F0")
    close_button.place(relx=0.9, rely=0.05, anchor="ne") # Top-right corner

    # Add profile icon placeholder and dynamic loading
    global profile_icon_label
    profile_icon_label = CTkLabel(master=login_frame, text="") # Text is cleared when image is set
    
    global default_circular_icon_tk # Declare global for the default icon
    default_icon_path = os.path.join('profile_images', 'default_profile_icon.png')
    
    if os.path.exists(default_icon_path):
        pil_image = make_circular_image(default_icon_path, size=(80, 80)) # Create circular PIL image
        default_circular_icon_tk = CTkImage(pil_image, size=(80, 80)) # Convert to CTkImage
        profile_icon_label.configure(image=default_circular_icon_tk, text="") # Set image, clear text
        profile_icon_label.image = default_circular_icon_tk # Keep a reference!
    else:
        print("WARNING: default_profile_icon.png not found in 'profile_images' folder. Please create it or the default icon will be text.")
        profile_icon_label.configure(text="Default Icon", text_color="gray") # Fallback to text if image not found

    profile_icon_label.place(relx=0.5, rely=0.2, anchor=CENTER)

    # Add "Log in" text
    login_text_label = CTkLabel(master=login_frame, text="Log in", font=('arial', 20, 'bold'), text_color='#333333')
    login_text_label.place(relx=0.5, rely=0.4, anchor=CENTER)

    # Define the entry widgets and login button as children of the new login_frame
    global UsernameEntry_right, passwordEntry_right, loginButton_right
    UsernameEntry_right = CTkEntry(master=login_frame, placeholder_text='username or email', width=220, height=35, font=('arial', 12), fg_color='#F0F0F0', text_color='#333333', border_color='#CCCCCC', corner_radius=7)
    UsernameEntry_right.place(relx=0.5, rely=0.55, anchor=CENTER)

    passwordEntry_right = CTkEntry(master=login_frame, placeholder_text='password', width=220, height=35, show='*', font=('arial', 12), fg_color='#F0F0F0', text_color='#333333', border_color='#CCCCCC', corner_radius=7)
    passwordEntry_right.place(relx=0.5, rely=0.68, anchor=CENTER)

    loginButton_right = CTkButton(master=login_frame, text='LOG IN', cursor='hand2', command=login_with_password, width=220, height=40, font=('arial', 14, 'bold'), fg_color='#5CB85C', hover_color='#4CAE4C', corner_radius=7)
    loginButton_right.place(relx=0.5, rely=0.85, anchor=CENTER)

    # Function to update profile icon based on typed username
    def update_profile_icon(event=None):
        username = UsernameEntry_right.get()
        user_profile_path = os.path.join('profile_images', f'{username}_profile.png')
        
        if os.path.exists(user_profile_path):
            try:
                pil_image = make_circular_image(user_profile_path, size=(80, 80)) # Create circular PIL image
                user_image_tk = CTkImage(pil_image, size=(80, 80)) # Convert to CTkImage
                profile_icon_label.configure(image=user_image_tk, text="") # Set image, clear text
                profile_icon_label.image = user_image_tk # Keep a reference!
            except Exception as e:
                print(f"Error loading user profile image {username}: {e}")
                # Fallback to default if user image corrupted
                if 'default_circular_icon_tk' in globals() and default_circular_icon_tk is not None:
                    profile_icon_label.configure(image=default_circular_icon_tk, text="")
                    profile_icon_label.image = default_circular_icon_tk
                else:
                    profile_icon_label.configure(text="Default Icon", image=None)
        else:
            # If no user-specific image, show default
            if 'default_circular_icon_tk' in globals() and default_circular_icon_tk is not None:
                profile_icon_label.configure(image=default_circular_icon_tk, text="")
                profile_icon_label.image = default_circular_icon_tk
            else:
                profile_icon_label.configure(text="Default Icon", image=None)
        
    UsernameEntry_right.bind('<KeyRelease>', update_profile_icon) # Update on each key press
    UsernameEntry_right.focus_set() # Set focus to username entry for convenience
    update_profile_icon() # Call once to set initial icon

    # Bind the Enter key to this specific flow, but target the widgets within the frame
    def handle_enter_key_in_frame(event=None):
        login_with_password()

    login_frame.bind('<Return>', handle_enter_key_in_frame)
    UsernameEntry_right.bind('<Return>', handle_enter_key_in_frame)
    passwordEntry_right.bind('<Return>', handle_enter_key_in_frame)

def initiate_face_login_flow():
    # Hide initial choice buttons
    hide_all_main_buttons()
    # Ensure the password login frame is hidden if it was visible
    if 'login_frame' in globals() and login_frame is not None and login_frame.winfo_exists():
        login_frame.place_forget()

    # Unbind return key from root as it's not applicable here
    root.unbind('<Return>') 

    admin_username = verify_admin_face_only()
    if admin_username:
        messagebox.showinfo('Success', f'Face verification successful! Welcome, {admin_username}', parent=root)
        print(f"Logged in as {admin_username} with role: admin")
        root.destroy()
        import ems
    else:
        # If face verification fails, go back to the initial choice screen
        messagebox.showerror('Error', 'Face recognition failed or cancelled. Please ensure you are an admin and your face data is registered.', parent=root)
        # Re-show initial choice buttons
        show_all_main_buttons()
        # Re-bind the root's return key to pass, to prevent unintended calls
        root.bind('<Return>', lambda event: None) # Make sure root's enter key is passive

def show_create_user_window():
    print("show_create_user_window called.")
    
    global create_user_frame
    if create_user_frame and create_user_frame.winfo_exists():
        create_user_frame.destroy()

    hide_all_main_buttons() # Hide main buttons when this frame is active

    create_user_frame = CTkFrame(master=root, width=350, height=400, fg_color="#FFFFFF", corner_radius=15, border_width=2, border_color="#E0E0E0") # Initial height for user, compact
    create_user_frame.place(relx=0.75, rely=0.5, anchor=CENTER)

    def close_create_user_frame():
        create_user_frame.destroy()
        show_all_main_buttons() # Show main buttons when this frame is closed
        root.bind('<Return>', lambda event: None) # Ensure root's enter key is passive

    close_button = CTkButton(master=create_user_frame, text="X", 
                             command=close_create_user_frame,
                             width=30, height=30, 
                             font=('arial', 14, 'bold'),
                             fg_color="transparent", text_color="#666666",
                             hover_color="#F0F0F0")
    close_button.place(relx=0.9, rely=0.03, anchor="ne") # Top-right corner

    CTkLabel(create_user_frame, text='Create New User', font=('arial', 20, 'bold'), text_color='#333333').place(relx=0.5, rely=0.08, anchor=CENTER)

    label_font = ('arial', 12)
    entry_font = ('arial', 12)

    # DEFINING FUNCTIONS AT THE TOP OF THE SCOPE TO AVOID NameError
    def capture_face_data_action(username, status_label):
        if not username:
            messagebox.showerror('Error', 'Please enter a username first.', parent=create_user_frame)
            return
        status_label.configure(text="Capturing face data...", text_color='yellow')
        create_user_frame.update_idletasks()
        if capture_face(username):
            status_label.configure(text="Face data captured!", text_color='green')
        else:
            status_label.configure(text="Face data capture failed/cancelled.", text_color='red')

    def create_user_action():
        new_username = new_username_entry.get()
        new_password = new_password_entry.get()
        confirm_password = confirm_password_entry.get()
        selected_role = role_var.get()

        if not all([new_username, new_password, confirm_password, selected_role]):
            messagebox.showerror('Error', 'All fields are required', parent=create_user_frame)
            return
        if new_password != confirm_password:
            messagebox.showerror('Error', 'Passwords do not match', parent=create_user_frame)
            return
        if len(new_password) < 6: # Basic password policy
            messagebox.showerror('Error', 'Password must be at least 6 characters', parent=create_user_frame)
            return

        if database.add_user(new_username, new_password, selected_role):
            if selected_role == 'admin':
                if not os.path.exists(f'face_data/{new_username}_face.pkl'):
                    messagebox.showwarning('Warning', 'Admin user created but face data not captured. Face login will not work.', parent=create_user_frame)
                if not os.path.exists(f'profile_images/{new_username}_profile.png'):
                    messagebox.showwarning('Warning', 'Admin user created but profile image not captured.', parent=create_user_frame)

            messagebox.showinfo('Success', 'New user created successfully!', parent=create_user_frame)
            close_create_user_frame() # Close frame on successful creation
        else:
            messagebox.showerror('Error', f"Could not create user '{new_username}'. It might already exist.", parent=create_user_frame)


    # Username
    CTkLabel(create_user_frame, text='Username:', font=label_font, text_color='#000000').place(relx=0.15, rely=0.2, anchor='w')
    new_username_entry = CTkEntry(create_user_frame, placeholder_text='username', width=220, height=35, font=entry_font, fg_color='#F0F0F0', text_color='#333333', border_color='#CCCCCC', corner_radius=7)
    new_username_entry.place(relx=0.6, rely=0.2, anchor=CENTER)

    # Password
    CTkLabel(create_user_frame, text='Password:', font=label_font, text_color='#000000').place(relx=0.15, rely=0.28, anchor='w') # Consistent spacing
    new_password_entry = CTkEntry(create_user_frame, placeholder_text='password', width=220, height=35, font=entry_font, fg_color='#F0F0F0', text_color='#333333', border_color='#CCCCCC', corner_radius=7)
    new_password_entry.place(relx=0.6, rely=0.28, anchor=CENTER) # Consistent spacing

    # Confirm Password
    CTkLabel(create_user_frame, text='Confirm Password:', font=label_font, text_color='#000000').place(relx=0.15, rely=0.36, anchor='w') # Consistent spacing
    confirm_password_entry = CTkEntry(create_user_frame, placeholder_text='confirm password', width=220, height=35, show='*', font=entry_font, fg_color='#F0F0F0', text_color='#333333', border_color='#CCCCCC', corner_radius=7)
    confirm_password_entry.place(relx=0.6, rely=0.36, anchor=CENTER) # Consistent spacing

    # Role selection
    CTkLabel(create_user_frame, text='Role:', font=label_font, text_color='#000000').place(relx=0.15, rely=0.44, anchor='w') # Consistent spacing
    role_var = StringVar(value='user')
    role_combo = CTkComboBox(create_user_frame, variable=role_var, values=['user', 'admin'], state='readonly', width=220, height=35, font=('arial', 12), cursor='hand2', fg_color='#F0F0F0', text_color='#333333', button_color='#5CB85C', button_hover_color='#4CAE4C', border_color='#CCCCCC', corner_radius=7, dropdown_fg_color='#F0F0F0', dropdown_hover_color='#DDDDDD', dropdown_text_color='#333333')
    role_combo.place(relx=0.6, rely=0.44, anchor=CENTER) # Consistent spacing

    profile_image_status_label = CTkLabel(create_user_frame, text="", font=('arial', 12), text_color='#000000') # Changed to black
    face_capture_status_label = CTkLabel(create_user_frame, text="", font=('arial', 12), text_color='#000000') # Changed to black

    upload_profile_button = CTkButton(create_user_frame, text='Upload Profile Image',
                                       command=lambda: (upload_profile_image_action(new_username_entry.get(), profile_image_status_label)),
                                       font=('arial', 12, 'bold'), fg_color='#5CB85C', hover_color='#4CAE4C', height=35, corner_radius=7, width=220)
    
    capture_face_data_button = CTkButton(create_user_frame, text='Capture Face Data',
                                         command=lambda: (capture_face_data_action(new_username_entry.get(), face_capture_status_label)),
                                         font=('arial', 12, 'bold'), fg_color='#5CB85C', hover_color='#4CAE4C', height=35, corner_radius=7, width=220)

    # DEFINING CREATE BUTTON AFTER FUNCTIONS IT CALLS
    create_button = CTkButton(create_user_frame, text='Create User', command=create_user_action,
                              font=('arial', 14, 'bold'), fg_color='#5CB85C', hover_color='#4CAE4C', height=40, corner_radius=7, width=220)

    def update_visibility(*args):
        if role_var.get() == 'admin':
            create_user_frame.configure(height=600) # Adjusted height for admin options, compact
            upload_profile_button.place(relx=0.5, rely=0.56, anchor=CENTER)
            profile_image_status_label.place(relx=0.5, rely=0.62, anchor=CENTER)
            capture_face_data_button.place(relx=0.5, rely=0.68, anchor=CENTER)
            face_capture_status_label.place(relx=0.5, rely=0.74, anchor=CENTER)
            create_button.place(relx=0.5, rely=0.88, anchor=CENTER) # Button placement for admin
        else:
            create_user_frame.configure(height=400) # Shrink frame for user options
            upload_profile_button.place_forget()
            capture_face_data_button.place_forget()
            profile_image_status_label.place_forget()
            face_capture_status_label.place_forget()
            create_button.place(relx=0.5, rely=0.65, anchor=CENTER) # Default placement for user, adjusted for compact

    role_var.trace_add('write', update_visibility)
    update_visibility() # Initial call to set visibility

    # Bind Enter key to create_user_action
    create_user_frame.bind('<Return>', lambda event: create_user_action())
    new_username_entry.bind('<Return>', lambda event: create_user_action())
    new_password_entry.bind('<Return>', lambda event: create_user_action())
    confirm_password_entry.bind('<Return>', lambda event: create_user_action())
    role_combo.bind('<Return>', lambda event: create_user_action())

    new_username_entry.focus_set() # Set focus to username entry

def show_change_password_window():
    print("show_change_password_window called.")
    
    global change_password_frame
    if change_password_frame and change_password_frame.winfo_exists():
        change_password_frame.destroy()

    hide_all_main_buttons() # Hide main buttons when this frame is active

    change_password_frame = CTkFrame(master=root, width=350, height=400, fg_color="#FFFFFF", corner_radius=15, border_width=2, border_color="#E0E0E0") # Compact height
    change_password_frame.place(relx=0.75, rely=0.5, anchor=CENTER)

    def close_change_password_frame():
        change_password_frame.destroy()
        show_all_main_buttons() # Show main buttons when this frame is closed
        root.bind('<Return>', lambda event: None) # Ensure root's enter key is passive

    close_button = CTkButton(master=change_password_frame, text="X", 
                             command=close_change_password_frame,
                             width=30, height=30, 
                             font=('arial', 14, 'bold'),
                             fg_color="transparent", text_color="#666666",
                             hover_color="#F0F0F0")
    close_button.place(relx=0.9, rely=0.03, anchor="ne") # Top-right corner

    CTkLabel(change_password_frame, text='Change Password', font=('arial', 20, 'bold'), text_color='#333333').place(relx=0.5, rely=0.08, anchor=CENTER)

    label_font = ('arial', 12)
    entry_font = ('arial', 12)

    # Username
    CTkLabel(change_password_frame, text='Username:', font=label_font, text_color='#000000').place(relx=0.15, rely=0.2, anchor='w') # Consistent relx
    username_entry_cp = CTkEntry(change_password_frame, placeholder_text='username', width=220, height=35, font=entry_font, fg_color='#F0F0F0', text_color='#333333', border_color='#CCCCCC', corner_radius=7)
    username_entry_cp.place(relx=0.6, rely=0.2, anchor=CENTER)

    # Old Password
    CTkLabel(change_password_frame, text='Old Password:', font=label_font, text_color='#000000').place(relx=0.15, rely=0.3, anchor='w') # Consistent spacing
    old_password_entry_cp = CTkEntry(change_password_frame, placeholder_text='old password', width=220, height=35, show='*', font=entry_font, fg_color='#F0F0F0', text_color='#333333', border_color='#CCCCCC', corner_radius=7)
    old_password_entry_cp.place(relx=0.6, rely=0.3, anchor=CENTER) # Consistent spacing

    # New Password
    CTkLabel(change_password_frame, text='New Password:', font=label_font, text_color='#000000').place(relx=0.15, rely=0.4, anchor='w') # Consistent spacing
    new_password_entry_cp = CTkEntry(change_password_frame, placeholder_text='new password', width=220, height=35, show='*', font=entry_font, fg_color='#F0F0F0', text_color='#333333', border_color='#CCCCCC', corner_radius=7)
    new_password_entry_cp.place(relx=0.6, rely=0.4, anchor=CENTER) # Consistent spacing

    # Confirm New Password
    CTkLabel(change_password_frame, text='Confirm New Password:', font=label_font, text_color='#000000').place(relx=0.15, rely=0.5, anchor='w') # Consistent spacing
    confirm_new_password_entry_cp = CTkEntry(change_password_frame, placeholder_text='confirm new password', width=220, height=35, show='*', font=entry_font, fg_color='#F0F0F0', text_color='#333333', border_color='#CCCCCC', corner_radius=7)
    confirm_new_password_entry_cp.place(relx=0.6, rely=0.5, anchor=CENTER)

    def change_password_action():
        username = username_entry_cp.get()
        old_password = old_password_entry_cp.get()
        new_password = new_password_entry_cp.get()
        confirm_new_password = confirm_new_password_entry_cp.get()

        if not all([username, old_password, new_password, confirm_new_password]):
            messagebox.showerror('Error', 'All fields are required', parent=change_password_frame)
            return
        if new_password != confirm_new_password:
            messagebox.showerror('Error', 'New passwords do not match', parent=change_password_frame)
            return
        if len(new_password) < 6: # Basic password policy
            messagebox.showerror('Error', 'New password must be at least 6 characters', parent=change_password_frame)
            return

        if database.update_user_password(username, old_password, new_password):
            messagebox.showinfo('Success', 'Password changed successfully!', parent=change_password_frame)
            close_change_password_frame() # Close frame on successful change
        else:
            messagebox.showerror('Error', 'Failed to change password. Check old password or username.', parent=change_password_frame)

    change_button = CTkButton(change_password_frame, text='Change Password', command=change_password_action,
                              font=('arial', 14, 'bold'), fg_color='#5CB85C', hover_color='#4CAE4C', height=40, corner_radius=7, width=220)
    change_button.place(relx=0.5, rely=0.75, anchor=CENTER) # Adjusted rely for button

    # Bind Enter key to change_password_action
    change_password_frame.bind('<Return>', lambda event: change_password_action())
    username_entry_cp.bind('<Return>', lambda event: change_password_action())
    old_password_entry_cp.bind('<Return>', lambda event: change_password_action())
    new_password_entry_cp.bind('<Return>', lambda event: change_password_action())
    confirm_new_password_entry_cp.bind('<Return>', lambda event: change_password_action())

    username_entry_cp.focus_set() # Set focus to username entry

def enter_key(event):
    pass # This function is now unused, as the return key binding is handled within the new login frame

# Helper functions to manage button visibility
def hide_all_main_buttons():
    btn_username_password_choice.place_forget()
    btn_face_login_choice.place_forget()
    createUserButton.place_forget()
    changePasswordButton.place_forget()

def show_all_main_buttons():
    btn_username_password_choice.place(x=70, y=150)
    btn_face_login_choice.place(x=70, y=205)
    createUserButton.place(x=70, y=300)
    changePasswordButton.place(x=70, y=350)

root = CTk()
root.geometry('930x478')
root.resizable(0, 0)
root.title('Login Page')

image = CTkImage(Image.open('5561830_21207.jpg'), size=(930, 478))
imagelabel = CTkLabel(root, image=image, text="")
imagelabel.place(x=0, y=0)

headinlabel = CTkLabel(root, text='Employee Management System', bg_color='#FAFAF7', text_color='dark blue',
                       font=('Goudy Old Style', 29, 'bold'))
headinlabel.place(x=20, y=100)

# These buttons remain on the left, at their current (desired) fixed positions
createUserButton = CTkButton(root, text='Create New User', cursor='hand2', command=show_create_user_window, width=250, height=40, font=('arial', 16, 'bold'), fg_color='#1F538D', hover_color='#144870', corner_radius=10)
createUserButton.place(x=70, y=300) 

changePasswordButton = CTkButton(root, text='Change Password', cursor='hand2', command=show_change_password_window, width=250, height=40, font=('arial', 16, 'bold'), fg_color='#1F538D', hover_color='#144870', corner_radius=10)
changePasswordButton.place(x=70, y=350)

# These initial choice buttons remain on the left, at their current (desired) fixed positions
btn_username_password_choice = CTkButton(root, text='Login with Username/Password', cursor='hand2', command=initiate_password_login_flow, width=250, height=45, font=('arial', 16, 'bold'), fg_color='#1F538D', hover_color='#144870', corner_radius=10)
btn_username_password_choice.place(x=70, y=150)

btn_face_login_choice = CTkButton(root, text='Login with Face Recognition', cursor='hand2', command=initiate_face_login_flow, width=250, height=45, font=('arial', 16, 'bold'), fg_color='#1F538D', hover_color='#144870', corner_radius=10)
btn_face_login_choice.place(x=70, y=205)

# Unbind the global return key initially, it will be bound contextually to the login frame
root.bind('<Return>', lambda event: None)

root.mainloop();