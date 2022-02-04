from asyncio import subprocess
from unicodedata import name
from flask_restful import Resource, reqparse, marshal_with, fields
from ContainerServices.LocalCluster import LocalPod, MiniKube
import subprocess

input_data = reqparse.RequestParser()
input_data.add_argument("user_name", type=str, help="username is reuqired", required=True)
input_data.add_argument("pw", type=str)

def get_response_format():
    mfields = {'message': fields.String, 'error' : fields.String,'payload' : fields.Raw}
    return mfields

mfields = get_response_format()

class SQLInj(Resource):
    _running_pods = {}

    @marshal_with(mfields)
    def post(self):
        # create vm
        args = input_data.parse_args()
        user_name = args['user_name']
        pod = LocalPod(MiniKube.get_instance(), name=f"{user_name}-sql-inj-ex", img_name="viet009/sql-inj-ex", port=8000, remote_access=False)
        ip, port = pod.get_internal_address()
        return {"payload": {"ip" : ip, "port" : port}, "message" : "Successfully created resource for sql injection example}"}

    @marshal_with(mfields)
    def delete(self):
        args = input_data.parse_args()
        user_name = args['user_name']

        query = f"kubectl delete pod {user_name}-sql-inj-ex"
        subprocess.call(query, shell=True)
            
        return {"message" : f"Successfully terminate {user_name}'s sql injection example"}


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
