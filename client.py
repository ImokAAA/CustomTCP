import socket
import random
import os

host='127.0.0.1'
port=9090

'''
Request format:

HEAD: 
"
request_type request_id
"
BODY IS SEPARATED BY \n FROM HEAD
"
item1:value1,item2:value2,item3:list_val1#amount listval2#amount listval3#amount
"
----------------------------
Response format:

HEAD: 
"
request_type response_id request_id response_code
"
BODY IS SEPARATED BY \n FROM HEAD
"
item1:value1,item2:value2,item3:list_val1#price1 listval2#price2 listval3#price3
"

'''

def send_request(request_type, body, payment_request_id = None) -> str:
    '''
    Sends request to the server according to its type, creates header string and adds it with body
    '''
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((host,port))
    request_id = random.randint(1000, 9999)
    if request_type == 'PAYM' and payment_request_id != None: # since the request_id in payment request must be equal to request id of order request
        request_id = payment_request_id
    header = f"{request_type} {request_id} {len(body)}"
    body = f"{body}"
    byt=f"{header}\n{body}".encode() #Used .encode() to send to the server request
    s.sendall(byt)
    data_byte = s.recv(1024)
    s.close()
    data = data_byte.decode()
    return data

def serializer(data)->dict:
    '''
    Serializes the answer of the server. Returns dictionary of fields and their values from the server`s answer.
    '''
    dc = dict()
    header = data.split('\n')[0].split()
    body_str = data.split('\n')[1]
    dc['request_type'] = header[0]
    dc['response_id'] = header[1]
    dc['request_id'] = header[2]
    dc['response_code'] = header[3]

    if(dc['request_type'] == 'MENU' and dc['response_code'] == '200'):
        menu_dic = dict()
        for item in body_str.split(':')[1].split():
            menu_dic[item.split('#')[0]] = item.split('#')[1]
        dc['menu'] = menu_dic
    else:
        for item in body_str.split(','):
            key = item.split(':')[0]
            value = item.split(':')[1]
            dc[f'{key}'] = value

    return dc

while(1):

    json_response_menu = send_request('MENU', '') #sending the request to the server to get menu
    response_menu = serializer(json_response_menu) #parsing the answer of the server into dict
    if(response_menu['request_type'] == "MENU"):
        items_list = dict() #Saves all the items and their amount that user chose from the menu
        while True:
            question = ''
            for i, (key, value) in enumerate(response_menu['menu'].items()): #showing the menu to the user
                question+=f'{i+1}) {key} {value}\n'
            item = input(question+"Please choose the item number from menu and Enter F to order: ")
            if(item != 'F'):
                amount = input(f"Enter amount of the {list(response_menu['menu'].keys())[int(item)-1]} : ")
                items_list[list(response_menu['menu'].keys())[int(item)-1]] = int(amount)
            else: #After user pressed F, the ORDR request must be sent to the server
                print(items_list)
                body = 'order:'
                for key, value in items_list.items(): #Adding items of menu to the body of ORDR request
                    body+=f'{key}#{value} '
                json_response_order = send_request('ORDR', body) #Sending ORDR request
                response_order = serializer(json_response_order)
                if(response_order['response_code'] == '300'): # If the menu does not contain items from the Order
                    print('Mistake in your order, please try again')
                    break
                elif(response_order['response_code'] == '200'):# If the menu contains items in order
                    while True: #Payment process of the order
                        money = input(f"Total price of your order is {response_order['total_price']}\nEnter the amount of money to be paid: ")
                        name = input("Enter your name: ")
                        address = input("Enter your address: ")
                        card = input("Enter your card number: ")
                        body = f"money:{money},name:{name},address:{address},card:{card}"
                        json_response_payment = send_request('PAYM', body, response_order['request_id']) #Sending PAYM request
                        response_payment = serializer(json_response_payment) #parsing PAYM request
                        if(response_payment['response_code'] == '300'): #if not enough money was paid
                            print('Not enough money. Try again the payment')
                        elif(response_payment['response_code'] == '200'):#if payment is successfull
                            print(f"Succesfull payment for your order {response_payment['request_id']}\n{response_payment['optional']}")
                            break
