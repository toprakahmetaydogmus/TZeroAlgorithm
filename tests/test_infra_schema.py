# -*- coding: utf-8 -*-
"""Unit tests for DevOps and Database Infrastructure AST Schema Compressor."""

import unittest
from tzero.tzero_infra import SchemaInfraReducer


class TestSchemaInfraReducer(unittest.TestCase):
    def test_sql_ddl_compression(self):
        sql_input = """
        -- Table documentation
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT check_u_len CHECK (char_length(username) >= 3)
        );

        -- Bulk inserts should be dropped completely
        INSERT INTO users (username, password_hash, email) VALUES ('alice', 'h1', 'alice@test.com');
        INSERT INTO users (username, password_hash, email) VALUES ('bob', 'h2', 'bob@test.com');
        INSERT INTO users (username, password_hash, email) VALUES ('charlie', 'h3', 'charlie@test.com');

        CREATE TABLE orders (
            order_id UUID PRIMARY KEY,
            user_id INT REFERENCES users(id),
            total_amount DECIMAL(10,2) NOT NULL
        );
        """
        reduced, savings = SchemaInfraReducer.reduce_sql(sql_input, mode="ultra")
        self.assertGreater(savings, 30.0)
        self.assertIn("CREATE TABLE users", reduced)
        self.assertIn("CREATE TABLE orders", reduced)
        self.assertNotIn("INSERT INTO users", reduced)
        self.assertIn("id SERIAL PRIMARY KEY", reduced)

    def test_k8s_yaml_compression(self):
        k8s_input = """
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: auth-service
          namespace: production
          managedFields:
            - manager: kubectl
              operation: Update
          annotations:
            deployment.kubernetes.io/revision: '12'
        spec:
          replicas: 5
          template:
            spec:
              containers:
                - name: auth-api
                  image: internal.reg/auth:v3.1.0
                  ports:
                    - containerPort: 8080
        status:
          availableReplicas: 5
          readyReplicas: 5
        """
        reduced, savings = SchemaInfraReducer.reduce_k8s_yaml(k8s_input, mode="ultra")
        self.assertGreater(savings, 40.0)
        self.assertIn("kind: Deployment", reduced)
        self.assertIn("name: auth-service", reduced)
        self.assertIn("image: internal.reg/auth:v3.1.0", reduced)
        self.assertNotIn("managedFields", reduced)
        self.assertNotIn("availableReplicas", reduced)

    def test_dockerfile_compression(self):
        docker_input = """
        FROM python:3.11-slim
        WORKDIR /app
        ARG BUILD_ENV=production
        ENV PYTHONUNBUFFERED=1

        # Long build command
        RUN apt-get update && apt-get install -y \\
            build-essential \\
            libpq-dev \\
            curl \\
            && rm -rf /var/lib/apt/lists/*

        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt
        COPY . .

        EXPOSE 8080
        ENTRYPOINT ["python", "app.py"]
        """
        reduced, savings = SchemaInfraReducer.reduce_dockerfile(docker_input)
        self.assertGreater(savings, 20.0)
        self.assertIn("FROM python:3.11-slim", reduced)
        self.assertIn("EXPOSE 8080", reduced)
        self.assertIn("ENTRYPOINT", reduced)

    def test_terraform_compression(self):
        tf_input = """
        terraform {
          required_version = ">= 1.5.0"
        }

        variable "environment" {
          type        = string
          default     = "production"
          description = "Deployment stage"
        }

        resource "aws_instance" "web_server" {
          ami           = "ami-0c55b159cbfafe1f0"
          instance_type = "t3.micro"
          monitoring    = true
          ebs_optimized = true

          tags = {
            Name = "ProductionWebServer"
            Owner = "DevOps"
          }
        }
        """
        reduced, savings = SchemaInfraReducer.reduce_terraform(tf_input)
        self.assertGreater(savings, 20.0)
        self.assertIn('resource "aws_instance" "web_server"', reduced)
        self.assertIn('variable "environment"', reduced)


if __name__ == "__main__":
    unittest.main()
