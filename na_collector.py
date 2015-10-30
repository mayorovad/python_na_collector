import socket,struct,sys,time

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 2463)
sock.connect(server_address)

#Отправляем пакет, который указывает на то, что размер следующего будет 40 (\x28 = 40)
packed_data = b'\x80\x00\x00\x28'

sock.sendall(packed_data)

#для теста просто закидываю 40 байт из повторяющихся 4-ех -  x80\x00\x00\x28
packed_data = b'\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28'

sock.sendall(packed_data)

#Разобраться, как получать данные пакетами и проверять на конец передачи

'''
def recvall(sock):
    data = ""
    part = None
    while part != "":
        part = sock.recv(4096)
        data += part
    return data

data = recvall(sock)
print(data)
text = data.decode("utf-8")

'''	
data = sock.recv(4096)					
print(data)
data = sock.recv(4096)					
print(data)
data = sock.recv(4096)					
print(data)
#Чаще всего на тот пакет получаю ответ b'\x80\x00\xe4\xd0'
#Но иногда выплевывает что-то очень большое, содержащее в себе imno FactoryDefault 
# и теги SolTPGSALUA и SVC
print("\n")