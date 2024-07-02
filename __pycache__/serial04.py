import serial                       #これは動くやつ
import serial.tools.list_ports
import threading
import time

Serial_Port=None
running=True

#----------------------
# データを送信
#----------------------
def serial_write():
    global Serial_Port,running

    while running:
        if Serial_Port is not None:
            gps_command_header = bytes.fromhex('1075')
            gps_command_footer = bytes.fromhex('1003')
            gps_command_data = bytes.fromhex('0100000000')  # CC、予約2、OP00、OP01
            data= b''.join([gps_command_header, gps_command_data, gps_command_footer])
            Serial_Port.write(data)
            print("send1",data)
            time.sleep(1)

#----------------------
# データを受信,処理
#----------------------
def serial_read():
    global Serial_Port

    listdata=[]


    while running:
        if Serial_Port is not None:
            if Serial_Port.in_waiting>0:
                data = Serial_Port.read(Serial_Port.in_waiting)
                hex_data = "".join("{:02x}".format(byte) for byte in data)
                #リストへの追加
                listdata.append(hex_data)

                #文字列のスライス
                londata, landata = listdata[3:7], listdata[7:11]

                #文字列の結合
                joinlon, joinlan = ''.join(londata), ''.join(landata)
                #--------------------------16進数文字列型

                #16進数文字列から10進数への変換
                if joinlon and joinlan:
                    joinlon,joinlan=int(joinlon,16),int(joinlan,16)

                    #緯度経度計算
                    if isinstance(joinlon,int) and isinstance(joinlan,int):
                        joinlon, joinlan = joinlon / (256 * 3600), joinlan / (256 * 3600)
                        print(f"緯度 : {joinlon:.5f} 経度 : {joinlan:.5f}")
                else:
                    pass
                    #print(type(joinlon))

#----------------------
# シリアルポートをOpen
#----------------------
def serial_open():
    global Serial_Port

    #portリストを取得
    serial_ports={}
    for i,port in enumerate(serial.tools.list_ports.comports()):
        serial_ports[str(i)]=port.device

    Serial_Port=serial.Serial(port="COM3", baudrate=9600, parity= "N")
    #print(f'open{Serial_Port.port:4s}/{Serial_Port.baudrate:4d}bps/parity:{Serial_Port.parity:4s}')


if __name__ == '__main__':

    Serial_Port=''

    #ポート開放
    serial_open()

    thread_1 = threading.Thread(target=serial_write)
    #timer1=threading.Timer(2.0,serial_write)
    thread_2= threading.Thread(target=serial_read)

    thread_1.start()
    thread_2.start()

    #Ctrl+Cで終了
    def stoprunning():
        global running
        running=False

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stoprunning()
        thread_1.join()
        thread_2.join()


def get_cs(buf):
    cs = 0
    for byte in buf:
        cs ^= byte

    cs_hex = format(cs, '02X')
    return cs_hex