import socket
import threading as th
import random
'''
Request format:

HEAD: 
"
request_type request_id length_body
"
BODY IS SEPARATED BY \n FROM HEAD
"
item1:value1,item2:value2,item3:list_val1 listval2 listval3
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
host='127.0.0.1'
port=9090


def hanlde_req(conn, addr, orders)->None:
    '''
    Handles the request using separate thread
    '''
    print('connected:', addr)

    data_byte = conn.recv(1024)
    data = data_byte.decode()
    request = serializer(data)
    if not data:
        conn.close()
        return
    if(request['request_type'] == 'MENU'): #If request_type is menu
        response_id = random.randint(1000, 9999)
        header = f"{request['request_type']} {response_id} {request['request_id']} 200"
        body = menu_to_body() #parses menu.txt into appropriate body response string
        response = f"{header}\n{body}"
        conn.sendall(response.encode())
    if(request['request_type'] == 'ORDR'):
        response_id = random.randint(1000, 9999)
        header = f"{request['request_type']} {response_id} {request['request_id']}"
        is_correct_order = check_order(request['order']) #if the order items are in menu
        if is_correct_order:
            total_price = return_total_price(request['order'])
            orders[request['request_id']] = total_price
            body = f"total_price:{total_price}"
            header+= ' 200' #successfull status code of header
        else: #if order is not correct
            body = ''
            header+= ' 300' #unsuccesfull status code
        response = f"{header}\n{body}"
        conn.sendall(response.encode())
    if(request['request_type'] == 'PAYM'):
        response_id = random.randint(1000, 9999)
        header = f"{request['request_type']} {response_id} {request['request_id']}"
        if(int(request['money']) >= int(orders[request['request_id']])): #checks if the money from the client is enough to pay for the order
            header += ' 200'
            body = "optional:Thanks!"
        else:
            header += ' 300'
            body = "error:NotEnoughMoney"
        response = f"{header}\n{body}"
        conn.sendall(response.encode())
    conn.close()

def serializer(data)->dict:
    '''
    Parses the requests from client side and puts into dict
    '''
    dc = dict()
    header = data.split('\n')[0].split()
    body_str = data.split('\n')[1]
    body = []
    if(body_str != ''):
        body = body_str.split(',')
    dc['request_type'] = header[0]
    dc['request_id'] = header[1]
    dc['length_body'] = header[2]

    if(dc['request_type'] == 'ORDR'):
        order_dic = dict()
        for item in body_str.split(':')[1].split(): #parsing the items of order
            order_dic[item.split('#')[0]] = item.split('#')[1]
        dc['order'] = order_dic
    else:
        for item in body:
            key = item.split(':')[0]
            value = item.split(':')[1]
            dc[f'{key}'] = value
    return dc

def menu_to_body()->str:
    '''
    parses menu.txt into appropriate body response string
    '''
    body = "menu:"
    with open('/Users/imangali/Developer/projects/NU/cn/hw1/menu.txt') as f:
        lines = f.readlines()
    for line in lines:
        body+= f"{line.split()[0]}#{line.split()[1]} "
    return body

def check_order(order)->bool:
    '''
    Check if the items from the order actually present in the menu
    '''
    menu = _return_current_menu_dict()
    for item in order.keys():
        if item not in menu.keys():
            return False
    return True

def _return_current_menu_dict()->dict:
    '''
    Returns integer by parsing the menu: key - item name; value - item price
    '''
    with open('/Users/imangali/Developer/projects/NU/cn/hw1/menu.txt') as f:
        lines = f.readlines()
    menu = dict()
    for line in lines:
        menu[line.split()[0]] = line.split()[1]
    return menu

def return_total_price(order) -> int:
    '''
    Calculates the total price of the order according to the menu
    '''
    menu = _return_current_menu_dict()
    total = 0
    for item, amount in order.items():
        total += int(menu[item]) * int(amount)
    return total

sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.bind((host,port))

sock.listen(2)

orders = dict() # saves the information about the orders like key = request_id, value=total_price of the order
while True:
    conn, addr = sock.accept()
    t = th.Thread(target= hanlde_req(conn, addr, orders), args=()) #sends every request into separate threads for allowing mutiple clients
    t.start()