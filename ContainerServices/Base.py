class Cluster:
    def __init__(self) -> None:
        self.start()
        pass
    def start(self):
        pass
    def expose_service(self, service_name):
        pass

    def stop_service(self, service_name):
        pass

class Pod:
    def __init__(self, cluster : Cluster, name, img_name, port, remote_access) -> None:
        self.name = name
        self.cluster = cluster
        self.ext_ip = None
        self.ext_port = None
        self.img_name = img_name
        self.port = port
        self.remote_access = remote_access

        self.start()
    def start(self):
        pass
    def add_user(self, username, pw):
        pass
    def get_address(self) -> tuple:
        pass

    def get_internal_address(self) -> tuple:
        pass
