# Docker Commands

## Containers
```
docker run -d <image>       # Run in detached mode
docker run -it <image>      # Run interactively
docker ps                   # List running containers
docker ps -a                # List all containers
docker stop <id>            # Stop container
docker rm <id>              # Remove container
docker logs <id>            # View logs
docker exec -it <id> bash   # Shell into container
```

## Images
```
docker images               # List images
docker build -t <name> .    # Build image from Dockerfile
docker pull <image>         # Pull from registry
docker push <image>         # Push to registry
docker rmi <image>          # Remove image
docker tag <src> <tag>      # Tag image
```

## Compose
```
docker compose up -d        # Start services
docker compose down         # Stop services
docker compose ps           # List services
docker compose logs         # View logs
docker compose build        # Rebuild images
docker compose restart      # Restart services
```

## Cleanup
```
docker system prune -a      # Remove all unused data
docker volume prune         # Remove unused volumes
docker network prune        # Remove unused networks
```
