from asyncio import subprocess
import resource
from unicodedata import name
from flask_restful import Resource, reqparse, marshal_with, fields
from ContainerServices.LocalCluster import LocalPod, MiniKube
import subprocess

input_data = reqparse.RequestParser()
input_data.add_argument("user_name", type=str, help="username is reuqired", required=True)
input_data.add_argument("resource_name", type=str)
input_data.add_argument("pw", type=str)

def get_response_format():
    mfields = {'message': fields.String, 'error' : fields.String,'payload' : fields.Raw}
    return mfields

mfields = get_response_format()


def is_exist(img_name):
    q = f'docker search --format "{{.Name}}" {img_name}'
    res = subprocess.run(q, shell=True, capture_output=True)

    return res.stdout.decode() != ""

class CustomResource(Resource):
    _running_pods = {}

    @marshal_with(mfields)
    def post(self):
        # create vm
        # resource name is same as repo name
        args = input_data.parse_args()
        user_name, resource_name = args['user_name'], args['resource_name']

        try:
            temp = resource_name.split("/")
            user_repo, img_tag = temp[0], temp[1]

            if ":" in img_tag:
                img_name = img_tag.split(":")[0]
            else:
                img_name = img_tag

            if not is_exist(img_name):
                print(img_name)
                return {"error" : "Image not found in Docker Hub"}

        except Exception as e:
            print(e)
            return {"error" : "Resource name in wrong format"}


        pod = LocalPod(MiniKube.get_instance(), name=f"{user_name}-{user_repo}-{img_name}", img_name=resource_name, port=8000, remote_access=False)
        ip, port = pod.get_internal_address()

        if ip == port and port == "":
            return {"error" : "Your resource image contains error"}

        return {"payload": {"ip" : ip, "port" : port}, "message" : f"Successfully created resource {resource_name}"}

    @marshal_with(mfields)
    def delete(self):
        args = input_data.parse_args()
        user_name, resource_name = args['user_name'], args['resource_name']

        resource_name = resource_name.replace("/", "-")

        query = f"kubectl delete pod {user_name}-{resource_name}"
        # print(query)
        subprocess.call(query, shell=True)
            
        return {"message" : f"Successfully terminate {user_name}'s {resource_name} example"}


class KaliContainer(Resource):
    # for user remote access
    _running_pods = {}

    @marshal_with(mfields)
    def post(self):
        args = input_data.parse_args()
        user_name, pw = args['user_name'], args['pw']
        print(user_name, pw)
        
        # create vm
        pod = LocalPod(MiniKube.get_instance(), user_name)
        pod.add_user(user_name, pw)
        pod.setup_ssh()

        MiniKube.get_instance().expose_service(service_name=user_name)

        ip, port = pod.get_address()
        print("After exposed, address is : ", ip, port)

        self._running_pods[user_name] = pod
        return {"payload": {"ip" : ip, "port" : port}, "message" : f"Successfully created resources for {user_name}"}

    @marshal_with(mfields)
    def delete(self):
        args = input_data.parse_args()
        user_name = args['user_name']

        if user_name in self._running_pods:
            self._running_pods[user_name].terminate()
            
        return {"message" : f"Successfully terminate {user_name}'s resources"}
