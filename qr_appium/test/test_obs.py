import obsws_python as obs


HOST = "127.0.0.1"
PORT = 4455

password = input("OBS WebSocket şifresi: ")

client = obs.ReqClient(
    host=HOST,
    port=PORT,
    password=password
)

print("======================================")
print("✅ OBS WebSocket bağlantısı başarılı!")
print("======================================")

version = client.get_version()

print("OBS sürümü:", version.obs_version)
print("WebSocket sürümü:", version.rpc_version)