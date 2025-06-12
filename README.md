# AwsOllamaWagtailChatbot

This is an Ollama LLM Chatbot on Wagtail-Django CMS that is stored data user input on AWS RDS . Note that the system is also using RAG and Amazon Aurora

## Installation
# Create Key pairs

Go to link: https://ap-southeast-2.console.aws.amazon.com/ec2/home?region=ap-southeast-2#KeyPairs:
or locate Key Pairs in Network & Security in side bar of the website

![alt text](image.png)

# Click on Create key pair

![image](https://github.com/user-attachments/assets/4c644752-1f20-40df-b1da-8affee3e0f04)

# Name your key pair, select format as pem file then click create

![image](https://github.com/user-attachments/assets/2f2c4d86-d74f-42aa-b44c-db2fdd6575cb)

# Create a new security group

Go to link: https://ap-southeast-2.console.aws.amazon.com/ec2/v2/home?region=ap-southeast-2#SecurityGroups:
or locate Security Groups in Network & Security in side bar of the website

![alt text](image-2.png)

# Click on create security group

![alt text](image-1.png)

# Create Inbound rule for port 11434 which is port for Ollama server

![alt text](image-4.png)

![alt text](image-5.png)

# Create Instance 

Go to link: https://ap-southeast-2.console.aws.amazon.com/ec2/home?region=ap-southeast-2#Instances:v=3;$case=tags:true%5C,client:false;$regex=tags:false%5C,client:false
or locate Instances in Instances in side bar of the website

![alt text](image-13.png)

# Click on launch instance

![alt text](image-6.png)

Name the instance and choose AMI to run the server.
For the demo, i will use Amazon Linux 2023

![alt text](image-7.png)

Choose the instance type. For this demo, I will use t3.medium

![alt text](image-8.png)

However, it's recommended using something way more powerful and has way more storage like g4dn.xlarge or c6i.large
Choosing the instance type really depends on which AI Model you want to use. For this demo, i am using deepseek-r1 and i am choosing t3.medium due to the cost. 

# Key Pair

Select the key pair created earlier

![alt text](image-10.png)

# Network settings

![alt text](image-9.png)

Check the checkbox for Allow HTTPS traffic from the internet and Allow HTTP traffic from the internet
Moreover, it's recommended to choose your own IP. For this demo, choosing Anywhere (0.0.0.0) or My Ip are both fine.

After all these steps, read the summary and click Launch

![alt text](image-8.png)

# Sucessfully launched

![alt text](image-11.png)
![alt text](image-12.png)


# Then Click Connect

![alt text](image-14.png)
![alt text](image-15.png)
![alt text](image-16.png)

Then follow these step

1. SSH into your EC2 instance

ssh -i /path/to/your-key.pem ec2-user@<EC2_PUBLIC_IP>

2. Install Ollama

curl -fsSL https://ollama.com/install.sh | sh
ollama --version   # verify it prints something like “ollama version 0.1.x”
3. Configure Ollama to listen on all interfaces
Edit /etc/systemd/system/ollama.service so the [Service] block looks like:

[Service]
ExecStart=/usr/local/bin/ollama serve
Environment="OLLAMA_HOST=0.0.0.0"
Restart=always
RestartSec=3
User=ollama
Group=ollama

4. Reload systemd & restart Ollama

sudo systemctl daemon-reload
sudo systemctl restart ollama
sudo systemctl status ollama   # should say “active (running)”

5. Confirm Ollama is listening on 0.0.0.0:11434

ss -tulnp | grep 11434
→ LISTEN  0 4096 0.0.0.0:11434

6. Pull your model (once Ollama is running. If you want other models, see the list here: https://ollama.com/search) 

ollama pull deepseek-r1:1.5b

7. Test the API locally on EC2

curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-r1:1.5b","prompt":"What is Ollama?","stream":false}'
8. Test from your laptop (replace with your real IP)

curl -X POST http://<EC2_PUBLIC_IP>:11434/api/generate \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"deepseek-r1:1.5b\",\"prompt\":\"What is Ollama?\",\"stream\":false}"
  
![alt text](image-17.png)

If you cannot find public IP, there are several ways to do it. 
One way is to go to EC2 console -> Select your instance -> Description tab -> Public IPv4 address

Then go to file chatbot/views.py and change the line 10 to your public ip
OLLAMA_API_URL = "http://<EC2_PUBLIC_IP>:11434/api/generate"

and in chatbot/views.py

payload = {
            "model": "deepseek-r1:1.5b",
            "prompt": user_prompt,
            "stream": False
        }

Change the AI Model to whatever you have downloaded. For example if you download llama2, change it to llama2

# Run Django Server

  python manage.py makemigrations
  
  python manage.py migrate
  
  python manage.py createsuperuser
  
  python manage.py runserver
  
Go to link: localhost:8000/chatbot/

# Create IAM Role

Find IAM and click on Create User

![image](https://github.com/user-attachments/assets/ff49415d-496e-41b3-aac1-447c0f6fa342)

Click on Next 

For Permission Policies, we will create the rds all permission and allow ec2 and rds pgacloud 

![image](https://github.com/user-attachments/assets/900943a5-b035-4697-bf2a-6ee65911fde3)

Click on attach policies directly and create policies with content as below:

For AllowEC2andRDSforpgacloud

Insert this in json 

{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": [
				"ec2:CreateSecurityGroup",
				"ec2:AuthorizeSecurityGroupIngress",
				"ec2:DeleteSecurityGroup",
				"ec2:DescribeSecurityGroups"
			],
			"Resource": "*"
		},
		{
			"Effect": "Allow",
			"Action": [
				"rds:CreateDBInstance",
				"rds:DescribeDBInstances",
				"rds:DescribeDBSubnetGroups",
				"rds:DescribeDBEngineVersions",
				"rds:CreateDBSubnetGroup",
				"rds:ModifyDBInstance",
				"rds:DeleteDBInstance"
			],
			"Resource": "*"
		}
	]
}

For rds-all-permissions insert json

{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "VisualEditor0",
			"Effect": "Allow",
			"Action": "rds:*",
			"Resource": "*"
		}
	]
}


# Create AWS RDS

Go to link: https://ap-southeast-2.console.aws.amazon.com/rds/home?region=ap-southeast-2#

Click on Databases -> Create database

![alt text](image-18.png)

For this demo, i will be using PostgreSQL database engine with engine version PostgreSQL 17.4-R1 and Templates Free Tier.

![alt text](image-19.png)

![alt text](image-20.png)

![alt text](image-21.png)

![alt text](image-22.png)

For Connectivity, connect with AWS EC2 that you created early on and running
![alt text](image-23.png)

For VPC security group, select the one you created earlier

![alt text](image-24.png)

For database authentication, i will use Password authentication. Feel free to use others.

![alt text](image-25.png)

For Monitoring, i will use 7 Days since it's free tier.

![alt text](image-26.png)

![alt text](image-27.png)

After clicking creating, wait until it's ready and this will be shown

![alt text](image-28.png)

Please noted that the AWS RDS is connected with AWS EC2 that previously we created. Which means you can check the connection using EC2 Bash (Click on Connect button in AWS EC2 for the instance we created earlier)

When EC2 bash is opened:

Insert this to install psql for ec2 bash ( For linux )

sudo dnf search postgresql

I choose version 15

sudo dnf install -y postgresql15
which psql
psql --version

Test connection to RDS instance in EC2 bash

psql --host=<your-rds-endpoint>.ap-southeast-2.rds.amazonaws.com --port=5432 --username=postgresql --dbname=database-1

If psql command does not work you can use these instead

sudo dnf install -y nmap-ncat 
nc -zv database-1.c10mgacs26tc.ap-southeast-2.rds.amazonaws.com 5432

OR using SSL handshake with OPENSSL
openssl s_client -connect database-1.c10mgacs26tc.ap-southeast-2.rds.amazonaws.com:5432

If it connects succesfully, congrats. If it fails, it's the security group setting in your rds-ec2 for port 5432

![image](https://github.com/user-attachments/assets/54fb3547-58a1-4770-b76e-b9989a17ade4)

![image](https://github.com/user-attachments/assets/c29a4707-81c3-4735-ad00-062cd2d67ee1)

![image](https://github.com/user-attachments/assets/83db9cfe-83b2-407d-b56f-941a7447ac12)

![image](https://github.com/user-attachments/assets/45cb5454-ceed-43f8-b8dc-362d1d6f6d3c)

![image](https://github.com/user-attachments/assets/a3cfb0a0-d5cd-4479-85d2-0c2dcccceaaf)

![image](https://github.com/user-attachments/assets/3cd45d24-fb6f-4f59-b87a-bd4153b42bb1)

![image](https://github.com/user-attachments/assets/828d0ae1-c376-4fee-a119-5eef92d632b9)


Remember file pem we created earlier on? Time to use it in your command prompt

Open your command prompt or powershell and insert 

ssh -i "C:\Users\Admin\Downloads\ollamaawskey.pem" `
  -L 5433:database-1.c10mgacs26tc.ap-southeast-2.rds.amazonaws.com:5432 `
  ec2-user@ec2-54-252-237-194.ap-southeast-2.compute.amazonaws.com

![image](https://github.com/user-attachments/assets/908ad42e-529f-4f80-bb33-ee57e2f36489)

you can insert aws command above at here to check as well.

Now for PGADMIN setup. you click on register -> Server

![image](https://github.com/user-attachments/assets/e456e731-bb32-4c9d-95a5-f09005d9093e)

![image](https://github.com/user-attachments/assets/058d8492-d2f0-414b-9619-9f5a518a053f)

![image](https://github.com/user-attachments/assets/db8ce50b-eae8-4516-866a-d9029ebc99d5)

![image](https://github.com/user-attachments/assets/40a5c2a8-5836-4a9f-886e-8f42c02852cc)

If it shows, then congrats.

![image](https://github.com/user-attachments/assets/c7aa1b9d-37ed-4ced-83f6-66066432c8a6)


# Deploying to Elastic Beanstalk
https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html
