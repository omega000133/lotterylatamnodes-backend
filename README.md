# Deployment Guide

## Initial Setup
### Install Dependencies
Ensure you have the following installed on your system:
- Python (3.10+)
- pip (Python package manager)
- Virtualenv

### Clone the repo and change directory
```bash
git clone https://github.com/clock-workorange/LotteryLatamNodesBack.git
cd LotteryLatamNodesBack
```

### Create a Virtual Environment and Install dependencies
1. Create a virtual environment:
```bash
  python3 -m venv .venv
```
2. Activate the virtual environment:
```bash
source .venv/bin/activate
```
3. Install other dependencies listed in requirements
```bash
pip install -r requirements/dev.txt
```

## Configuration
### Database Configuration
1. Create database
- Install postgresql on system
- Create Database on on postgresql
2. Change .env file configuration
```bash
nano .env
DB_USER=postgres
DB_HOST=localhost
DB_PASSWORD=localhost_pwd
```

## Database migration and Create super user
### Database migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### Create super user
```bash
python manage.py createsuperuser
```

## Running server
```bash
sh start.sh
sh celery_db.sh
sh celery_info.sh
```

## Configuration default delegator data
### Open django shell
```bash
python manage.py shell
```

### Running task manually
```python
from latam_nodes.delegator.tasks import save_delegators_task, create_ticket

save_delegators_task()
create_ticket()
```


# Testing Guide
## Login admin page
[Go to Admin page](https://app.latamnodes.org/admin/)
```bash
username: test
password: testpassword
```
That info is from ```python manage.py createsuperuser```

## Create Packpot
### [Go to Packpot page](https://app.latamnodes.org/admin/ticket/jackpot/add/)
### Create Packpot
- Winning percentage: Percentage number of Reward that delegators will get
- Ticket cost: Cost per ticket(Delegators will get `staking amount / ticket cost`'s ticket for free)
- Draw date: The date the Lottery ends(You have to set this value after now)
