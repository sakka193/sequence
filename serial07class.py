import serial
import serial.tools.list_ports
import threading
import time

class GPScontroller():
    def __init__(self,port="COM3",baudrate=9600):
        self.running = True
        self.serial_lock = threading.Lock()
        self.serial_port = None
        self.port = port
        self.baudrate = baudrate

    def main(self):
        self.serial_open()

        thread_1 = threading.Thread(target=self.serial_write1)
        thread_2=threading.Thread(target=self.serial_write2)
        thread_3 = threading.Thread(target=self.serial_read)

        thread_1.start()
        thread_2.start()
        thread_3.start()

        #Ctrl+Cで終了
        def stoprunning(self):
            self.running=False

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            stoprunning()
            thread_1.join()
            thread_2.join()
            thread_3.join()

    def serial_open(self):
        #portリストを取得
        serial_ports={}
        for i,port in enumerate(serial.tools.list_ports.comports()):
            serial_ports[str(i)]=port.device

        self.serial_port=serial.Serial(port=self.port, baudrate=self.baudrate, parity= "N")

    def serial_write1(self):

        while self.running:
            if self.serial_port is not None:
                gps_command_header=bytes.fromhex('103F')
                gps_command_footer=bytes.fromhex('1003')
                gps_command_data=bytes.fromhex('2F09')

                csm = self.CalculatingCS(gps_command_data)

                with self.serial_lock:
                    data=b''.join([gps_command_header,gps_command_data,gps_command_footer, bytes.fromhex(csm)])
                    self.serial_port.write(data)
                    #print("send2",data)


    #----------------------
    #入力設定、結果要求
    #----------------------
    def serial_write2(self):

        while self.running:
            if self.serial_port is not None:
                gps_command_header = bytes.fromhex('1075')
                gps_command_footer = bytes.fromhex('1003')
                gps_command_data = bytes.fromhex('0100000000')  # CC、予約2、OP00、OP01

                csm=self.CalculatingCS(gps_command_data)

                with self.serial_lock:
                    data= b''.join([gps_command_header, gps_command_data, gps_command_footer,bytes.fromhex(csm)])
                    self.serial_port.write(data)
                    #print("send1",data)
    def serial_read(self):

        listdata=[]
        max_length=49
        lanmin=3
        lanmax=7
        lonmin=7
        lonmax=11


        while self.running:
            if self.serial_port is not None and self.serial_port.in_waiting>0:
                with self.serial_lock:
                    data = self.serial_port.read(self.serial_port.in_waiting)

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
                        print("中身なし")
                    listdata.clear()

    #チェックサムの計算
    def CalculatingCS(self,check):
        cs=0
        for i in check:
            cs^=i
        cs_hex=format(cs,'02x')
        return cs_hex

#メイン処理
if __name__=="__main__":
    GPS_controller=GPScontroller()
    GPS_controller.main()