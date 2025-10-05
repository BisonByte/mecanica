from pyngrok import ngrok
import time

def main():
    # Open an HTTP tunnel to local port 8000
    tunnel = ngrok.connect(8000, "http")
    print("NGROK_TUNNEL:", tunnel.public_url)
    try:
        # keep the process alive while the tunnel is active
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        try:
            ngrok.disconnect(tunnel.public_url)
        except Exception:
            pass
        ngrok.kill()

if __name__ == "__main__":
    main()
