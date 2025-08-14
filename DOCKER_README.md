# Docker Setup for Django UWH Attendance Project

This Django project tracks attendance and payments for the Denver Area Underwater Hockey Club and has been fully dockerized for easy deployment and development.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

### 1. Environment Setup

Copy the environment example file:
```bash
cp .env.example .env
```

Edit `.env` with your preferred configuration:
```bash
# Django Configuration
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database Configuration
DB_NAME=uwh_attendance
DB_USER=uwh_user
DB_PASSWORD=your-secure-db-password
DB_HOST=db
DB_PORT=3306

# MySQL Root Password
MYSQL_ROOT_PASSWORD=your-secure-root-password
```

### 2. Development Mode

For development with live code reloading:

```bash
# Start the services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Access the application at http://localhost:8000
```

### 3. Production Mode

For production deployment with Nginx:

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Access the application at http://localhost (port 80)
```

## Management Commands

### Database Operations

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic

# Access Django shell
docker-compose exec web python manage.py shell
```

### Container Management

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: This will delete your data!)
docker-compose down -v

# Rebuild containers
docker-compose build --no-cache

# View container status
docker-compose ps
```

## Architecture

The Docker setup includes:

### Services

1. **web** - Django application server (Gunicorn)
2. **db** - MySQL 8.0 database
3. **nginx** - Reverse proxy and static file server (production only)

### Volumes

- `mysql_data` - Persistent database storage
- `static_volume` - Collected static files
- `media_volume` - User uploaded media files

### Network

- `uwh_network` - Internal network for service communication

## Database Access

To connect to the MySQL database directly:

```bash
# Access MySQL shell
docker-compose exec db mysql -u uwh_user -p uwh_attendance

# Or using root
docker-compose exec db mysql -u root -p
```

## Backup and Restore

### Backup Database

```bash
docker-compose exec db mysqldump -u root -p uwh_attendance > backup.sql
```

### Restore Database

```bash
docker-compose exec -T db mysql -u root -p uwh_attendance < backup.sql
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change port mappings in docker-compose.yml if ports 80, 8000, or 3306 are already in use.

2. **Permission issues**: Ensure the application user has proper permissions:
   ```bash
   docker-compose exec web chown -R appuser:appuser /app
   ```

3. **Database connection issues**: Check that the database is ready:
   ```bash
   docker-compose logs db
   ```

4. **Static files not loading**: Collect static files:
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   ```

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs web
docker-compose logs db
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f web
```

## Security Considerations

1. Change all default passwords in `.env`
2. Use a strong `SECRET_KEY`
3. Set `DEBUG=False` in production
4. Configure proper `ALLOWED_HOSTS`
5. Use HTTPS in production (configure SSL in nginx)
6. Regularly update Docker images

## Monitoring

Health checks are configured for the web service. You can check the status:

```bash
# Check container health
docker ps

# Manual health check
curl http://localhost/health/
```

## File Structure

```
.
├── Dockerfile                 # Main application container
├── docker-compose.yml        # Production configuration
├── docker-compose.dev.yml    # Development configuration
├── nginx.conf                # Nginx configuration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .dockerignore             # Docker ignore file
└── DOCKER_README.md          # This file
```
