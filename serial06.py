import serial
import serial.tools.list_ports
import threading
import time

Serial_Port = None
running = True
serial_lock = threading.Lock()

# 各スレッドの実行間隔を管理するための時間変数
last_send_time_1 = 0
last_send_time_2 = 0

#測地系設定
def serial_write1():
    global Serial_Port

    gps_command_header = bytes.fromhex('103F')
    gps_command_footer = bytes.fromhex('1003')
    gps_command_data = bytes.fromhex('2F09')

    with serial_lock:
        data = b''.join([gps_command_header, gps_command_data, gps_command_footer])
        Serial_Port.write(data)
        print("send1", data)

#----------------------
# 入力設定、結果要求
#----------------------
def serial_write2():
    global Serial_Port, last_send_time_2

    while running:
        if Serial_Port is not None:
            current_time = time.time()
            if current_time - last_send_time_2 >= 1:  # 1秒ごとに送信
                gps_command_header = bytes.fromhex('1075')
                gps_command_footer = bytes.fromhex('1003')
                gps_command_data = bytes.fromhex('0100000000')  # CC、予約2、OP00、OP01

                with serial_lock:
                    data = b''.join([gps_command_header, gps_command_data, gps_command_footer])
                    Serial_Port.write(data)
                    print("send2", data)

                last_send_time_2 = current_time  # 最後の送信時刻を更新

        time.sleep(0.1)  # CPUを占有しないために短いスリープ

#----------------------
# データを受信,処理
#----------------------
def serial_read():
    global Serial_Port

    listdata = []
    lanmin = 3
    lanmax = 7
    lonmin = 7
    lonmax = 11

    while running:
        if Serial_Port is not None:
            if Serial_Port.in_waiting > 0:
                with serial_lock:
                    data = Serial_Port.read(Serial_Port.in_waiting)
                Serial_Port.flushInput()
                listdata.clear()
                hex_data = "".join("{:02x}".format(byte) for byte in data)
                # リストへの追加
                listdata.append(hex_data)

                # 文字列のスライス
                """landata, londata = listdata[lanmin:lanmax], listdata[lonmin:lonmax]

                # 文字列の結合
                joinlan, joinlon = ''.join(landata), ''.join(londata)

                # 16進数文字列から10進数への変換と緯度経度計算
                if joinlan and joinlon:
                    joinlan, joinlon = int(joinlan, 16), int(joinlon, 16)
                    if isinstance(joinlan, int) and isinstance(joinlon, int):
                        joinlan, joinlon = joinlan / (256 * 3600), joinlon / (256 * 3600)
                        print(f"緯度 : {joinlan:.5f} 経度 : {joinlon:.5f}")"""

                time.sleep(1)  # CPUを占有しないために短いスリープ

#----------------------
# シリアルポートをOpen
#----------------------
def serial_open():
    global Serial_Port

    # portリストを取得
    serial_ports = {}
    for i, port in enumerate(serial.tools.list_ports.comports()):
        serial_ports[str(i)] = port.device

    Serial_Port = serial.Serial(port="COM3", baudrate=9600, parity="N")
    # print(f'open{Serial_Port.port:4s}/{Serial_Port.baudrate:4d}bps/parity:{Serial_Port.parity:4s}')


def threading_make():
    global running

    # ポート開放
    serial_open()

    #測地系設定送信
    serial_write1()

    # スレッドを生成して開始
    thread_2 = threading.Thread(target=serial_write2)
    thread_3 = threading.Thread(target=serial_read)

    thread_2.start()
    thread_3.start()

    # Ctrl+Cで終了
    def stop_running():
        global running
        running = False

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_running()
        thread_2.join()
        thread_3.join()

if __name__=='__main__':
    threading_make()
