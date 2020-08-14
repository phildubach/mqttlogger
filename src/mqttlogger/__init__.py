import argparse, mqttlogger.logger, os.path, json

def main():
    parser = argparse.ArgumentParser(description="MQTT Logger")
    parser.add_argument('-b', '--broker')
    parser.add_argument('-c', '--clear', action='store_true')
    parser.add_argument('-t', '--topic', action='append', type=str)
    parser.add_argument('-p', '--port', type=int)
    parser.add_argument('-U', '--user', help='MQTT username')
    parser.add_argument('-P', '--password', help='MQTT password')
    parser.add_argument('-C', '--client', help='MQTT client ID')
    parser.add_argument('-f', '--conf', default=".credentials")
    parser.add_argument('database')
    args = parser.parse_args()

    if os.path.exists(args.conf):
        try:
            print("Reading credentials from config file: ", args.conf)
            with open(args.conf) as creds:
                loaded = json.load(creds)
                print(loaded)
                for key in ('client', 'user', 'password'):
                    if key in loaded and not getattr(args, key):
                        setattr(args, key, loaded[key])
        except Exception as e:
            print("Unable to parse credentials file ", args.conf)
        
    print(args)

    log = logger.MQTTLogger(args)
    if args.port:
        server = logger.WebServer(args, log)
        server.start()
    log.loop_forever()

if __name__ == '__main__':
    main()
