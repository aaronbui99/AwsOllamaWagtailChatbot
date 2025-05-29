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

# Run Django Server

  python manage.py makemigrations
  
  python manage.py migrate
  
  python manage.py createsuperuser
  
  python manage.py runserver
  
Go to link: localhost:8000/chatbot/
