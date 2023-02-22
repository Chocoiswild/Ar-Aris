
# import
import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime

# Go
class MagtiFun:
    '''
        The class allows us to use Magtifun.ge
         to send messages without an Internet browser.
        
         Arguments when creating an object:
             1. Username for authentication
             2. User password for authentication
             3. Log file location - (optional) -
             Where to save the log.
             If not specified, a log.txt file is created in the existing folder.
    '''

    # all instances will have access to these links
    urls = {  
        'login'        :'http://www.magtifun.ge/',
        'login_proc'   :'http://www.magtifun.ge/index.php?page=11&lang=ge',
        'sms_page'     :'http://www.magtifun.ge/index.php?page=2&lang=ge',
        'message_send' :'http://www.magtifun.ge/scripts/sms_send.php'
    }


    def __init__(self, username, password, log_file = None):
        self.username = username
        self.password = password
        self.log_file = "log.txt" if log_file is None else log_file


    def update_login_log(self, status):
        '''
            Enter information about authorization in the log file
             in the format:
                 time, user number,
                 Authorization status (+/- --- successful/failed),
                 balance('N/A' if status is -)
        ''' 
        with open(self.log_file, "ba") as f:
            time = datetime.now().strftime("%d/%m/%Y %H:%M:%S") 

            text = (time + f"| User authorisation {self.username} "
                           f"|{'+' if status else '-'}|"
                           f" balance: {self.balance if status else 'N/A'}")

            f.write((text + "\r\n").encode("utf-8"))  


    def update_messages_log(self, number, message, server_resp):
        ''' 
            Writes information about the message to the log file
             in the format:
                 time of sending, number, response received from server,
                 Remaining balance (after sending), text of sent message
        ''' 
        with open(self.log_file, "ba") as f:
            time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            f.write(
                    (time +
                    "| number: " + number                         + 
                    " | status: " + server_resp.center(10)        + 
                    " | balance: " + str(self.balance)             +
                    " | sms: " + message                           +
                    "|\r\n").encode("utf-8"))


    def login(self):
        '''
            In case of successful authentication, we get True as a result,
             otherwise, False.
        '''
        headers = {'User-Agent': \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36', 
                   'Referer': 'http://www.magtifun.ge/index.php?page=2&lang=ge'
                }
        s = requests.Session() 
        self.session = s; 
        s.headers.update(headers)

        # user info
        info = {'user': self.username, 'password': self.password}

        self.soup = bs(s.get(self.urls['login']).text, 'html.parser')
        info['csrf_token'] = self.soup.select('input[name="csrf_token"]')[0]['value']
        # get login page
        answer = s.post(self.urls['login_proc'], data=info);
        answer.encoding = "utf-8"
        self.soup = bs(answer.text, "html.parser") 
        
        # logged in or not?
        if "თქვენს ანგარიშზეა" in answer.text:
            self.get_balance()
            self.update_login_log(True)
            return True

        self.update_login_log(False)
        return False
        

    def get_balance(self):
        ''' 
            Helps us get balance & renew token
        '''  
        s = self.session
        soup = bs(s.get(self.urls['sms_page']).text, "html.parser")
        div = soup.select('div.menu_list')[0]
        balance = int(div.find_all("span")[1].text)

        token = soup.find("input", {'name':'csrf_token'})['value']
        self.balance = balance
        self.token = token

        return balance


    def send_messages(self, numbers, messages):
        '''
             If all messages are sent successfully, we get the result True,
             otherwise, to False.
             Information for individual messages is stored in a log file.

             The function does not significantly check the arguments, therefore, before using it
             Make sure all parameters are set correctly

             Arguments:
                 1. numbers - 1 or several numbers where we send the message
                 2. messages - 1 or several messages according to numbers
                
             for example:
                 1 numbers in case of sending a message
                 Can be either "123456678" or ["123456678"]

                 messages as "Greetings from magtifun" and ["Greetings from magtifun"]
        '''

        # check login status
        if not hasattr(self, "token"): return False

        if not isinstance(numbers, list): numbers = [numbers]
        if not isinstance(messages, list): messages = [messages]

        s = self.session
        resps = [] # to check that server said * is ok

        for number, message in zip(numbers, messages):

            send_me = {"csrf_token": self.token, 
                       "recipients": number, 
                       "message_body": message}
            # save response text
            server_resp = s.post(self.urls['message_send'], data=send_me).text

            self.get_balance() # update balance & token

            self.update_messages_log(number, message, server_resp)
            resps.append(server_resp)

        # decide what to return
        for resp in resps:
            if resp.lower() != "success":
                return False
        return True
