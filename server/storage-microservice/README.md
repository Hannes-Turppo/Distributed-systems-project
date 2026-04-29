## Guide to setting up storage:

1. Make sure you have a working PostgreSQL server running on your machine.
2. create "database.ini"-file in the same directory as storage.py and config.py.
3. database.ini contents should be as follows:

```ini
[postgresql]
host=[your host name, ex: localhost]
database=[name of the running DB you want to use]
user=[PostgreSQL username that has acces to the DB]
password=[your PostgreSQL user password]
port=[the port your DB is running on. PgSQL default is 5432]
```

Now when you run the microservice as storage.py, you should have a working connection to PostgreSQL 
