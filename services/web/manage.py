from flask.cli import FlaskGroup

import pandas as pd

from project import app, db, CurrencyDaily

cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command("seed_db")
def seed_db():
    with open('data/curr_and_gold.csv', 'r') as file:
        data_df = pd.read_csv(file)
    for index, row in data_df.iterrows():
        db.session.add(CurrencyDaily(name=row['currency'], code=row['code'], bid=row['bid'], ask=row['ask'], date=row['date']))
    db.session.commit()


if __name__ == "__main__":
    cli()
