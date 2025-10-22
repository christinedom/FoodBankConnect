# Use the official Node.js image
FROM node:20

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json first for caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose React development server port
EXPOSE 3000

# Start React dev server with polling enabled for file changes
CMD ["sh", "-c", "CHOKIDAR_USEPOLLING=true CHOKIDAR_INTERVAL=1000 npm start"]
