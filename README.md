# Urban Occurrences Registration Project

This project is a Spring Boot application designed for the registration and management of urban occurrences. It allows users to report various urban issues such as potholes, broken public lighting, accumulated waste, leaks, damaged signage, infrastructure problems, thefts, vandalism, abandoned animals, dengue hotspots, illegal waste disposal, pollution, public safety risks, environmental issues, and urban risk situations.

## Features

- **User-Friendly Interface**: Built with Thymeleaf, HTMX, and Bootstrap for a responsive and interactive user experience.
- **Data Management**: Utilize PostgreSQL for robust data storage and management of urban occurrences.
- **RESTful API**: Provides endpoints for creating, retrieving, updating, and deleting occurrences.
- **Security**: Configured with Spring Security to ensure secure access to the application.
- **Database Migrations**: Managed with Flyway for seamless database version control.

## Project Structure

- **src/main/java/br/ufpb/dsc/ocorrencias**: Contains the main application code.
  - `OcorrenciasApplication.java`: Entry point of the application.
  - `config/SecurityConfig.java`: Security configuration for authentication and authorization.
  - `controller/OcorrenciaController.java`: Handles HTTP requests related to urban occurrences.
  - `dto/OcorrenciaDTO.java`: Data Transfer Object for urban occurrences.
  - `model/Ocorrencia.java`: Entity representing an urban occurrence.
  - `repository/OcorrenciaRepository.java`: Repository interface for database operations.
  - `service/OcorrenciaService.java`: Business logic for managing urban occurrences.

- **src/main/resources**: Contains application resources.
  - `application.yml`: Main configuration file.
  - `application-dev.yml`: Development-specific configuration.
  - `db/migration/V1__init.sql`: SQL migration scripts for database initialization.
  - `templates`: Thymeleaf templates for UI rendering.
  - `static`: Static resources such as CSS and JavaScript files.

- **src/test/java/br/ufpb/dsc/ocorrencias**: Contains unit tests for the application.

- **docker**: Docker Compose configuration for development environment setup.

- **.github/workflows**: Continuous integration workflows.

## Getting Started

### Prerequisites

- Java 21
- Maven
- PostgreSQL
- Docker (for testing)

### Running the Application

To run the application locally, use the following command:

```
mvn spring-boot:run
```

For testing, ensure Docker is running and execute:

```
mvn test
```

To set up the complete development environment with Docker Compose, run:

```
docker compose -f docker/docker-compose.dev.yml up
```

### Database Migration

Database migrations are managed using Flyway. Ensure the migration scripts are located in `src/main/resources/db/migration/`.

### Security

Ensure to configure the security settings in `src/main/java/br/ufpb/dsc/ocorrencias/config/SecurityConfig.java` according to your requirements.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.