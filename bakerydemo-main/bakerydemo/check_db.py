from sshtunnel import SSHTunnelForwarder
import os, psycopg2

with SSHTunnelForwarder(
    ('ec2-3-106-117-102.ap-southeast-2.compute.amazonaws.com', 22),
    ssh_username='ec2-user',
    ssh_pkey='C:/Users/Admin/Downloads/ollamaawskey.pem',
    remote_bind_address=("database-1.c10mgacs26tc.ap-southeast-2.rds.amazonaws.com", 5432)
) as tunnel:
    conn = psycopg2.connect(
        dbname   = "postgres",
        user     = "postgres",
        password = "AaronB01652004549",
        host     = '127.0.0.1',
        port     = tunnel.local_bind_port,
        sslmode  = 'require'
    )
    print("✅ Connected!")
    conn.close()
