Starting the Docker Containers
To run your React frontend and Flask backend applications using Docker, follow these steps.

Prerequisites
Docker and Docker Compose installed on your machine.
Install Docker
Install Docker Compose
Steps to Start the Containers
1. Navigate to the Project Directory
Open your terminal and navigate to the directory containing your docker-compose.yml file.

bash
Copy code
cd ~/projects
2. Build and Start the Containers
Use Docker Compose to build the images and start the containers.

bash
Copy code
docker-compose up --build
The --build flag tells Docker Compose to build the images before starting the containers.
This command will read your docker-compose.yml file and perform the necessary actions.
3. Access the Applications
React Frontend: Open your web browser and go to http://localhost:3000.
Flask Backend API: You can access the API at http://localhost:5000/api/classes.
4. Stop the Containers
To stop the running containers, press CTRL + C in the terminal where Docker Compose is running. Alternatively, in a new terminal window, navigate to your project directory and run:

bash
Copy code
docker-compose down
Additional Commands and Tips
Run Containers in Detached Mode
If you prefer to run the containers in the background:

bash
Copy code
docker-compose up --build -d
The -d flag runs Docker Compose in detached mode.
View Container Logs
To see the logs from your containers:

bash
Copy code
docker-compose logs
Or for a specific service (e.g., frontend):

bash
Copy code
docker-compose logs frontend
Rebuild Images Without Cache
If you've made changes and need to rebuild the images without using the cache:

bash
Copy code
docker-compose build --no-cache
Verifying the Containers
After running docker-compose up --build, Docker will:

Build the Docker images for both the frontend and backend.
Start the containers.
Link the services via the network specified in docker-compose.yml.
Check Running Containers
You can verify that the containers are running using:

bash
Copy code
docker ps
You should see entries for both the frontend and backend containers.

Troubleshooting
Common Issues
Port Already in Use: If you receive an error that a port is already in use, make sure no other application is using ports 3000 or 5000, or modify the docker-compose.yml file to use different ports.
Environment Variables Not Set: Ensure that the environment variables are correctly set in your .env files and Dockerfiles.
Cleaning Up
If you need to remove all containers and images to start fresh:

bash
Copy code
# Stop all running containers
docker stop $(docker ps -aq)

# Remove all containers
docker rm $(docker ps -aq)

# Remove all images
docker rmi $(docker images -q)
Use caution with these commands as they will remove all Docker containers and images from your system.

Example docker-compose.yml File
Ensure your docker-compose.yml file in the ~/projects directory looks like this:

yaml
Copy code
version: '3'

services:
  backend:
    build: ./adult-education-backend
    ports:
      - "5000:5000"
    volumes:
      - ./adult-education-backend:/app
    networks:
      - app-network

  frontend:
    build: ./adult-education-frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./adult-education-frontend:/app
    networks:
      - app-network

networks:
  app-network: