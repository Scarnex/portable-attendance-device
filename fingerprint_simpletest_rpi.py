# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import serial
import mysql.connector
import adafruit_fingerprint
import os
import getpass
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


# import board
# uart = busio.UART(board.TX, board.RX, baudrate=57600)

# If using with a computer such as Linux/RaspberryPi, Mac, Windows with USB/serial converter:
# uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi and hardware UART:
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi 3 with pi3-disable-bt
# uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)


# Connect to your AWS RDS instance
connection = mysql.connector.connect(
    host=db_host,
    port=3306,  # Specify port 3306 for MySQL
    database=db_name,
    user=db_user,
    password=db_password
)
cursor = connection.cursor()

##################################################

def login():
    print("Welcome to the Portable Attendance Device!")
    while True:
        role = input("Please select your role (admin, instructor): ").lower()
        if role == "admin":
            admin_menu()
            break
        elif role == "instructor":
            instructor_menu()
            break
        else:
            print("Invalid role. Please try again.")


# Define the rest of your functions below


def admin_menu():
    while True:
        print("----------------")
        print("Admin Menu:")
        print("1. Enroll User")
        print("2. Delete User")
        print("3. Find User")
        print("4. Save Fingerprint Image")
        print("5. Exit")
        print("----------------")
        choice = input("Enter your choice: ")
        if choice == "1":
            enroll_finger(get_num(finger.library_size))
        elif choice == "2":
            delete_user()
        elif choice == "3":
            if finger.read_templates() != adafruit_fingerprint.OK:
                raise RuntimeError("Failed to read templates")
            print("Fingerprint templates: ", finger.templates)
            if finger.count_templates() != adafruit_fingerprint.OK:
                raise RuntimeError("Failed to read templates")
            print("Number of templates found: ", finger.template_count)
            if finger.read_sysparam() != adafruit_fingerprint.OK:
                raise RuntimeError("Failed to get system parameters")
            print("Size of template library: ", finger.library_size)
            if get_fingerprint():
                print("Detected #", finger.finger_id, "with confidence", finger.confidence)
            else:
                print("Finger not found")
        elif choice == "4":
            if save_fingerprint_image("fingerprint.png"):
                print("Fingerprint image saved")
            else:
                print("Failed to save fingerprint image")
        elif choice == "5":
            break
        else:
            print("Invalid choice. Please try again.")


def instructor_menu():
    while True:
        print("----------------")
        print("Instructor Menu:")
        print("1. Choose Class for Attendance")
        print("2. Exit")
        print("----------------")
        choice = input("Enter your choice: ")
        if choice == "1":
            choose_class_for_attendance()
        elif choice == "2":
            break
        else:
            print("Invalid choice. Please try again.")


def delete_user():
    # Prompt the user to input the template to delete
    fingerprint_template = input("Enter the template to delete: ")

    # Attempt to delete the user from the device first
    if finger.delete_model(int(fingerprint_template)) == adafruit_fingerprint.OK:
        print("User with template {} has been deleted successfully from the device.".format(fingerprint_template))
    else:
        print("User with template {} was not found in the device.".format(fingerprint_template))

    # Execute the SQL DELETE statement to remove the user from the table
    sql = "DELETE FROM USERS WHERE Fingerprint_Template = %s"
    cursor.execute(sql, (fingerprint_template,))

    # Commit the transaction to apply the changes
    connection.commit()

    # Check if any rows were affected by the DELETE operation
    if cursor.rowcount == 1:
        print("User with template {} has been deleted successfully from the database.".format(fingerprint_template))
        return True  # Return True if deletion is successful from both database and device
    else:
        print("User with template {} was not found in the database.".format(fingerprint_template))
        return False  # Return False if user is not found in the database


def choose_class_for_attendance():
    # Add logic for instructor to choose a class for attendance
    fingerprint_template = scan_fingerprint()
    if fingerprint_template:
        classes = get_classes_for_instructor(fingerprint_template)
        if classes:
            print("Available Classes:")
            for idx, class_name in enumerate(classes, start=1):
                print(f"{idx}. {class_name}")
            selected_class_idx = input("Enter the number of the class you want to take attendance for: ")
            try:
                selected_class_idx = int(selected_class_idx)
                if 1 <= selected_class_idx <= len(classes):
                    selected_class = classes[selected_class_idx - 1]
                    print(f"You have selected class: {selected_class}")
                    # Start attendance for the selected class
                    start_attendance(selected_class)
                else:
                    print("Invalid class number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        else:
            print("No classes available for this instructor.")
    else:
        print("Fingerprint not detected or recognized.")


import datetime

def start_attendance(selected_class):
    # Print message to prompt input of student fingerprints for attendance
    print("Input student fingerprints for attendance in class:", selected_class)
    
    # Add code here to handle attendance process for the selected class
    while True:
        # Scan student fingerprint
        fingerprint_template = scan_fingerprint()
        
        if fingerprint_template:
            # Get student ID associated with the fingerprint
            student_id = get_student_id_by_fingerprint(fingerprint_template)
            
            if student_id:
                # Record attendance in the database
                record_attendance(selected_class, student_id)
                print("Attendance recorded for student with ID:", student_id)
            else:
                print("Student not found.")
        else:
            print("Fingerprint not detected or recognized.")
        
        # Ask if the instructor wants to continue taking attendance
        continue_attendance = input("Do you want to continue taking attendance? (yes/no): ").lower()
        if continue_attendance != "yes":
            break

def record_attendance(selected_class, student_id):
    # Insert a new row into the ATTENDANCE table
    sql = "INSERT INTO ATTENDANCE (Course_ID, Student_ID, Date_Time) VALUES (%s, %s, %s)"
    data = (selected_class, student_id, datetime.datetime.now())
    cursor.execute(sql, data)
    connection.commit()

def get_student_id_by_fingerprint(fingerprint_template):
    # Retrieve the student ID associated with the given fingerprint template
    sql = "SELECT User_ID FROM USERS WHERE Fingerprint_Template = %s"
    cursor.execute(sql, (fingerprint_template,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None


def get_classes_for_instructor(fingerprint_template):
    sql = "SELECT Course_Name FROM COURSES WHERE Fingerprint_Template = %s"
    cursor.execute(sql, (fingerprint_template,))
    classes = cursor.fetchall()
    return [class_info[0] for class_info in classes]


def accept_fingerprints_for_attendance(selected_class):
    while True:
        # Scan fingerprint for attendance
        fingerprint_template = scan_fingerprint()
        if fingerprint_template:
            # Check if the student exists in the database
            student_info = get_student_info_by_template(fingerprint_template)
            if student_info:
                student_id, first_name, last_name = student_info
                # Mark the student as present for the selected class
                mark_attendance(selected_class, student_id)
                print(f"{first_name} {last_name} marked as present for {selected_class}.")
            else:
                print("Student not found in the database.")
        else:
            print("Fingerprint not detected or recognized.")

def get_student_info_by_template(fingerprint_template):
    # Query the database to retrieve student information based on fingerprint template
    sql = "SELECT User_ID, First_Name, Last_Name FROM USERS WHERE Fingerprint_Template = %s"
    cursor.execute(sql, (fingerprint_template,))
    result = cursor.fetchone()
    return result if result else None


def scan_fingerprint():
    """Scan fingerprint and return the fingerprint template if recognized."""
    if get_fingerprint():
        print("Detected fingerprint!")
        return finger.finger_id
    else:
        print("Fingerprint not detected or recognized.")
        return None


def scan_fingerprint_for_attendance():
    # Add logic for student to scan fingerprint for attendance
    if get_fingerprint():
        print("Detected fingerprint!")

        # Get the fingerprint template ID
        fingerprint_template = finger.finger_id

        # Execute SQL SELECT statement to fetch student information based on fingerprint template
        sql = "SELECT First_Name, Last_Name FROM USERS WHERE Fingerprint_Template = %s"
        cursor.execute(sql, (fingerprint_template,))
        result = cursor.fetchone()

        if result:
            first_name, last_name = result

            # Increment the absence count for the student
            sql = "UPDATE SOFTWARE_MAINTENANCE_AND_EVOLUTION_1_02 SET Absence = Absence + 1 WHERE First_Name = %s AND Last_Name = %s"
            cursor.execute(sql, (first_name, last_name))
            connection.commit()

            print(f"Attendance recorded for {first_name} {last_name}. Absence count updated.")
        else:
            print("Student information not found for the provided fingerprint.")
    else:
        print("Fingerprint not detected.")


def get_fingerprint():
    """Get a finger print image, template it, and see if it matches!"""
    print("Waiting for image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True


# pylint: disable=too-many-branches
def get_fingerprint_detail():
    """Get a finger print image, template it, and see if it matches!
    This time, print out each error instead of just returning on failure"""
    print("Getting image...", end="")
    i = finger.get_image()
    if i == adafruit_fingerprint.OK:
        print("Image taken")
    else:
        if i == adafruit_fingerprint.NOFINGER:
            print("No finger detected")
        elif i == adafruit_fingerprint.IMAGEFAIL:
            print("Imaging error")
        else:
            print("Other error")
        return False

    print("Templating...", end="")
    i = finger.image_2_tz(1)
    if i == adafruit_fingerprint.OK:
        print("Templated")
    else:
        if i == adafruit_fingerprint.IMAGEMESS:
            print("Image too messy")
        elif i == adafruit_fingerprint.FEATUREFAIL:
            print("Could not identify features")
        elif i == adafruit_fingerprint.INVALIDIMAGE:
            print("Image invalid")
        else:
            print("Other error")
        return False

    print("Searching...", end="")
    i = finger.finger_fast_search()
    # pylint: disable=no-else-return
    # This block needs to be refactored when it can be tested.
    if i == adafruit_fingerprint.OK:
        print("Found fingerprint!")
        return True
    else:
        if i == adafruit_fingerprint.NOTFOUND:
            print("No match found")
        else:
            print("Other error")
        return False


# pylint: disable=too-many-statements
def enroll_finger(location):
    """Take a 2 finger images and template it, then store in 'location'"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="")
        else:
            print("Place same finger again...", end="")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
                return False
            else:
                print("Other error")
                return False

        print("Templating...", end="")
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Templated")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Image invalid")
            else:
                print("Other error")
            return False

        if fingerimg == 1:
            print("Remove finger")
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
        else:
            print("Other error")
        return False

    print("Storing model #%d..." % location, end="")
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        print("Stored")
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            print("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            print("Flash storage error")
        else:
            print("Other error")
        return False

    # Add code to insert data into the database
    fingerprint_template = location
    first_name = input("Enter first name: ")
    last_name = input("Enter last name: ")
    role = input("Enter role: ")
    user_id = input("Enter ID: ")

    sql = "INSERT INTO USERS (user_id, first_name, last_name, role, Fingerprint_Template) VALUES (%s, %s, %s, %s, %s)"
    data = (user_id, first_name, last_name, role, fingerprint_template)
    cursor.execute(sql, data)
    connection.commit()
    print("User enrolled successfully!")

    return True


def pad(data):
    block_size = AES.block_size
    return data + (block_size - len(data) % block_size) * bytes([block_size - len(data) % block_size])

def save_fingerprint_image(filename):
    """Scan fingerprint then save both encrypted and decrypted images to filename."""
    while finger.get_image():
        pass

    # Create a new PIL image for the original (decrypted) image
    img = Image.new("L", (256, 288), "white")
    pixeldata = img.load()
    mask = 0b00001111
    result = finger.get_fpdata(sensorbuffer="image")

    # Unpack the data received from the fingerprint module and copy the image data to the image placeholder "img"
    x = 0
    y = 0
    for i in range(len(result)):
        pixeldata[x, y] = (int(result[i]) >> 4) * 17
        x += 1
        pixeldata[x, y] = (int(result[i]) & mask) * 17
        if x == 255:
            x = 0
            y += 1
        else:
            x += 1

    # Save the original (decrypted) image
    img.save("decrypted_" + filename)

    # Encrypt the image data
    key = get_random_bytes(16)  # Generate a random 128-bit key
    cipher = AES.new(key, AES.MODE_ECB)  # Create an AES cipher object
    plaintext = bytes(result)  # Convert the image data to bytes
    padded_plaintext = pad(plaintext)  # Pad the plaintext to the block boundary
    ciphertext = cipher.encrypt(padded_plaintext)

    # Create a new image for the encrypted version
    encrypted_img = Image.new("L", (256, 288), "white")
    encrypted_pixeldata = encrypted_img.load()
    idx = 0
    for y in range(288):
        for x in range(256):
            if idx < len(ciphertext):
                encrypted_pixeldata[x, y] = ciphertext[idx]
                idx += 1

    # Save the encrypted image
    encrypted_img.save("encrypted_" + filename)

    # Combine the images horizontally into a single image
    combined_img = Image.new("L", (512, 288), "white")
    combined_img.paste(img, (0, 0))
    combined_img.paste(encrypted_img, (256, 0))

    # Save the combined image
    combined_img.save("combined_" + filename)

    return True


##################################################


def get_num(max_number):
    """Use input() to get a valid number from 0 to the maximum size
    of the library. Retry till success!"""
    i = -1
    while (i > max_number - 1) or (i < 0):
        try:
            i = int(input("Enter ID # from 0-{}: ".format(max_number - 1)))
        except ValueError:
            pass
    return i


if __name__ == "__main__":
    login()