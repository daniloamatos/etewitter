# Deploy Etewitter on AWS EC2

This setup runs the existing Django ASGI application in Docker on one Ubuntu EC2 instance. SQLite and uploaded images persist on the instance disk. Nginx handles HTTPS and proxies both HTTP and WebSocket traffic to Django.

## 1. Create the EC2 instance

In the AWS Console, open **EC2 → Launch instance** and choose Ubuntu Server 24.04 LTS. Select an instance type that the console marks as eligible for your account's Free Tier or credits. Free Tier eligibility and credit offers depend on when the AWS account was created; check the estimate before launching.

Create or select a key pair and save the `.pem` file securely. In the security group allow inbound:

- SSH (22) from **My IP** only
- HTTP (80) from anywhere
- HTTPS (443) from anywhere

Do not open port 8080; the app binds it to localhost. Allocate an Elastic IP only if you need a stable address and have checked its current cost. Point your Cloudflare DNS record to the instance's public IP. If using the Cloudflare proxy, keep the record proxied and use **Full (strict)** after HTTPS is installed on EC2.

## 2. Install Docker and Nginx

Connect with the SSH command shown by the EC2 console, then run:

```sh
sudo apt update
sudo apt install -y docker.io docker-compose-v2 nginx certbot python3-certbot-nginx git
sudo systemctl enable --now docker nginx
sudo usermod -aG docker "$USER"
```

Log out and reconnect so the Docker group change takes effect.

## 3. Configure the application

Clone the repository and enter the deployment directory:

```sh
git clone YOUR_REPOSITORY_URL etewitter
cd etewitter/deploy/aws
mkdir -p data/uploads
```

Copy the example to `.env` in this directory (do not commit the copy), then replace the values:

```sh
cp environment.example .env
```

The `.env` file should contain:

```dotenv
DJANGO_SECRET_KEY=REPLACE_WITH_A_LONG_RANDOM_SECRET
DJANGO_ALLOWED_HOSTS=YOUR_DOMAIN,YOUR_EC2_PUBLIC_DNS
```

Generate a secret with `openssl rand -base64 48`. Use the exact domain users open in their browsers. Add the `www` hostname too if it will be used. Keep the `.env` file private.

Build and start the service:

```sh
docker compose -f compose.aws.yaml up -d --build
docker compose -f compose.aws.yaml logs -f web
```

The container runs migrations during startup and listens on `127.0.0.1:8080`. Verify locally on the instance with `curl -I http://127.0.0.1:8080/login/`.

## 4. Configure Nginx and HTTPS

Create `/etc/nginx/sites-available/etewitter` and replace `YOUR_DOMAIN` in this configuration:

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80;
    server_name YOUR_DOMAIN;

    client_max_body_size 8m;

    location /uploads/ {
        alias /home/ubuntu/etewitter/deploy/aws/data/uploads/;
        try_files $uri =404;
    }

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 3600s;
    }
}
```

If the Ubuntu username or repository directory differs, update the absolute path in `alias`. Enable the site and get a certificate:

```sh
sudo ln -s /etc/nginx/sites-available/etewitter /etc/nginx/sites-enabled/etewitter
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d YOUR_DOMAIN
```

If you use `www`, add it to `server_name`, `DJANGO_ALLOWED_HOSTS`, and the Certbot command. Test sign-in, uploads, and the chat WebSocket after HTTPS is active.

## Updating

```sh
cd ~/etewitter
git pull
cd deploy/aws
docker compose -f compose.aws.yaml up -d --build
```

Back up `deploy/aws/data/` regularly. It contains the SQLite database and user uploads. A single instance with SQLite and an in-memory Channels layer is suitable for a small demo, but does not provide high availability or safe multi-instance scaling.

## Security and billing notes

The project runs on Django 5.2 LTS. Keep dependencies on their latest patch releases before deploying updates. Also configure AWS billing alerts; Free Tier credits and quotas are limited and can expire. EC2, disks, addresses, and network usage may incur charges outside the eligible limits.
