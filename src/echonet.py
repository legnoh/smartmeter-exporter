# 第3章 電文構成(フレームフォーマット) 3.2 電文構成 を参照

smartmeter_eoj = b'\x02\x88\x01' #住宅設備関連機器(低圧スマート電力量メータクラス)
wisun_module_eoj = b'\x05\xFF\x01' #管理操作関連機器/コントローラ
epc_watt = b'\xE7' #EPC 瞬時電力計測値
epc_ampare = b'\xE8' #EPC 瞬時電流計測値

esv_req_codes = {
    "Get": b'\x62',
}

esv_res_codes = {
    "Get_Res": b'r', #b'\x72' (pythonの仕様上、bytes.fromhexすると文字変換されてしまう)
}

def parse_elite_response_data(data: str):
    parse_data = {
        "ehd1": bytes.fromhex(data[0:0+2]),
        "ehd2": bytes.fromhex(data[2:2+2]),
        "tid": bytes.fromhex(data[4:4+4]),
        "seoj": bytes.fromhex(data[8:8+6]),
        "deoj": bytes.fromhex(data[14:14+6]),
        "esv": bytes.fromhex(data[20:20+2]),
        "opc": bytes.fromhex(data[22:22+2]),
        "epc": bytes.fromhex(data[24:24+2]),
        "pdc": bytes.fromhex(data[26:26+2]),
        "edt": data[28:],
    }
    return parse_data

def make_elite_request_str(epc_type: str):

    if epc_type == 'watt':
        epc = epc_watt
    elif epc_type == 'ampare':
        epc = epc_ampare
    else:
        epc = ""

    data = {
        "ehd1": b'\x10',
        "ehd2": b'\x81',
        "tid": b'\x00\x01',
        "seoj": wisun_module_eoj,
        "deoj": smartmeter_eoj,
        "esv": esv_req_codes['Get'], #読み出し要求
        "opc": b'\x01',          #処理対象プロパティカウンタ数
        "epc": epc,
        "pdc": b'\x00',          #PDC
    }
    return b''.join(data.values())
