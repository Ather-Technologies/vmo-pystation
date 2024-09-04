from rtlsdr import RtlSdrTcpServer
rtl_server = RtlSdrTcpServer(hostname="0.0.0.0", port=12345)
rtl_server.run_forever()
rtl_server.close()