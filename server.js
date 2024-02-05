const express = require('express');
const mongoose = require('mongoose');

const app = express();
const PORT = process.env.PORT || 3000;

// Connect to MongoDB Atlas
require("dotenv").config();

const MONGO_URI = process.env.MONGODB_URI;
mongoose.connect(MONGO_URI, { 
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

const db = mongoose.connection;
db.once('open', async () => {
  try {
    // Fetch all collections in the database
    const collections = await mongoose.connection.db.listCollections().toArray();

    if (collections.length === 0) {
      console.error('No collections found in the database.');
      return;
    }

    // Use the first collection name
    const firstCollectionName = collections[0].name;
    console.log(`Using collection: ${firstCollectionName}`);
    // Create a model using the first collection name
    const GenericModel = mongoose.model(firstCollectionName,new mongoose.Schema({},  { collection: firstCollectionName}));


    // Define a route to get all data
    app.get('/api/data', async (req, res) => {
      try {
        // Fetch all data from the first collection
        const allData = await GenericModel.find();
        res.json(allData);
      } catch (error) {
        console.error(error);
        res.status(500).send('Internal Server Error');
      }
    });

    // Start the Express server
    app.listen(PORT, () => {
      console.log(`Server is running on port ${PORT}`);
    });

  } catch (error) {
    console.error('Error fetching collections:', error);
  }
});