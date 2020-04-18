import hmac
import json
import hashlib
import time
import requests
import ast

class PusherAPI(object):
    def __init__(self, app_id, key, secret, cluster):
        self.app_id = app_id
        self.key = key
        self.secret = secret
        self.cluster = cluster

    def load(self, events):
        # Decide type of event and endpoints needed
        if isinstance(events, list):
            self.__batch_events(events)
        elif isinstance(events,dict):
            self.__event(events)
        else:
            raise TypeError("Load() only accepts list or dictionary datatypes")

    def __event(self, event):
        self.__validate_event(event)
        # Convert Dictionary to JSONString
        event["data"] = str(event["data"])
        
        self.payload = json.dumps(event)
        self.http_method = "POST"
        self.endpoint = "/apps/"+ self.app_id + "/events"

    def __batch_events(self, batch):
        # Convert Dictionary to JSONString
        for event in batch:
            self.__validate_event(event)
            # Extra validation for batch events
            if "channels" in event:
                raise KeyError("channels is not supported in batch mode, please use channel instead.")
            event['data'] =  str(event['data'])

        self.payload = json.dumps({"batch":batch})
        self.http_method = "POST"
        self.endpoint = "/apps/"+ self.app_id + "/batch_events"

    def __validate_event(self, event):
        # Validate a single event
        if "name" not in event:
            raise KeyError("Name is missing from event dictionary")
        elif "data" not in event:
            raise KeyError("Data is missing from event dictionary")
        elif len(str(event['data'])) > 10240:
            raise ValueError("Data is too big, limited to 10KB")
        elif "channel" not in event and "channels" not in event:
            raise KeyError("Channel/s is missing from event dictionary")
        elif "channels" in event and len(event["channels"]) > 100:
            raise ValueError("Max channels allowed is 100.")
        elif "channels" in event and not isinstance(event["channels"], list):
            raise TypeError("Channels must be a list datatype")

    def get_channels(self):
        self.payload =  json.dumps({"info":["user_count"]})
        self.http_method = "GET"
        self.endpoint = "/apps/"+ self.app_id + "/channels"

    def get_channel(self, channel_name):
        self.payload =  json.dumps({"info":["user_count","subscription_count"]})
        self.http_method = "GET"
        self.endpoint = "/apps/"+ self.app_id + "/channels/"+channel_name

    def get_users(self, channel_name):
        self.payload =  json.dumps({})
        self.http_method = "GET"
        self.endpoint = "/apps/"+ self.app_id + "/channels/"+channel_name+"/users"

    def __authenticate_request(self):
        # Get the Relevant Authentication Details
        auth_timestamp = '%.0f' % time.time()
        auth_version = "1.0"
        body_md5 = hashlib.md5(self.payload.encode('utf-8')).hexdigest()
        auth_parameters = ("auth_key=" + self.key +
                           "&auth_timestamp=" + auth_timestamp +
                           "&auth_version="+ auth_version +
                           "&body_md5=" + body_md5)
        signature = (self.http_method+"\n" + self.endpoint +"\n"+auth_parameters)
        auth_signature = hmac.new(self.secret.encode('utf-8'), signature.encode('utf-8'), hashlib.sha256).hexdigest()
        return auth_parameters, auth_signature

    def execute(self):
        # Authenticate
        auth_parameters, auth_signature = self.__authenticate_request()
        request_url = ("https://api-" + self.cluster + ".pusher.com" + self.endpoint + "?" + auth_parameters + "&auth_signature=" + auth_signature)
        # Send Request
        if self.http_method == "GET":
            api_response = requests.get(request_url, data=self.payload, headers={"Content-Type": "application/json"})
        elif self.http_method == "POST":
            api_response = requests.post(request_url, data=self.payload, headers={"Content-Type": "application/json"})
        # Create a response dictionary 
        user_response = {"code":api_response.status_code}
        try:
            user_response["response"] = json.loads(api_response.content)
        except:
            user_response["response"] = api_response.content.decode("utf-8")
        return user_response