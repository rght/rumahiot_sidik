import boto3
from uuid import uuid4
from datetime import datetime
from rumahiot_sidik.apps.authentication.utils import password_hasher
from rumahiot_sidik.apps.authentication.jwt import token_generator
from boto3.dynamodb.conditions import Key, Attr
import uuid

# DynamoDB client
def dynamodb_client():
    client = boto3.resource('dynamodb', region_name='ap-southeast-1')
    return client

# get user account by email
# input parameter : email(string)
# return user [dict]
def get_user_account_by_email(email):
    client = dynamodb_client()
    table = client.Table('rumahiot_users')
    # get user account
    response = table.scan(
        FilterExpression=Key('email').eq(email),
    )
    # please take the first element , (its shouldn't be possible though , just in case)
    # returning [uuid(string), email(string), password(string), last_login (string) -> utc timestamp] or [] if theres not match
    return response['Items']

# email authentication
# input parameter : email(string) , password(string)
# returning : is_valid(boolean) , data(dict) , error_message(string)
def user_check_by_email(email,password):
    # get the user
    data = {}
    user = get_user_account_by_email(email)
    if len(user) != 1 :
        # If returned data isnt normal (more than 1 email) -> shouldn't happen though
        data['is_valid'] = False
        data['user'] = None
        data['error_message'] = "Invalid email or password"
        return data
    else:
        if user[0]['password'] != password_hasher(user[0]['salt'],password):
            # if the password wasn't correct
            data['is_valid'] = False
            data['user'] = None
            data['error_message'] = "Invalid email or password"
            return data
        else:
            data['is_valid'] = True
            data['user'] = user[0]
            data['error_message'] = None
            return data

# put session and user uuid binding into DynamoDB and return jwt
# input parameter : uuid(string) , session_key(string)
# returning : token(string)
def create_jwt_token(uuid,session_key):
    # TODO : Check if deleting is cheaper than writing, or is it the same
    token = token_generator(session_key)
    client = dynamodb_client()
    table = client.Table('rumahiot_sessions')
    # put the token & user uuid in dynamodb
    item = {
            'session_key' : session_key,
            'uuid' : uuid,
            'time_created' : str(datetime.now().timestamp())
        }
    response = table.put_item(
        Item=item
    )
    item = {
        'token': token.decode("utf-8"),
    }
    return item


# Create user and put the data in dynamodb
# input parameter : email(string) , password(string)
# returning : status(boolean)
def create_user_by_email(email,password):
    status = False
    # for password salt
    salt = uuid4().hex
    # for user uuid
    uuid = uuid4().hex
    # password
    hashed_password = password_hasher(salt,password)
    # check for account existance
    user = get_user_account_by_email(email)

    if len(user) != 0:
        status = False
    else:
        # dynamodb client
        client = dynamodb_client()
        table = client.Table('rumahiot_users')
        response = table.put_item(
            Item={
                'email' : email,
                'password' : hashed_password,
                'uuid' : uuid
            }
        )
        status = True
    return status


# # create new user using email address and passsword
# def create_user_by_email(email,password):
#     # salt will be used as table uuid
#     salt = uuid.uuid4().hex
#     hashed_password = password_hasher(salt,password)
#     # dynamodb client
#     client = dynamodb_client()
#     table = client.Table('rumahiot_user')
#     response = table.put_item(
#         Item = {
#         'uuid' : salt,
#         'email' : email,
#         'password' : hashed_password
#     }
#     )