#! python 3 -- personal program to check for credits into current and credit card accounts for yesterday
import os
import json
import re
import plaid
import datetime
import sys
from email.message import EmailMessage
import smtplib

# available from https://plaid.com/docs/quickstart/
# set to your details
ACCESS_TOKEN_CREDIT_CARD = ''
ACCESS_TOKEN_CURRENT_ACCOUNT =  ''
PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')
PLAID_PUBLIC_KEY = os.getenv('PLAID_PUBLIC_KEY')
PLAID_ENV = 'development'
# email details for the alerts
SEND_TO_EMAIL =  ''
FROM_EMAIL =  ''
FROM_EMAIL_PWD = '' 
MAIL_SERVER = ''

def checkCreditCard():
    # try to generate query for transactions
    try:
        response = plaidClient.Transactions.get(ACCESS_TOKEN_CREDIT_CARD,start_date=yesterday, end_date=yesterday)
    except Exception as e:
        errorMessage = f'Could not get transaction object: {e}'
        sendEmail(errorMessage,-1,-1) # sends email in case of plaid error with error details
        sys.exit()
        
    # get transactions from response object
    transactions = response['transactions']

    # set total transactions
    total_transactions  = response['total_transactions']
   
    substring = 'DIRECT DEBIT'
    totalTrans = 0
    creditCardResults = ''

    for transaction in transactions:
        # only want negative values (money in) amd exclude direct debit payments of balance 
        if substring not in transaction['name'] and transaction['amount'] < 0:
            creditCardResults = creditCardResults + (f"\n{transaction['name']} \n {transaction['date']} \n {str(transaction['amount'])}\n")
            totalTrans = totalTrans + 1

    return totalTrans, total_transactions, creditCardResults

def checkCurrentAccount():

    # try to generate query for transactions
    try:
        response2 = plaidClient.Transactions.get(ACCESS_TOKEN_CURRENT_ACCOUNT,start_date=yesterday, end_date=yesterday)
    except Exception as e:
        errorMessage = f'Could not get transaction object: {e}'
        sendEmail(errorMessage,-1,-1)  # sends email in case of plaid error with error details
        sys.exit()
        
    # get transactions from response object
    transactions = response2['transactions']

    # show total transactions
    total_transactions  = response2['total_transactions']
    totalTrans = 0

    currentAccountResults = ''
    for transaction in transactions:
        # only want negative values (money in)
        if transaction['amount'] < 0:
            currentAccountResults = currentAccountResults + (f"\n{transaction['name']} \n {transaction['date']} \n {str(transaction['amount'])}\n")
            totalTrans = totalTrans + 1

    return totalTrans, total_transactions, currentAccountResults

def sendEmail(emailMessage, totalMatches, totalTransactions):
    # Create the email
    msg = EmailMessage()
    msg['Subject'] = f'NW TT: {totalTransactions} IN:{totalMatches}'
    msg['From'] = FROM_EMAIL
    msg['To'] = SEND_TO_EMAIL

   
    # Connect to SMTP Server
    smtpObj = smtplib.SMTP(MAIL_SERVER,587)
    print(type(smtpObj))
    smtpObj.ehlo()

    # Start encryption and provide login credentials
    smtpObj.starttls()
    smtpObj.login(FROM_EMAIL, FROM_EMAIL_PWD)
    
    # Set body of message
    msg.add_header('Conent-Type','text/plain')
    msg.set_payload(emailMessage.encode())
    
    # Send email
    print('About to send email')
    smtpObj.send_message(msg)
    print('Email sent')

    # Quit the SMTP 
    smtpObj.quit()


### main code
# create new plaid object
try:
    plaidClient = plaid.Client(client_id=PLAID_CLIENT_ID,
                    secret=PLAID_SECRET,
                    environment=PLAID_ENV,
                    api_version='2019-05-29')
except Exception as e:
    errorMessage = f'Could not create plaid client object: {e}'
    sendEmail(errorMessage,-1,-1)
    sys.exit()

# set the date for query i.e. yesterday
yesterday = (datetime.datetime.now() - datetime.timedelta(days= 1)).strftime('%Y-%m-%d')

# check credit card 
ccMatches, ccTotal, ccResults = checkCreditCard()

# check current account
caMatches, caTotal, caResults = currentAccountData=checkCurrentAccount()

# generate return data for email message
emailMessage = f'Current Account Results:\n{caResults}\nCredit Card Results:\n{ccResults}'
totalMatches = ccMatches + caMatches
totalTransactions  = ccTotal + caTotal

# email data
sendEmail(emailMessage, totalMatches, totalTransactions)

