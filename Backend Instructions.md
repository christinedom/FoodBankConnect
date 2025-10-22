
# How to Set Up the Backend (WIP)

---

## Database

### PostgreSQL
I used **Aurora RDS** to make a **PostgreSQL** database. I did not use **AWS Secrets Manager** to store login information, just a regular username and password.

### Public/Private
You can choose to make the database public or private based on how you think you will use it. I made it public because I was learning at the time and needed to connect to DataGrip to view the entries in the database. However, based on how it is set up now, making it private would also be a valid choice. Making it public still means you must connect with the correct username and password, however. But, setting it to be private means that you can only connect to it from within AWS.

### Inbound & Outbound Rules
Make sure to edit your inbound and outbound rules in the Security Group of your database to allow reads and writes on port 5432. You will need to allow your **Database Loader** inbound access of type **PostgreSQL** with the source being the Security Group of your **ECS**. You also need to allow outbound access to your **Lambda** so that it can read your database and make sure to choose its Security Group. Alternatively, you can allow all traffic for inbound and outbound, but that does make your database less secure since anyone with the correct username and password can view or modify your database.

---

## REST API
We used a Lambda which is hooked up to a HTTP gateway. The lambda also has some environment variables to allow it to connect to the database.

### Lambda
Stuff

### HTTP Gateway
You're going to want to make an **API Gateway** of type **HTTP API**. AWS also gives you the option of doing traditional **REST API**'s or using **WebSockets**, but **HTTP API** supports all the same features at a lower cost.

You can choose to use IPv4 or Dualstack (IPv4 & IPv6), but I don't think it matters. I went with Dualstack anyways. Make sure to add Lambda integration.

You will have to configure some routes. These will be your requests types like GET, POST, etc. You can model this off of your Postman example. The stage does not really matter.

Once you have created your **HTTP API**, you're going to want add integrations to each of your requests to your **Lambda**. You can have multiple **Lambda**'s if you wish (it might even simplify your code), but I just have all my requests feed into the same **Lambda**.

Within your **HTTP API**, you can also connect a custom domain
