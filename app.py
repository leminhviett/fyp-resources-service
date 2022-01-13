from flask import Flask
from flask_restful import Api       
from ContainerServices.LocalCluster import MiniKube
from ContainerResources import Container

if __name__ == "__main__":
    mk = MiniKube()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "asdfavaead124435"

    api = Api(app)

    api.add_resource(Container, "/container")
    app.run(debug=True, port=8000)