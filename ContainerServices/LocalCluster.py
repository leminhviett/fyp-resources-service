from re import sub
import time, subprocess
from .Base import Cluster, Pod
import multiprocessing, collections, threading

class MiniKube(Cluster):
    started = False
    _exposed_services = None

    def __init__(self) -> None:
        if MiniKube._exposed_services is None:
            super().__init__()
            MiniKube._exposed_services = collections.defaultdict(None)
            return 
        raise Exception("Minikube is singleton")
    @classmethod
    def get_instance(cls):
        return cls

    @classmethod
    def start(cls):
        if cls.started:
            return 
        cls.started = True
        subprocess.call("minikube start", shell=True)

    @classmethod
    def expose_service(cls, service_name):
        try:
            subprocess.call(f"rm ./temp/{service_name}", shell=True)
        except Exception as e:
            print(f"old log file of {service_name} not exist")

        query = f"nohup minikube service {service_name} --url > ./temp/{service_name}"
        proc = subprocess.Popen(query, shell=True)
        cls._exposed_services[service_name] = proc

        time.sleep(3)

    @classmethod
    def stop_service(cls, service_name):
        cls._exposed_services[service_name].kill()
        del cls._exposed_services[service_name]
    
class LocalPod(Pod):
    def __init__(self, cluster, name, remote_access=True, img_name="viet009/kali-headless:0.02", port=22) -> None:
        self.pod_proc = None
        super().__init__(cluster, name, img_name, port, remote_access)


    def start(self):
        if self.remote_access:
            query = f"kubectl run {self.name} --image={self.img_name} -i --tty --port {self.port}"
        else:
            query = f"kubectl run {self.name} --image={self.img_name} --port {self.port}"
        self.pod_proc = subprocess.Popen(query, shell=True)
        
        if self.remote_access:
            #make sure pod is up & running
            time.sleep(2.5)
            create_service = f"kubectl expose pod {self.name} --type=LoadBalancer --name={self.name}"
            subprocess.call(create_service, shell=True)

    def setup_ssh(self):
        q1 = f"kubectl exec {self.name} -- systemctl enable ssh"
        q2 = f"kubectl exec {self.name} -- systemctl start ssh"

        subprocess.call(q1, shell=True)
        subprocess.call(q2, shell=True)
        print("ssh set up")


    def add_user(self, username, pw):
        q1 = f"kubectl exec {self.name} -- useradd -m {username}"
        q2 = f"kubectl exec {self.name} -- usermod -aG sudo {username}"
        q3 = f"kubectl exec {self.name} -- bash -c \"echo '{username}:{pw}'|chpasswd\""
        subprocess.call(q1, shell=True)
        subprocess.call(q2, shell=True)
        subprocess.call(q3, shell=True)


        print("user added")

        return username, pw
    
    def get_address(self) -> tuple:
        # external address
        if self.ext_ip and self.port:
            return self.ext_ip, self.port

        flag = 0
        # parse log file to get ip address
        while flag <= 5:
            try:
                with open(f"./temp/{self.name}", 'r') as f:
                    lines = f.readlines()
                    if len(lines) < 7:
                        print("Still waiting for MK logs ... Wait for 2 sec")
                        time.sleep(2)
                        flag += 1 
                        continue
                        
                    i = len(lines) - 1
                    
                    while i >= 0:
                        if lines[i].startswith("http://"):
                            x = lines[i]
                            self.ext_ip, self.port = x.split("\n")[0].split("//")[-1].split(":")
                            return (self.ext_ip, self.port)
                        i -= 1
            except Exception as e:
                print("Still waiting for MK exposing service ... Wait for 2 sec")
                flag += 1
                time.sleep(2)

        return None, None

    def get_internal_address(self):
        time.sleep(3)

        q1 = "kubectl get pod %s -o jsonpath='{.status.podIP}'"% (self.name)
        q2 = "kubectl get pod %s -o jsonpath='{.spec.containers[*].ports[*].containerPort}'"% (self.name)

        flag = 0
        while flag <= 10:
            res1 = subprocess.run(q1, shell=True, capture_output=True)
            res2 = subprocess.run(q2, shell=True, capture_output=True)
            int_ip, port = res1.stdout.decode(), res2.stdout.decode()

            if int_ip != "" and port != "":
                return int_ip, port

            time.sleep(1)
            flag += 1
        return "", ""


    def terminate(self):
        q1 = f"kubectl delete pod {self.name}"
        q2 = f"kubectl delete svc {self.name}"
        subprocess.call(q1, shell=True)
        subprocess.call(q2, shell=True)
        
        try:
            self.cluster.stop_service(self.name)
            self.pod_proc.terminate()
        except:
            print("process might not exist")
            

        try:
            subprocess.call(f"rm ./temp/{self.name}", shell=True)
        except:
            pass
