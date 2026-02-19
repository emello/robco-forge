#!/bin/bash
export DATABASE_URL="postgresql://forge:XQ%5D%3CzzL%28%3C%28W%5BA0udBn%21iH%250ED72PB%3ADt@production-forge-db.cl6cq84yuuew.us-east-1.rds.amazonaws.com:5432/forge"
source venv/bin/activate
alembic upgrade head
