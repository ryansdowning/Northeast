# Northeast

Automating things that Southwest makes annoying.

## Features

Currently supports:

1. Sending email alerts if the price of a flight in your reservation changes by a certain amount.

Coming soon:

- Automatic check-in for flights.

## Usage

1. Install python 3.12 and install poetry.

2. Install the project dependencies with `poetry install`.

3. Add environment variables or a .env file that define the following:

- `NORTHEAST_SMTP_SERVER` - The host of your SMTP server. Defaults to `smtp.gmail.com`.
- `NORTHEAST_SMTP_PORT` - The port of your SMTP server. Defaults to `587`.
- `NORTHEAST_SMTP_USERNAME` - The email of your SMTP username, also used as the sender's email address.
- `NORTHEAST_SMTP_PASSWORD` - The password of the SMTP account associated with the username. If using gmail, you will need to obtain an [app password](https://support.google.com/accounts/answer/185833?hl=en).

4. Modify the values in `price_check.py` below where it says "Replace these!".

5. Run the script with `poetry run python -m northeast.price_check`
