import os
import random

import psycopg2
from flask import Flask, request
from flask_restful import Api, Resource, reqparse

#!  Credentials set in environment variables
DATABASE_URL = os.environ["DATABASE_URL"]

app = Flask(__name__)
api = Api(app)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

@app.before_request
def check_request_auth():
    try:
        if request.headers['X-RapidAPI-Proxy-Secret'] != os.environ['X-RapidAPI-Proxy-Secret']:
            raise ValueError
    except:
        return {
            'message': 'Request from wrong provider.'
        }, 400

@app.after_request
def close_connection(response):
    conn.close()
    cur.close()
    return response

class Projects(Resource):
    def get(self, id=0):
        parser = reqparse.RequestParser()
        parser.add_argument('category_id', required=False)
        args = parser.parse_args()  # parse arguments to dictionary

        if args["category_id"]:
            cur.callproc('\"GetProjects\"', (args["category_id"]))
            data = cur.fetchall()
        else:
            cur.callproc('\"GetProjects\"', ())
            data = cur.fetchall()

        if id == 0:
            return {
                'data': random.choice(data)
            }, 200
        else:
            for value in data:
                if value['id'] == id:
                    return {
                        'data': value
                    }, 200  # return data and 200 OK code

            return {
                'message': f"Project with ID '{id}' not found."
            }, 404


class Submissions(Resource):
    def post(self):
        json_data = request.get_json(force=True)
        name = json_data['name']
        description = json_data['description']

        cur.callproc('\"InsertSubmission\"', (f"\'{name}\'", f"\'{description}\'"))
        id = cur.fetchone()
        conn.commit()

        # Get the line with the id just inserted to return to the user
        data = cur.callproc('\"GetSubmissions\"', (id))
        data = cur.fetchall()

        conn.close()
        cur.close()

        return {
            'message': 'Submission recieved. It will be reviewed manually. Thank you :)',
            'data': data,
        }, 201


class Categories(Resource):
    def get(self, id=0):
        cur.callproc('\"GetSubmissions\"', (id))
        data = cur.fetchall()

        conn.close()
        cur.close()

        if id == 0:
            return {
                'data': data
            }, 200  # return data and 200 OK code
        else:
            for value in data:
                if value['id'] == id:
                    return {
                        'data': value
                    }, 200  # return data and 200 OK code

            return {
                'message': f"Category with ID '{id}' not found."
            }, 404


api.add_resource(Projects, '/projects', '/projects/', '/projects/<int:id>')
api.add_resource(Submissions, '/projects/submission', '/projects/submission/')
api.add_resource(Categories, '/categories', '/categories/', '/categories/<int:id>')

if __name__ == '__main__':
    app.run()
