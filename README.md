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
- `NORTHEAST_HEADLESS` - Set to `true` if you want to run selenium in headless mode. Defaults to `false`.

4. Run the script with `poetry run python -m northeast.price_check your.email@example.com CONFIRMATION_CODE FIRST_NAME LAST_NAME --threshold -1`

\* threshold is the price difference to trigger an email alert for. For example, if the threshold is -1, an email will be sent if the price lowers at all. If the threshold is -10, an email will only be sent if the price decreases at least $10.
