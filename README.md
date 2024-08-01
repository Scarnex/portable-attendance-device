# Portable Attendance Device (PAD)

This repository contains Python scripts for a portable attendance system utilizing fingerprint recognition. The system interacts with a fingerprint sensor, a MySQL database for user and attendance management, and provides separate functionalities for administrators and instructors.

## Features

- **Enrollment**: Allows administrators to enroll new users by capturing and storing fingerprint templates along with user details in a MySQL database.
- **User Management**: Provides functionalities to delete users from both the device and the database, and to search for users based on fingerprint templates.
- **Attendance Management**: Instructors can choose classes and record attendance using fingerprint recognition. Attendance records are stored in a database along with timestamps.
- **Image Encryption**: Includes functionality to capture fingerprint images, encrypt them using AES encryption, and store both decrypted and encrypted versions.

## Requirements

- Python 3.x
- Libraries: `adafruit_fingerprint`, `PyMySQL`, `PIL`, `pycryptodome`

## Setup

1. **Hardware Setup**:
   - Connect the fingerprint sensor to the designated UART port (`/dev/ttyS0`).
   - Ensure the Raspberry Pi or similar device is configured correctly for UART communication.

2. **Database Setup**:
   - Set up a MySQL database instance with the following schema:

     ```sql
     CREATE TABLE USERS (
         User_ID INT PRIMARY KEY AUTO_INCREMENT,
         First_Name VARCHAR(50) NOT NULL,
         Last_Name VARCHAR(50) NOT NULL,
         Role ENUM('admin', 'instructor') NOT NULL,
         Fingerprint_Template INT NOT NULL
     );

     CREATE TABLE ATTENDANCE (
         Attendance_ID INT PRIMARY KEY AUTO_INCREMENT,
         Course_ID INT NOT NULL,
         Student_ID INT NOT NULL,
         Date_Time DATETIME DEFAULT CURRENT_TIMESTAMP,
         FOREIGN KEY (Course_ID) REFERENCES COURSES(Course_ID),
         FOREIGN KEY (Student_ID) REFERENCES USERS(User_ID)
     );

     CREATE TABLE COURSES (
         Course_ID INT PRIMARY KEY AUTO_INCREMENT,
         Course_Name VARCHAR(100) NOT NULL,
         Fingerprint_Template INT NOT NULL,
         FOREIGN KEY (Fingerprint_Template) REFERENCES USERS(Fingerprint_Template)
     );
     ```

   - Update the `db_host`, `db_name`, `db_user`, and `db_password` variables in the script with your database credentials.

3. **Software Installation**:
   - Install Python dependencies using `pip install -r requirements.txt`.
   - Modify the UART configuration in the script (`uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)`) as per your setup.

4. **Usage**:
   - Run `python attendance_system.py` to start the portable attendance system.
   - Follow the prompts to log in as an administrator or instructor and utilize the respective functionalities.

## Acknowledgments

- This project utilizes the Adafruit Fingerprint Sensor library and other open-source libraries.
- Thanks to Adafruit Industries for the fingerprint sensor and MIT for the license model.
