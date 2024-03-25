const express = require('express');
const mysql = require('mysql2');
process.env.DEBUG = 'express:*';

// Create a MySQL connection
const connection = mysql.createConnection({
  host: 'ENDPOINT',
  user: 'USERNAME',
  password: 'PASS',
  database: 'pad_sys',
  port: 3306
});

// Connect to the MySQL database
connection.connect((err) => {
  if (err) {
    console.error('Error connecting to the database:', err);
    process.exit(1); // Terminate the application
  }
  console.log('Connected to the database');
});

// Create an Express application
const app = express();

// Define a route to retrieve and display the table data
app.get('/tables', (req, res) => {
  // Specify your table name
  const tableName = 'COURSES'; // Replace with the actual table name

  // Define the SQL query
  const query = `SELECT * FROM ${tableName}`;

  // Execute the SQL query
  connection.query(query, (err, results) => {
    if (err) {
      console.error('Error retrieving table data:', err);
      res.status(500).send('Error retrieving table data');
    } else {
      // Display the table data in the response
      res.json(results);
    }
  });
});

// Start the server
app.listen(3000, () => {
  console.log('Server is running on port 3000');
});