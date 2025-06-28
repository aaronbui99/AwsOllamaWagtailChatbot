# Create IAM Role for kendra

IAM > Roles

Click on Create role

Add Custom Trust Policy

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "kendra.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}

Then Add Permissions policies:

![alt text](image-42.png)

![alt text](image-43.png)

![alt text](image-44.png)

Then add inline policy

![alt text](image-45.png)

![alt text](image-46.png)

![alt text](image-47.png)



# Amazon Kendra

https://ap-southeast-2.console.aws.amazon.com/kendra/home?region=ap-southeast-2#welcome

![alt text](image-49.png)

![alt text](image-48.png)

![alt text](image-40.png)

![alt text](image-41.png)

![alt text](image-39.png)