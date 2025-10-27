# language.py
import os

NETRUM_FILE = ".netrum"

translations = {
    "en": {
        "welcome": "Welcome!",
        "wallet": "Check Wallet",
        "wallet_desc": "Check Wallet",
        "logs": "Logs Bot",
        "logs_desc": "Check Logs Bot",
        "timeout": "Set Timeout",
        "timeout_desc": "Set timeout in minutes",
        "claim": "Claim Now",
        "claim_desc": "Claim now",
        "lang": "Language",
        "lang_desc": "Set Language",
        "choose_lang": "Please select language:",
        "updated": "Language updated!",
        "start_desc": "Show main menu",
        "invalid_lang": "Invalid language code. Use en or vi.",
        "lang_in_use": "Language is already in use",
        "cancel": "Cancel",
        # --- Claim Command ---
        "claim_question": "Do you want to claim?",
        "claim_confirm": "Claim",
        "claim_cancel": "Cancel",
        "claim_cancelled": "Claim cancelled.",
        # --- Set_timout Command ---
        "invalid_number": "Invalid number, 5-1440.",
        "timeout_already_set": "Timeout is already set to {value} minutes.",
        "timeout_updated": "Timeout updated to {minutes} minutes",
        "current_timeout": "Current timeout: {timeout} min",
        "enter_new_timeout": "Please enter new timeout (5-1440):",
        "timeout_change_cancelled": "Timeout change cancelled.",
        "timeout_prompt_retry": "Please enter a new value or press ❌ Cancel.",
        # --- Monitor ---
        "mining_update": "Mining Update",
        "remain": "Remain",
        "load": "Load",
        "mined": "Mined",
        "speed": "Speed",
        "tasks": "Tasks",
        "status_monitor": "Status",
        # --- Daly ---
        "wallet_info": "Wallet Check",
        "time": "Time",
        'wallet_daily': 'Wallet',
        # --- Claim ---
        "claim_result": "Claim Result", 
        "address_claim": "Address",   
        "claimable": "Claimable",           
        "fee_claim": "Fee",                    
        "balance": "Balance",               
        "status_claim": "Status",            
        "transaction": "Transaction",        
        "output": "Output",                    
        "claim_exception": "Claim Exception",
        # --- Log ---
        "logs_logs": "Logs",               
        "no_logs": "No logs found",  
        "logs_exception": "Exception in Logs",
    },
    "vi": {
        "welcome": "Xin chào!",
        "wallet": "Kiểm tra Ví",
        "wallet_desc": "Kiểm tra Ví",
        "logs": "Nhật ký Bot",
        "logs_desc": "Xem nhật ký Bot",
        "timeout": "Cài Timeout",
        "timeout_desc": "Cài thời gian timeout (phút)",
        "claim": "Claim ngay",
        "claim_desc": "Claim reward ngay",
        "lang": "Ngôn ngữ",
        "lang_desc": "Đổi ngôn ngữ",
        "choose_lang": "Vui lòng chọn ngôn ngữ:",
        "updated": "Ngôn ngữ đã được cập nhật!",
        "start_desc": "Hiển thị menu chính",
        "invalid_lang": "Ký hiệu ngôn ngữ không hợp lệ. Sử dụng en hoặc vi.",
        "lang_in_use": "Ngôn ngữ đang được sử dụng",
        "cancel": "Huỷ",
        # --- Claim Command ---
        "claim_question": "Bạn có muốn claim không?",
        "claim_confirm": "Claim",
        "claim_cancel": "Huỷ",
        "claim_cancelled": "Hủy claim.",
        # --- Set_timout Command ---
        "invalid_number": "Số không hợp lệ, phải từ 5-1440.",
        "timeout_already_set": "Timeout đã được đặt là {value} phút.",
        "timeout_updated": "Timeout đã được cập nhật thành {minutes} phút",
        "current_timeout": "Timeout hiện tại: {timeout} phút",
        "enter_new_timeout": "Vui lòng nhập timeout mới (5-1440):",
        "timeout_change_cancelled": "Đã huỷ thay đổi timeout.",
        "timeout_prompt_retry": "Vui lòng nhập giá trị mới hoặc nhấn ❌ Huỷ.",
        # --- Monitor ---
        "mining_update": "Cập nhật trạng thái",
        "remain": "Còn lại",
        "load": "Tiến độ",
        "mined": "Đào được",
        "speed": "Tốc độ",
        "tasks": "Nhiệm vụ",
        "status_monitor": "Trạng thái",
        # --- Daly ---
        "wallet_info": "Kiểm tra Ví",
        "time": "Thời gian",
        'wallet_daily': 'Ví',
        # --- Claim ---
        "claim_result": "Kết quả Claim",
        "address_claim": "Địa chỉ",
        "claimable": "Có thể Claim",
        "fee_claim": "Phí",
        "balance": "Số dư",
        "status_claim": "Trạng thái",
        "transaction": "Giao dịch",
        "output": "Kết quả đầu ra",
        "claim_exception": "Lỗi Claim",
        # --- Log ---
        "logs_logs": "Nhật ký",
        "no_logs": "Không có log",
        "logs_exception": "Lỗi nhật ký",
    },
}

def get_lang() -> str:
    if not os.path.exists(NETRUM_FILE):
        return "en"
    with open(NETRUM_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("LANG="):
                return line.strip().split("=", 1)[1]
    return "en"

def set_lang_file(lang: str):
    lines = []
    if os.path.exists(NETRUM_FILE):
        with open(NETRUM_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

    found = False
    with open(NETRUM_FILE, "w", encoding="utf-8") as f:
        for line in lines:
            if line.startswith("LANG="):
                f.write(f"LANG={lang}\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"LANG={lang}\n")

def t(key: str) -> str:
    lang = get_lang()
    return translations.get(lang, translations["en"]).get(key, key)
