import serial
import serial.tools.list_ports
import threading
import time

Serial_Port=True
running=True
serial_lock=threading.Lock()

#チェックサムの計算
def CalculatingCS(check):
    cs=0
    for i in check:
        cs^=i
    cs_hex=format(cs,'02x')
    return cs_hex

#----------------------
#入力設定、結果要求
#----------------------
def serial_write1():
    global Serial_Port

    while running:
        if Serial_Port is not None:
            gps_command_header = bytes.fromhex('1075')
            gps_command_footer = bytes.fromhex('1003')
            gps_command_data = bytes.fromhex('0100000000')  # CC、予約2、OP00、OP01

            csm=CalculatingCS(gps_command_data)

            with serial_lock:
                data= b''.join([gps_command_header, gps_command_data, gps_command_footer,bytes.fromhex(csm)])
                Serial_Port.write(data)
                #print("send1",data)
#測地系設定
def serial_write2():
    global Serial_Port

    while running:
        if Serial_Port is not None:
            gps_command_header=bytes.fromhex('103F')
            gps_command_footer=bytes.fromhex('1003')
            gps_command_data=bytes.fromhex('2F09')

            csm = CalculatingCS(gps_command_data)

            with serial_lock:
                data=b''.join([gps_command_header,gps_command_data,gps_command_footer, bytes.fromhex(csm)])
                Serial_Port.write(data)
                #print("send2",data)

#----------------------
# データを受信,処理
#----------------------
def serial_read():
    global Serial_Port

    listdata=[]
    max_length=49
    lanmin=3
    lanmax=7
    lonmin=7
    lonmax=11


    while running:
        if Serial_Port is not None:
            if Serial_Port.in_waiting>0:
                with serial_lock:
                    data = Serial_Port.read(Serial_Port.in_waiting)
                for byte in data:
                    hex_str = '{:02x}'.format(byte)
                    listdata.append(hex_str)
                    if len(listdata)==max_length:
                        break
                if len(listdata)==max_length:
                    print(listdata)
                    #文字列のスライス
                    landata, londata = listdata[lanmin:lanmax], listdata[lonmin:lonmax]
                    #文字列の結合
                    joinlan, joinlon = ''.join(landata), ''.join(londata)
                    #16進数文字列から10進数整数型への変換
                    joinlan,joinlon=int(joinlan,16),int(joinlon,16)
                    #緯度経度計算
                    if isinstance(joinlan,int) and isinstance(joinlon,int):
                        joinlan, joinlon = joinlan / (256 * 3600), joinlon / (256 * 3600)
                        print(f"緯度 : {joinlan:.5f} 経度 : {joinlon:.5f}")
                    else:
                        print("中身ないよ")
                    listdata.clear()

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

#メイン処理
if __name__ == '__main__':
    #ポート開放
    serial_open()

    thread_1 = threading.Thread(target=serial_write1)
    thread_2=threading.Thread(target=serial_write2)
    thread_3 = threading.Thread(target=serial_read)

    thread_1.start()
    thread_2.start()
    thread_3.start()

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
        thread_3.join()

