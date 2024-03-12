import mysql.connector
import json
from xmlrpc.server import SimpleXMLRPCServer

print("[INFO] Connecting to database...")

# Enter mysql credentials here...
mydb = mysql.connector.connect(
  host="localhost",
  user="networks",
  password="password",
  database="networking"
)

cursor = mydb.cursor()

print("[     --- ]connected")

print("[INFO] Creating tables...")
print("     creating table `messages`")
cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, ecg VARCHAR(100) NOT NULL, time INT NOT NULL, content JSON NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
print("     ---- OK")
print("     creating table `endpoints`")
cursor.execute("CREATE TABLE IF NOT EXISTS endpoints (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, type VARCHAR(255) NOT NULL, name VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
print("     ---- OK")
print("     creating table `endpoint_relations`")
cursor.execute("CREATE TABLE IF NOT EXISTS endpoint_relations (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, ecg_id VARCHAR(255) NOT NULL, doctor_id VARCHAR(255) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
print("     ---- OK")

print("[INFO] Ready to accept requests")

def process_request(type, request_data):
    print("[INFO] Request received")
    parsed_json = json.loads(request_data)
    if type == "WRITE_MSG":
        try:
            sql = "INSERT INTO messages (ecg, time, content) VALUES (%s, %s, %s)"
            json_encoded = json.dumps(request_data)  
            values = (parsed_json.get("id"), parsed_json.get("seconds"), request_data, )
            cursor.execute(sql, values)
            mydb.commit()
            print("[INFO] Request OK")
            return 200
        except mysql.connector.Error as err:
            print(f"[ERROR] {err}")    
            return 500
    if type == "RETRIEVE_DOCTOR_CACHE":
        print("[INFO] Retrieving doctor's cache for ecg id ", parsed_json.get("ecg"))
        sql = "SELECT content FROM messages WHERE ecg = %s ORDER BY time ASC;"
        values = (parsed_json.get("ecg"), )
        try:
            print("[INFO] Executing select query...")
            cursor.execute(sql, values)
            print("[INFO] Fetching results...")
            result = cursor.fetchall()

            print(result)

            print("[INFO] Results fetched")
        except mysql.connector.Error as err:
                print(f"[ERROR] {err}")    
                return 500
        print("[INFO] Request OK")
        return result
# Create the server instance
server = SimpleXMLRPCServer(("localhost", 8899))

# Register functions as RPC methods
server.register_introspection_functions()  # Optional: Allow introspection methods
server.register_function(process_request, "process_request")

# Start listening for requests
print("[INFO] Server listening on port 8899...")
server.serve_forever()