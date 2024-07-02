import serial
import time
import serial.tools.list_ports
import asyncio
import threading

bGPSinit=0
bGPSsokuidata=0
GPStimer=None
myComport=None
myComportname=None

status_gps = {
    "open": False,
    "iscomport": False,
    "lon": 0,
    "lat": 0
}



#COM3ポートに接続されたデバイスとの通信
ser=serial.Serial('COM3',9600,timeout=2)
while True:
    time.sleep(1)
    #バイナリ型出力
    #result=ser.read_all()
    #int型出力
    result=int.from_bytes(ser.read_all(),byteorder="big")
    result=str(result)
    bytelist=[result[i:i+2]for i in range(0,len(result),2)]
    #型確認
    #print(type(result))
    print(bytelist)



    #利用可能なシリアルポートのリスト取得
    async def getserialportlist():
        ports=serial.tools.list_ports.comports()
        portlist=[port.device for port in ports]
        return portlist

    async def main():
        ports = await getserialportlist()
        print(ports)

    asyncio.run(main())
    
    #初期化フラグとデータ受信フラグを0にリセット
    async def stopGPS():
        global bGPSinit,bGPSsokuidata,GPStimer
        if GPStimer:
            GPStimer.cancel()
            GPStimer = None

        if status_gps['open']:
            status_gps['open'] = False
            #updateStatus(status_gps)

        print("stop gps")

    # 状態を更新するための処理
    """async def updateStatus(status):
        pass"""

    receivebuf=[]
    #GPSデータの初期化処理
    def getGPSinitdata():
        global iscommandresponce,status_gps

        iscommandresponce=False
        status_gps.open = True
        status_gps.lon = 0
        status_gps.lat = 0
        #updateStatus(status_gps)
        sendGPScommand(configsetGPSID3F())

    #GPSデータ取得の開始（一定時間ごとに送信）
    def getgpsdata():
        gps_command_senddata = configsetGPSID75()
        global bGPSsokuidata
        bGPSsokuidata = 1
        sendGPScommand(gps_command_senddata)
        msec = 1.0  #間隔の設定
        gpstimer = threading.Timer(msec, sendGPScommand)  # タイマーの作成
        gpstimer.start()  # タイマーの開始

    #コマンド送信処理    
    def sendGPScommand(command):
        global receivebuf
        if iscommandresponce:
            return
        receivebuf=[]
        iscommandresponce=True
        try:
            myComport.write(command)
        except Exception as e:
            print(e)


    #測位結果要求コマンド
    def configsetGPSID75():
        gps_command_header = bytes.fromhex('1075')
        gps_command_footer = bytes.fromhex('1003')
        gps_command_data = bytes.fromhex('0100000000')  # CC、予約2、OP00、OP01

        cs = get_cs(gps_command_data)
        gps_command_cs = bytes.fromhex(cs)

        gps_command_senddata = b''.join([gps_command_header, gps_command_data, gps_command_cs, gps_command_footer])

        return gps_command_senddata
    
    #測地系設定コマンド
    def configsetGPSID3F():
        gps_command_header = bytes.fromhex('103F')#103Fという16進数文字列をバイト列に変換して代入
        gps_command_footer = bytes.fromhex('1003')#同様
        gps_command_data = bytes.fromhex('2F09')  # 世界測地系、UTC時刻オフセット

        cs = get_cs(gps_command_data)
        gps_command_cs = bytes.fromhex(cs)

        gps_command_senddata = b''.join([gps_command_header, gps_command_data, gps_command_cs, gps_command_footer])

        return gps_command_senddata
    
    #排他的論理和(XOR)の計算
    def get_cs(buf):
        cs = 0
        for byte in buf:
            cs ^= byte
        cs_hex = hex(cs)[2:].upper()
    # チェックサムが1桁の場合は先頭に0を追加
        if len(cs_hex) < 2:
            cs_hex = '0' + cs_hex
        return cs_hex

