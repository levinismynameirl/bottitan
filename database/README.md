# Database Setup

This directory contains the necessary configuration and scripts to set up and run a PostgreSQL database within a Docker container. This setup allows for the database to be deployed and managed separately from the main website application, providing flexibility and scalability.

## Structure

-   **`Dockerfile`**: Defines the Docker image for the PostgreSQL database.
-   **`init.sql`**: Contains the initial SQL commands to create the database schema and populate it with initial data. (Optional)
-   **`.env`**: Stores environment variables such as the database user and password.
-   **`docker-compose.yml`**: Orchestrates the building and running of the database container.

## Usage

### Build and Run

1.  Navigate to the `database` directory.
2.  Create an `.env` file with the following variables:
```
    POSTGRES_USER=your_db_user
    POSTGRES_PASSWORD=your_db_password
    POSTGRES_DB=your_db_name
    
```
3.  Build and start the database container using Docker Compose:
```
bash
    docker-compose up -d
    
```
### Connect to the Database

You can connect to the database using any PostgreSQL client. The connection details are defined in the `.env` file.

-   **Host**: `localhost`
-   **Port**: `5432` (default)
-   **Database**: `your_db_name` (as defined in `.env`)
-   **User**: `your_db_user` (as defined in `.env`)
-   **Password**: `your_db_password` (as defined in `.env`)

### Stop and Remove

To stop and remove the database container:
```
bash
docker-compose down
```
## Deployment

This database setup is designed to be deployed independently from the website application. You can deploy the database container to any Docker-compatible environment, such as a cloud server, a virtual machine, or a dedicated server.

The website application can then connect to this database instance by using the connection details provided above. Ensure that your website application's environment variables or configuration files are updated with the correct database connection parameters.