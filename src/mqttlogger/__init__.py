import argparse, mqttlogger.logger

def main():
    parser = argparse.ArgumentParser(description="MQTT Logger")
    parser.add_argument('-b', '--broker')
    parser.add_argument('-c', '--clear', action='store_true')
    parser.add_argument('-t', '--topic', action='append', type=str)
    parser.add_argument('-p', '--port', type=int)
    parser.add_argument('database')
    args = parser.parse_args()
    print(args)

    log = logger.MQTTLogger(args)
    if args.port:
        server = logger.WebServer(args, log)
        server.start()
    log.loop_forever()

if __name__ == '__main__':
    main()
