from flask import Flask
from flask_restful import Api       
from ContainerServices.LocalCluster import MiniKube
from ContainerResources import KaliContainer, SQLInj

if __name__ == "__main__":
    mk = MiniKube()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "asdfavaead124435"

    api = Api(app)

    api.add_resource(KaliContainer, "/kali_container")
    api.add_resource(SQLInj, "/sql_inj")

    app.run(debug=True, port=8000)